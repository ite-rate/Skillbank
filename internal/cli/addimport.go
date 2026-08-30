// add / import 子命令 — 反向导入。(移植 cli.py _cmd_add/_cmd_import)
package cli

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/ite-rate/skillbank/internal/importer"
	"github.com/ite-rate/skillbank/internal/parser"
	"gopkg.in/yaml.v3"
)

var levelValues = []string{"auto", "manual", "experimental", "disable"}

func validLevel(s string) bool {
	for _, l := range levelValues {
		if s == l {
			return true
		}
	}
	return false
}

// isGitURL — http(s):// / git@ / ssh:// 开头视为 git URL。
func isGitURL(src string) bool {
	for _, p := range []string{"http://", "https://", "git@", "ssh://"} {
		if strings.HasPrefix(src, p) {
			return true
		}
	}
	return false
}

// errUserSkip — 用户在交互改名时选了跳过(Python 的 ValueError("user 跳过此次 import"))。
var errUserSkip = errors.New("user 跳过此次 import")

func (a *App) cmdAdd(args []string) int {
	fs := newFlagSet("level", "force", "machine", "yes")
	level := fs.strP("level", "manual")
	force := fs.boolP("force")
	machineFlag := fs.strP("machine", "")
	yes := fs.boolP("yes")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[add] %s\n", msg)
		return 2
	}
	if len(fs.args) == 0 {
		fmt.Fprintln(os.Stderr, "[add] 缺 <source>(本地路径 / git URL)")
		return 2
	}
	if !validLevel(*level) {
		fmt.Fprintf(os.Stderr, "[add] --level 必须是 %s 之一\n", strings.Join(levelValues, "/"))
		return 2
	}
	src := fs.args[0]

	// 交互重名: tty 且非 --yes 时问用户; 否则自动用建议名
	opts := importer.Options{Level: *level, Force: *force}
	if a.TTY && !*yes {
		opts.DisableAutoRename = true
		opts.RenameCallback = func(orig, suggested, native string) (string, error) {
			name, skip := a.renameCallback(orig, suggested, native)
			if skip {
				return "", errUserSkip
			}
			return name, nil
		}
	}

	if isGitURL(src) {
		results, err := importer.ImportGitURL(src, a.RepoRoot, opts)
		if err != nil {
			if errors.Is(err, errUserSkip) {
				fmt.Printf("[add] 跳过: %v\n", err)
				return 0
			}
			fmt.Printf("[add] ✗: %v\n", err)
			return 1
		}
		for _, r := range results {
			fmt.Printf("[add] 导入 → %s\n", r.CanonicalDir)
			for _, w := range r.Warnings {
				fmt.Printf("  ⚠ %s\n", w)
			}
		}
		fmt.Println("[add] 下一步: skillbank sync 同步到各 Agent")
		return 0
	}

	_, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[add] ✗ %v\n", err)
		return 1
	}
	machine, rc := a.resolveMachine("add", machines, *machineFlag, false)
	if rc != 0 {
		return rc
	}
	opts.Machines = machines
	opts.Machine = machine
	res, err := importer.ImportSkill(expandHome(src), a.RepoRoot, opts)
	if err != nil {
		if errors.Is(err, errUserSkip) || strings.Contains(err.Error(), "跳过") {
			fmt.Printf("[add] 跳过: %v\n", err)
			return 0
		}
		fmt.Printf("[add] ✗: %v\n", err)
		return 1
	}
	fmt.Printf("[add] 导入 → %s\n", res.CanonicalDir)
	for _, w := range res.Warnings {
		fmt.Printf("  ⚠ %s\n", w)
	}
	fmt.Println("[add] 下一步: skillbank sync 同步到各 Agent")
	return 0
}

func expandHome(p string) string {
	if p == "~" || strings.HasPrefix(p, "~/") {
		home, err := os.UserHomeDir()
		if err == nil {
			return filepath.Join(home, strings.TrimPrefix(p, "~"))
		}
	}
	return p
}

func (a *App) cmdImport(args []string) int {
	fs := newFlagSet("level", "agent", "force", "machine", "yes")
	level := fs.strP("level", "manual")
	agentFlag := fs.strP("agent", "")
	force := fs.boolP("force")
	machineFlag := fs.strP("machine", "")
	yes := fs.boolP("yes")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[import] %s\n", msg)
		return 2
	}
	if len(fs.args) == 0 {
		fmt.Fprintln(os.Stderr, "[import] 缺 <path>(agent 的 skill 目录, 须含 SKILL.md)")
		return 2
	}
	if !validLevel(*level) {
		fmt.Fprintf(os.Stderr, "[import] --level 必须是 %s 之一\n", strings.Join(levelValues, "/"))
		return 2
	}

	agentsCfg, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[import] ✗ %v\n", err)
		return 1
	}
	agent := *agentFlag
	if agent != "" && agentsCfg.Get(agent) == nil {
		fmt.Printf("[import] 未知 agent %q(agents.toml: %v)\n", agent, agentsCfg.Names())
		return 2
	}
	machine, rc := a.resolveMachine("import", machines, *machineFlag, false)
	if rc != 0 {
		return rc
	}
	opts := importer.Options{
		Level: *level, Agent: agent, Machines: machines, Machine: machine,
		Force: *force,
	}
	if !*yes && a.TTY {
		opts.DisableAutoRename = true
		opts.RenameCallback = func(orig, suggested, native string) (string, error) {
			name, skip := a.renameCallback(orig, suggested, native)
			if skip {
				return "", errUserSkip
			}
			return name, nil
		}
	}
	res, err := importer.ImportSkill(expandHome(fs.args[0]), a.RepoRoot, opts)
	if err != nil {
		msg := err.Error()
		if errors.Is(err, errUserSkip) || strings.Contains(msg, "改名后仍冲突") {
			fmt.Printf("[import] 跳过: %v\n", err)
			return 0
		}
		fmt.Printf("[import] ✗ %v\n", err)
		return 1
	}
	fmt.Printf("[import] → %s\n", res.CanonicalDir)
	for _, w := range res.Warnings {
		fmt.Printf("  ⚠ %s\n", w)
	}

	// 检测源是否含市场标志(install_source/skill_id) → 提示标 experimental
	srcPath := expandHome(fs.args[0])
	if raw, err := os.ReadFile(filepath.Join(srcPath, "SKILL.md")); err == nil {
		if m := parser.FrontmatterRe.FindSubmatchIndex(raw); m != nil {
			var srcFM map[string]any
			if yaml.Unmarshal(raw[m[2]:m[3]], &srcFM) == nil {
				hasMarket := srcFM["install_source"] != nil || srcFM["skill_id"] != nil
				if hasMarket && *level != "experimental" {
					fmt.Printf("  💡 来源带市场标志(install_source/skill_id), 建议 `skillbank set-level %s experimental`(未实测效 / 他者发表)\n",
						filepath.Base(res.CanonicalDir))
				}
			}
		}
	}
	fmt.Println("[import] 下一步: skillbank sync 同步到各 Agent")
	return 0
}