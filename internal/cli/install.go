// install 子命令 — 一条龙: git URL 导入中心仓 → 仅同步本次导入的 skill。
//
//	skillbank install <git-url> [--level L] [--force] [--machine <别名>]
//	                   [--agent <名>] [--yes] [--dry-run]
//
// 与 add 的关系: add 只导入; install 导入 + 链式 sync(bootstrap 链式样板)。
// 默认只同步新导入的 skill(--skill 过滤), 不 bulk 部署既有 canonical。
package cli

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/ite-rate/skillbank/internal/importer"
)

func (a *App) cmdInstall(args []string) int {
	fs := newFlagSet("level", "force", "machine", "agent", "yes", "dry-run")
	level := fs.strP("level", "manual")
	force := fs.boolP("force")
	machineFlag := fs.strP("machine", "")
	agentFlag := fs.strP("agent", "")
	yes := fs.boolP("yes")
	dryRun := fs.boolP("dry-run")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[install] %s\n", msg)
		return 2
	}
	if len(fs.args) == 0 {
		fmt.Fprintln(os.Stderr, "[install] 缺 <git-url>; 本地目录导入用 add")
		return 2
	}
	if !validLevel(*level) {
		fmt.Fprintf(os.Stderr, "[install] --level 必须是 %s 之一\n", strings.Join(levelValues, "/"))
		return 2
	}
	src := fs.args[0]
	if !isGitURL(src) {
		fmt.Fprintln(os.Stderr, "[install] 只收 git URL(http(s):// git@ ssh://); 本地目录用 add")
		return 2
	}

	// agents/machines 先加载(fail fast 在 clone 之前)
	_, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[install] ✗ %v\n", err)
		return 1
	}
	machine, rc := a.resolveMachine("install", machines, *machineFlag, false)
	machineUnresolved := rc != 0

	// 导入(交互重名: tty 且非 --yes 时问用户, 同 add)
	fmt.Printf("[install] 阶段 1/2: 从 git URL 导入 → 中心仓\n")
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
	results, err := importer.ImportGitURL(src, a.RepoRoot, opts)
	if errors.Is(err, errUserSkip) {
		fmt.Printf("[install] 跳过: %v\n", err)
		return 0
	}
	if err != nil {
		if len(results) > 0 {
			for _, r := range results {
				fmt.Printf("[install] 导入 → %s\n", r.CanonicalDir)
			}
		}
		fmt.Printf("[install] ✗: %v\n", err)
		return 1
	}
	var names []string
	for _, r := range results {
		fmt.Printf("[install] 导入 → %s\n", r.CanonicalDir)
		if r.Source != "" {
			fmt.Printf("[install] 来源  %s", r.Source)
			if r.Commit != "" {
				fmt.Printf("@%s", r.Commit[:min(len(r.Commit), 12)])
			}
			fmt.Println()
		}
		for _, w := range r.Warnings {
			fmt.Printf("  ⚠ %s\n", w)
		}
		names = append(names, filepath.Base(r.CanonicalDir))
	}
	if len(names) == 0 {
		fmt.Println("[install] 没有导入任何 skill(全部跳过)")
		return 0
	}

	if machineUnresolved {
		fmt.Println("[install] ⚠ 未同步: 机器别名未解析(原因见上 ✗ 行)。")
		fmt.Println("[install]   导入已完成; 先 skillbank use <别名> 或 scan --machine <别名>, 再 skillbank sync")
		fmt.Println("[install] 下一步: 改动记得 commit + push 中心仓(跨机同步靠 git)")
		return 0
	}

	// 阶段 2: 只同步本次导入的 skill(旗标须与 cmdSync 的 newFlagSet 严格一致)
	fmt.Printf("[install] 阶段 2/2: 同步 %d 个新 skill → %s\n", len(names), machine)
	var syncArgs []string
	for _, n := range names {
		syncArgs = append(syncArgs, "--skill", n)
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
	rcc := a.cmdSync(syncArgs)
	if rcc == 0 {
		fmt.Println("[install] 下一步: 改动记得 commit + push 中心仓(跨机同步靠 git)")
	}
	return rcc
}