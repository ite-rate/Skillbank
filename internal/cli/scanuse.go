// use / scan 子命令。(移植 cli.py _cmd_use/_cmd_scan)
package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/ite-rate/skillbank/internal/config"
	"github.com/ite-rate/skillbank/internal/identity"
	"github.com/ite-rate/skillbank/internal/scan"
)

// cmdUse — 绑定/查看本机身份(machines.toml 里的机器别名)。
//
// 绑定后, 所有命令的 --machine 默认取绑定值;未绑定时依赖默认值的命令
// 会拒绝执行(防在别的机器上按 mac-main 名义误动本机文件)。
func (a *App) cmdUse(args []string) int {
	_, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[use] ✗ %v\n", err)
		return 1
	}
	explicit := ""
	if len(args) > 0 {
		explicit = args[0]
	}
	if explicit == "" {
		bound := identity.ReadBinding(a.RepoRoot)
		if bound == "" {
			var names []string
			for name := range machines.Machines {
				names = append(names, name)
			}
			sort.Strings(names)
			fmt.Printf("[use] 本机未绑定。绑定: skillbank use <别名>(machines.toml 可用: %v)\n", names)
			return 2
		}
		fmt.Printf("[use] 当前绑定: %s\n", bound)
		return 0
	}
	machine, err := identity.ResolveMachine(a.RepoRoot, machines, explicit)
	if err != nil {
		fmt.Printf("[use] ✗ %v\n", err)
		return 2
	}
	p, err := identity.WriteBinding(a.RepoRoot, machine)
	if err != nil {
		fmt.Printf("[use] ✗ %v\n", err)
		return 2
	}
	fmt.Printf("[use] 本机身份绑定 → %s\n", machine)
	fmt.Printf("  %s(gitignored;下次 git pull 不受影响, 重 clone 需重新绑定)\n", p)
	return 0
}

// cmdScan — 探测本机 Agent skills 目录, 确认写入 machines.toml + 绑定本机身份。
//
// scan 与其它命令语义不同:显式 --machine 是注册新别名的入口, 不校验已存在;
// 无 flag 时用已绑定身份, 未绑定则报错给指引(首次使用必须指明本机别名)。
func (a *App) cmdScan(args []string) int {
	fs := newFlagSet("machine", "yes", "dry-run")
	machineFlag := fs.strP("machine", "")
	yes := fs.boolP("yes")
	dryRun := fs.boolP("dry-run")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[scan] %s\n", msg)
		return 2
	}

	agentsCfg, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[scan] ✗ %v\n", err)
		return 1
	}
	machine := *machineFlag
	if machine == "" {
		machine = identity.ReadBinding(a.RepoRoot)
	}
	if machine == "" {
		fmt.Println("[scan] 本机身份未绑定且未指定 --machine — " +
			"首次在本机使用请: `skillbank scan --machine <别名>`(顺带注册进 machines.toml)")
		return 2
	}
	// 显式别名时先注册进 machines.toml 的内存表(不存在的 machine 也能 get_skills_dir)
	registered := false
	if _, err := machines.GetMachine(machine); err != nil {
		// 新别名: 预建空 machine 条目
		machines.Machines[machine] = config.MachineConfig{
			Name: machine, DisplayName: machine,
			Agents: map[string]config.AgentInstall{}, AgentOrder: []string{},
		}
		registered = true
	}

	changes := map[string]string{}
	var changeOrder []string // 输出确定性

	fmt.Printf("[scan] 机器 %q — 探测本机 %d 个 Agent 的 skills 目录\n\n", machine, len(agentsCfg.Names()))
	home, _ := os.UserHomeDir()
	for _, agent := range agentsCfg.Names() {
		cur := machines.GetSkillsDir(machine, agent)
		if cur != "" {
			if _, err := os.Stat(cur); err == nil {
				fmt.Printf("  ✓ %-12s 保持 %s(已配置且存在)\n", agent, cur)
				continue
			}
			fmt.Printf("  ? %-12s 已配置 %s 但盘上不存在\n", agent, cur)
		}
		cands := scan.DetectAgent(agent, home)
		if len(cands) == 0 {
			fmt.Printf("  ✗ %-12s 未探测到(没装?), 跳过 = sync 时忽略该 Agent\n", agent)
			continue
		}
		for i, c := range cands {
			fmt.Printf("    [%d] %s  (%s: %s)\n", i+1, c.Path, c.Confidence, c.Evidence)
		}
		if *dryRun {
			best := scan.PickBest(cands)
			fmt.Printf("    (dry-run) 将选 %s\n", best.Path)
			continue
		}
		if *yes || !a.TTY {
			best := scan.PickBest(cands)
			changes[agent] = best.Path
			changeOrder = append(changeOrder, agent)
			fmt.Printf("    → 自动选 %s(%s)\n", best.Path, best.Confidence)
			continue
		}
		defaultIdx := 1
		best := scan.PickBest(cands)
		for i := range cands {
			if best == &cands[i] {
				defaultIdx = i + 1
			}
		}
		ans := a.input(fmt.Sprintf("    用哪个? [1-%d](回车=%d) / m=<路径>手输 / s跳过: ",
			len(cands), defaultIdx))
		switch {
		case strings.EqualFold(ans, "s"):
			fmt.Printf("    → 跳过 %s\n", agent)
		case strings.HasPrefix(strings.ToLower(ans), "m=") && len(ans) > 2:
			changes[agent] = ans[2:]
			changeOrder = append(changeOrder, agent)
			fmt.Printf("    → 手输 %s\n", ans[2:])
		default:
			idx := defaultIdx
			if ans != "" {
				n := 0
				valid := true
				for _, c := range ans {
					if c < '0' || c > '9' {
						valid = false
						break
					}
					n = n*10 + int(c-'0')
				}
				if !valid || n < 1 || n > len(cands) {
					fmt.Printf("    → 输入无法解析, 跳过 %s\n", agent)
					continue
				}
				idx = n
			}
			changes[agent] = cands[idx-1].Path
			changeOrder = append(changeOrder, agent)
			fmt.Printf("    → 选 [%d] %s\n", idx, cands[idx-1].Path)
		}
	}

	if *dryRun {
		fmt.Println("\n[scan] dry-run 结束, 未写任何文件")
		return 0
	}
	if len(changes) == 0 {
		// 新注册的别名即使零探测也要落盘, 否则绑定与 machines.toml 不一致(sync 会拒)
		if registered {
			if err := machines.Save(filepath.Join(a.RepoRoot, "machines.toml")); err != nil {
				fmt.Printf("[scan] ✗ machines.toml 写入失败: %v\n", err)
				return 1
			}
			fmt.Printf("\n[scan] 新机器别名 %q 已注册进 machines.toml(本机未探测到任何 Agent 目录)\n", machine)
		} else {
			fmt.Println("\n[scan] 无变更, machines.toml 未动")
		}
		// 即使无变更也要绑定身份(跑 scan = 在本机使用, scan 只在本机跑)
		fmt.Printf("[scan] 本机身份绑定 → %s(%s)\n", machine, BindingNote)
		identity.WriteBinding(a.RepoRoot, machine)
		return 0
	}
	for _, agent := range changeOrder {
		machines.SetSkillsDir(machine, agent, changes[agent])
	}
	if err := machines.Save(filepath.Join(a.RepoRoot, "machines.toml")); err != nil {
		fmt.Printf("[scan] ✗ machines.toml 写入失败: %v\n", err)
		return 1
	}
	fmt.Printf("\n[scan] machines.toml 已更新: %s\n", strings.Join(changeOrder, ", "))
	fmt.Printf("[scan] 本机身份绑定 → %s(%s)\n", machine, BindingNote)
	identity.WriteBinding(a.RepoRoot, machine)
	return 0
}