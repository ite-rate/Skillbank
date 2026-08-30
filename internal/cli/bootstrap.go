// bootstrap / init 子命令 — 新机器一条龙 + 零仓库脚手架。
package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/ite-rate/skillbank/internal/bootstrap"
	"github.com/ite-rate/skillbank/internal/identity"
)

// cmdInit — 当前目录脚手架成新 skillbank repo(零仓库用户的第一步)。
//
// 产物: skills/ + manifests/ + agents.toml + machines.toml + .gitignore + git init。
// 已存在的文件不覆盖(重复 init 幂等)。
func (a *App) cmdInit(args []string) int {
	dir := a.RepoRoot
	if dir == "" {
		d, err := os.Getwd()
		if err != nil {
			fmt.Printf("[init] ✗ %v\n", err)
			return 1
		}
		dir = d
	}
	created, err := bootstrap.InitRepo(dir)
	if err != nil {
		fmt.Printf("[init] ✗ %v\n", err)
		return 1
	}
	fmt.Printf("[init] repo 脚手架: %s\n", dir)
	if len(created) == 0 {
		fmt.Println("  全部已存在, 无新文件(幂等)")
	}
	for _, f := range created {
		fmt.Printf("  + %s\n", f)
	}
	fmt.Println("[init] 下一步:")
	fmt.Printf("  1. 本机探测 Agent 目录并注册: skillbank scan --machine <别名>(repo: %s)\n", dir)
	fmt.Println("  2. 把既有 skill 收进中心仓: skillbank add <目录> / skillbank import <agent 的 skill 目录>")
	fmt.Println("  3. 推到本机各 Agent: skillbank sync")
	return 0
}

// cmdBootstrap — 云服务器/新机器一条龙: clone repo → scan 探测+绑定 → sync。
//
//	skillbank bootstrap [--repo-url <url>] [--machine <别名>] [--yes] [--dry-run]
//
// repo 解析: 本地已有 repo(--repo/env/config.repo_path)→ 跳过 clone;
// 没有 → git clone <repo_url> ~/Skillbank 并写回 config.repo_path。
func (a *App) cmdBootstrap(args []string) int {
	fs := newFlagSet("repo-url", "machine", "yes", "dry-run")
	repoURL := fs.strP("repo-url", "")
	machineFlag := fs.strP("machine", "")
	yes := fs.boolP("yes")
	dryRun := fs.boolP("dry-run")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[bootstrap] %s\n", msg)
		return 2
	}

	cfg, cfgPath, err := bootstrap.LoadConfig()
	if err != nil {
		fmt.Printf("[bootstrap] ✗ %v\n", err)
		return 1
	}

	// 1. repo: 本地已有 → 直接用; 没有 → clone
	if a.RepoRoot == "" {
		url := *repoURL
		if url == "" {
			url = cfg.RepoURL
		}
		if url == "" {
			fmt.Println("[bootstrap] ✗ 本地无 skillbank repo 且未给 --repo-url。二选一:")
			fmt.Println("  a. 已有中心仓: skillbank bootstrap --repo-url <git URL>")
			fmt.Println("  b. 从零开始: 在空目录跑 `skillbank init`, 把它推到 git 作为中心仓")
			return 2
		}
		home, err := os.UserHomeDir()
		if err != nil {
			fmt.Printf("[bootstrap] ✗ %v\n", err)
			return 1
		}
		dest := filepath.Join(home, "Skillbank")
		if _, err := os.Stat(filepath.Join(dest, "agents.toml")); err == nil {
			fmt.Printf("[bootstrap] ~/Skillbank 已存在, 直接使用(不重新 clone)\n")
		} else {
			if _, err := os.Stat(dest); err == nil {
				fmt.Printf("[bootstrap] ✗ %s 已存在但不是 skillbank repo(缺 agents.toml), 请先处理\n", dest)
				return 1
			}
			fmt.Printf("[bootstrap] git clone %s → %s\n", url, dest)
			if err := bootstrap.Clone(url, dest); err != nil {
				fmt.Printf("[bootstrap] ✗ %v\n", err)
				return 1
			}
		}
		cfg.RepoPath = dest
		cfg.RepoURL = url
		if p, err := bootstrap.SaveConfig(cfg); err != nil {
			fmt.Printf("[bootstrap] ⚠ config 写入失败: %v\n", err)
		} else {
			fmt.Printf("[bootstrap] config 已写入: %s(repo_path 以后自动生效)\n", p)
		}
		a.RepoRoot = dest
	} else {
		fmt.Printf("[bootstrap] 使用本地 repo: %s\n", a.RepoRoot)
	}
	_ = cfgPath

	// 2. 机器别名: --machine > 已绑定
	machine := *machineFlag
	if machine == "" {
		machine = identity.ReadBinding(a.RepoRoot)
	}
	if machine == "" {
		fmt.Println("[bootstrap] ✗ 未指定本机别名。首次使用请: skillbank bootstrap --machine <别名> --repo-url <url>")
		return 2
	}
	fmt.Printf("[bootstrap] 本机别名: %s\n", machine)

	// 3. scan 探测 + machines.toml + 绑定身份(等价 scan --machine X --yes)
	fmt.Println("[bootstrap] 阶段 1/3: 探测本机 Agent skills 目录")
	if rc := a.cmdScan([]string{"--machine", machine, "--yes"}); rc != 0 {
		return rc
	}

	// 4. sync(collect → show → confirm → execute)
	fmt.Println("[bootstrap] 阶段 2/3: 同步 canonical → 本机 Agents")
	syncArgs := []string{}
	if *dryRun {
		syncArgs = append(syncArgs, "--dry-run")
	} else if *yes || !a.TTY {
		syncArgs = append(syncArgs, "--yes")
	}
	if rc := a.cmdSync(syncArgs); rc != 0 {
		return rc
	}
	if *dryRun {
		fmt.Println("[bootstrap] dry-run 结束, 未写任何部署文件")
		return 0
	}

	// 5. doctor 汇总
	fmt.Println("[bootstrap] 阶段 3/3: 体检汇总")
	if rc := a.cmdDoctor([]string{"--machine", machine}); rc != 0 {
		fmt.Println("[bootstrap] ⚠ doctor 报告了问题(见上), bootstrap 仍算完成")
		return 0
	}
	fmt.Println("[bootstrap] 完成 ✓")
	return 0
}