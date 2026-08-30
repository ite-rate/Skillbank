// rm / list 子命令。(移植 cli.py _cmd_rm/_cmd_list)
package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/ite-rate/skillbank/internal/manifest"
	"github.com/ite-rate/skillbank/internal/parser"
	"github.com/ite-rate/skillbank/internal/sync"
	"gopkg.in/yaml.v3"
)

func (a *App) cmdRm(args []string) int {
	fs := newFlagSet("machine", "dry-run")
	machineFlag := fs.strP("machine", "")
	dryRun := fs.boolP("dry-run")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[rm] %s\n", msg)
		return 2
	}
	if len(fs.args) == 0 {
		fmt.Fprintln(os.Stderr, "[rm] 缺 <name>(canonical skill 名)")
		return 2
	}
	name := fs.args[0]

	_, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[rm] ✗ %v\n", err)
		return 1
	}
	machine, rc := a.resolveMachine("rm", machines, *machineFlag, true)
	if rc != 0 {
		return rc
	}
	m, err := manifest.Load(a.ManifestPath())
	if err != nil {
		fmt.Printf("[rm] ✗ %v\n", err)
		return 1
	}
	recs := m.Find(name, "", "")
	if len(recs) == 0 {
		fmt.Printf("[rm] skill %q 无 manifest 部署记录(未同步过或已删), 无动作\n", name)
		return 0
	}
	local, remote := 0, 0
	for _, r := range recs {
		if r.Machine == machine {
			local++
		} else {
			remote++
		}
	}
	fmt.Printf("[rm] %q: 本机(%s) %d 条, 其它机器 %d 条\n", name, machine, local, remote)

	if *dryRun {
		for _, act := range m.DeleteLocal(name, machine, "", true) {
			fmt.Printf("  [dry-run] %s\n", act)
		}
		fmt.Println("  (dry-run: 其它机器仍会标 pending_deletion, 那边下次 sync 时删)")
		return 0
	}

	for _, act := range m.DeleteLocal(name, machine, "", false) {
		fmt.Printf("  %s\n", act)
	}
	if n := m.MarkPendingDeletion(name, machine); n > 0 {
		fmt.Printf("  标记 pending_deletion x%d(其它机器下次 sync 时删)\n", n)
	}
	if err := m.Save(""); err != nil {
		fmt.Printf("[rm] ✗ manifest 保存失败: %v\n", err)
		return 1
	}
	fmt.Printf("  manifest 已更新: %s\n", a.ManifestPath())
	fmt.Printf("  canonical 保留在 %s(disable 语义=stash, git 可恢复)\n",
		filepath.Join(a.RepoRoot, "skills", name))
	return 0
}

var agentShort = map[string]string{
	"ClaudeCode": "CC", "ZCode": "ZC", "QwenWorkCN": "QW", "TeleAgent": "TA",
	"Hermes": "HE", "Codex": "CX", "kimi-code": "KI",
}

func (a *App) cmdList(args []string) int {
	fs := newFlagSet("agent", "level", "machine")
	agentFlag := fs.strP("agent", "")
	levelFlag := fs.strP("level", "")
	machineFlag := fs.strP("machine", "")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[list] %s\n", msg)
		return 2
	}

	agentsCfg, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[list] ✗ %v\n", err)
		return 1
	}
	machine, rc := a.resolveMachine("list", machines, *machineFlag, false)
	if rc != 0 {
		return rc
	}
	m, err := manifest.Load(a.ManifestPath())
	if err != nil {
		fmt.Printf("[list] ✗ %v\n", err)
		return 1
	}
	mcfg, err := machines.GetMachine(machine)
	if err != nil {
		fmt.Printf("[list] ✗ %v\n", err)
		return 1
	}
	var cols []string
	for _, ag := range agentsCfg.Names() {
		if mcfg.HasAgent(ag) {
			cols = append(cols, ag)
		}
	}

	// 行来源: canonical + manifest-only(孤儿)
	type row struct{ name, level, native string }
	var rows []row
	seen := map[string]bool{}
	for _, d := range sync.IterCanonicalSkills(a.RepoRoot) {
		name := filepath.Base(d)
		seen[name] = true
		level, native := "?", ""
		if raw, err := os.ReadFile(filepath.Join(d, "SKILL.md")); err == nil {
			if m := parser.FrontmatterRe.FindSubmatchIndex(raw); m != nil {
				var fm map[string]any
				if yaml.Unmarshal(raw[m[2]:m[3]], &fm) == nil {
					if v, _ := fm["level"].(string); v != "" {
						level = v
					}
					if v, _ := fm["native_agent"].(string); v != "" {
						native = v
					}
				}
			}
		} // 列表展示容错: 读不出保持 "?"
		rows = append(rows, row{name, level, native})
	}
	for _, s := range m.Skills() {
		if !seen[s] {
			rows = append(rows, row{s, "(孤儿)", ""})
		}
	}

	if *levelFlag != "" {
		var filtered []row
		for _, r := range rows {
			if r.level == *levelFlag {
				filtered = append(filtered, r)
			}
		}
		rows = filtered
	}
	if *agentFlag != "" {
		cols = []string{*agentFlag}
	}

	fmt.Printf("[list] machine=%s(c=cp l=ln p=pending ·=未部署 ~=deferred)\n", machine)
	header := fmt.Sprintf("%-28s %-14s %-12s ", "skill", "level", "native")
	cell := ""
	for i, c := range cols {
		if i > 0 {
			cell += " "
		}
		short, ok := agentShort[c]
		if !ok && len(c) >= 2 {
			short = strings.ToUpper(c[:2])
		}
		cell += fmt.Sprintf("%2s", short)
	}
	fmt.Printf("  %s%s\n", header, cell)
	sort.Slice(rows, func(i, j int) bool { return rows[i].name < rows[j].name })
	for _, r := range rows {
		cells := ""
		for i, c := range cols {
			if i > 0 {
				cells += " "
			}
			recs := m.Find(r.name, machine, c)
			switch {
			case len(recs) == 0:
				cells += " ·"
			case recs[0].PendingDeletion:
				cells += " p"
			case recs[0].Method == "ln":
				cells += " l"
			default:
				cells += " c"
			}
		}
		fmt.Printf("  %-28s %-14s %-12s %s\n", r.name, r.level, r.native, cells)
	}
	return 0
}