// sync 子命令 — collect→show→confirm→execute;无 -s/-a 且 tty 时交互选。
package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/ite-rate/skillbank/internal/manifest"
	"github.com/ite-rate/skillbank/internal/sync"
)

func (a *App) cmdSync(args []string) int {
	fs := newFlagSet("s", "skill", "a", "agent", "to", "dry-run", "yes", "force")
	skillsFilter := fs.sliceP("skill")
	agentsFilter := fs.sliceP("agent")
	fs.strSlice["s"] = skillsFilter // -s 别名(同槽指针; 不绑会 panic)
	fs.strSlice["a"] = agentsFilter // -a 别名
	machineFlag := fs.strP("to", "")
	dryRun := fs.boolP("dry-run")
	yes := fs.boolP("yes")
	force := fs.boolP("force")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[sync] %s\n", msg)
		return 2
	}

	agentsCfg, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[sync] ✗ %v\n", err)
		return 1
	}
	machine, rc := a.resolveMachine("sync", machines, *machineFlag, true)
	if rc != 0 {
		return rc
	}
	m, err := manifest.Load(a.ManifestPath())
	if err != nil {
		fmt.Printf("[sync] ✗ %v\n", err)
		return 1
	}

	skills, agents := *skillsFilter, *agentsFilter

	// 交互:无 -s/-a 且 tty 且非 --yes → 选 skill × agent
	if len(skills) == 0 && len(agents) == 0 && a.TTY && !*yes {
		skillDirs := sync.IterCanonicalSkills(a.RepoRoot)
		if len(skillDirs) == 0 {
			fmt.Println("[sync] skills/ 为空 — 先 skillbank import <某 agent 的 skill 目录>")
			return 0
		}
		opts := make([]string, len(skillDirs))
		for i, d := range skillDirs {
			state := "无SKILL.md"
			if _, err := os.Stat(d + "/SKILL.md"); err == nil {
				state = "ok"
			}
			opts[i] = fmt.Sprintf("%s (%s)", filepath.Base(d), state)
		}
		idx := a.selectMany("选要同步的 skill:", opts, true)
		for _, i := range idx {
			skills = append(skills, filepath.Base(skillDirs[i]))
		}

		mcfg, err := machines.GetMachine(machine)
		if err != nil {
			fmt.Printf("[sync] ✗ %v\n", err)
			return 1
		}
		idx = a.selectMany(fmt.Sprintf("选要同步到 %s 的 Agent:", machine), mcfg.AgentOrder, true)
		for _, i := range idx {
			agents = append(agents, mcfg.AgentOrder[i])
		}
	}

	ctx, err := sync.Collect(a.RepoRoot, machine, skills, agents, machines, agentsCfg, m, *force)
	if err != nil {
		fmt.Printf("[sync] ✗ %v\n", err)
		return 1
	}
	srcNote := "(显式指定)"
	if *machineFlag == "" {
		srcNote = "(本机绑定)"
	}
	fmt.Printf("[sync] machine=%s%s 计划:\n", machine, srcNote)
	sync.ShowPlan(ctx)
	if *dryRun {
		fmt.Println("[sync] dry-run 结束, 未写任何文件")
		return 0
	}
	if !*yes && a.TTY {
		if !a.confirm("执行以上计划?", false) {
			fmt.Println("[sync] 已取消")
			return 0
		}
	}
	failures := sync.Execute(a.RepoRoot, machine, ctx, machines, agentsCfg, m)
	if failures > 0 {
		fmt.Printf("[sync] 完成(%d 个失败)\n", failures)
		return 1
	}
	fmt.Println("[sync] 完成 ✓")
	return 0
}

func base(path string) string {
	i := len(path) - 1
	for i >= 0 && path[i] != '/' && path[i] != os.PathSeparator {
		i--
	}
	return path[i+1:]
}