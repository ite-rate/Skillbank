// pull 子命令 — 中心仓 git pull → sync → doctor 一键日常动线。
//
//	skillbank pull [--to <machine>] [--agent <名>] [--skill <名>]...
//	             [--yes] [--dry-run] [--no-doctor]
//
// 语义:
//   - 脏工作区 → 中止(pull 可能半合并; --yes 也不豁免)
//   - 无 remote(本地-only 仓库)→ 跳过 pull 继续 sync
//   - pull --ff-only; 分叉 → 提示手动解决, 绝不 reset
//   - doctor 默认跑、非致命(--no-doctor 给脚本党)
//   - --dry-run 跳过部署执行, 不跳过 git pull(dry-run ≠ 零副作用)
package cli

import (
	"fmt"
	"os"
	"strings"

	"github.com/ite-rate/skillbank/internal/bootstrap"
)

func (a *App) cmdPull(args []string) int {
	fs := newFlagSet("to", "agent", "skill", "yes", "dry-run", "no-doctor")
	machineFlag := fs.strP("to", "")
	agentFlag := fs.strP("agent", "")
	skillFlag := fs.sliceP("skill")
	yes := fs.boolP("yes")
	dryRun := fs.boolP("dry-run")
	noDoctor := fs.boolP("no-doctor")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[pull] %s\n", msg)
		return 2
	}

	_, _, err := a.loadConfigs()
	_, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[pull] ✗ %v\n", err)
		return 1
	}
	machine, rc := a.resolveMachine("pull", machines, *machineFlag, true)
	if rc != 0 {
		return rc
	}

	// 阶段 1: git pull(有 remote 才拉)
	fmt.Println("[pull] 阶段 1/3: 更新中心仓")
	if !bootstrap.HasGitDir(a.RepoRoot) {
		fmt.Println("[pull] ✗ 中心仓不是 git 仓(缺 .git)。先 skillbank init 或 bootstrap")
		return 1
	}
	if bootstrap.HasRemote(a.RepoRoot) {
		dirty, err := bootstrap.IsDirty(a.RepoRoot)
		if err != nil {
			fmt.Printf("[pull] ✗ git status 失败: %v\n", err)
			return 1
		}
		if dirty {
			fmt.Printf("[pull] ✗ 中心仓有未提交改动(git status 非空)。pull 可能半合并, 已中止。\n")
			fmt.Printf("[pull]   先 git -C %s stash / commit / 复原后重试; --yes 不豁免此项\n", a.RepoRoot)
			return 1
		}
		if err := bootstrap.PullFastForward(a.RepoRoot); err != nil {
			msg := err.Error()
			fmt.Printf("[pull] ✗ %s\n", msg)
			if strings.Contains(msg, "CONFLICT") || strings.Contains(msg, "divergent") || strings.Contains(msg, "Not possible") {
				fmt.Printf("[pull]   中心仓与远端分叉: 手动 git -C %s pull 解决后重跑 skillbank pull\n", a.RepoRoot)
			}
			return 1
		}
		fmt.Println("[pull] 已更新(git pull --ff-only)")
	} else {
		fmt.Println("[pull] 本地仓无 remote, 跳过 pull(本地-only 仓库)")
	}

	// 阶段 2: sync(与 bootstrap 同款链式)
	fmt.Printf("[pull] 阶段 2/3: 同步 canonical → %s\n", machine)
	var syncArgs []string
	for _, s := range *skillFlag {
		syncArgs = append(syncArgs, "--skill", s)
	}
	if *agentFlag != "" {
		syncArgs = append(syncArgs, "--agent", *agentFlag)
	}
	if *machineFlag != "" {
		syncArgs = append(syncArgs, "--to", *machineFlag)
	}
	switch {
	case *dryRun:
		syncArgs = append(syncArgs, "--dry-run")
	case *yes || !a.TTY:
		syncArgs = append(syncArgs, "--yes")
	}
	if rc := a.cmdSync(syncArgs); rc != 0 {
		return rc
	}

	if *noDoctor {
		return 0
	}
	fmt.Println("[pull] 阶段 3/3: 体检")
	if rc := a.cmdDoctor([]string{"--machine", machine}); rc != 0 {
		fmt.Println("[pull] ⚠ doctor 报告了问题(见上); 同步已完成")
	}
	return 0
}