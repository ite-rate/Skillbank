// skillbank CLI 入口。
package main

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/ite-rate/skillbank/internal/bootstrap"
	"github.com/ite-rate/skillbank/internal/cli"
)

// resolveRepoRoot — repo 根解析链(Python __file__ 推导的 Go 等价物):
//
//	--repo <path> > SKILLBANK_REPO env > ~/.config/skillbank/config.toml 的
//	repo_path > cwd 向上找(含 agents.toml 的目录)
//
// bootstrap / init 不要求已有 repo(返回 ""), 其余命令找不到 repo 时报错退出。
func resolveRepoRoot(args []string) (string, []string, bool) {
	for i, a := range args {
		if a == "--repo" && i+1 < len(args) {
			abs, err := filepath.Abs(args[i+1])
			if err != nil {
				fmt.Fprintf(os.Stderr, "✗ --repo 路径无效: %s\n", args[i+1])
				os.Exit(2)
			}
			rest := append(append([]string{}, args[:i]...), args[i+2:]...)
			return abs, rest, true
		}
	}
	if env := os.Getenv("SKILLBANK_REPO"); env != "" {
		if abs, err := filepath.Abs(env); err == nil {
			return abs, args, true
		}
	}
	if cfg, _, err := bootstrap.LoadConfig(); err == nil && cfg.RepoPath != "" {
		if _, err := os.Stat(filepath.Join(cfg.RepoPath, "agents.toml")); err == nil {
			return cfg.RepoPath, args, true
		}
	}
	// cwd 向上找
	dir, err := os.Getwd()
	if err == nil {
		for {
			if _, err := os.Stat(filepath.Join(dir, "agents.toml")); err == nil {
				return dir, args, true
			}
			parent := filepath.Dir(dir)
			if parent == dir {
				break
			}
			dir = parent
		}
	}
	return "", args, false
}

func main() {
	args := os.Args[1:]
	first := ""
	if len(args) > 0 {
		first = args[0]
	}
	needRepo := first != "bootstrap" && first != "init"
	repoRoot, rest, found := resolveRepoRoot(args)
	if needRepo && !found {
		fmt.Fprintln(os.Stderr, "✗ 找不到 skillbank repo。任选其一:")
		fmt.Fprintln(os.Stderr, "  · 在 repo 目录里运行(或用 --repo <path> / SKILLBANK_REPO)")
		fmt.Fprintln(os.Stderr, "  · 已配置过的机器: ~/.config/skillbank/config.toml 的 repo_path")
		fmt.Fprintln(os.Stderr, "  · 新机器: skillbank bootstrap --repo-url <url> --machine <别名>")
		fmt.Fprintln(os.Stderr, "  · 从零开始: 空目录里 skillbank init")
		os.Exit(2)
	}
	// bootstrap/init 不吃全局 --repo 之外的位置参数冲突; found=false 时 RepoRoot 为空
	app := &cli.App{
		RepoRoot: repoRoot,
		TTY:      isTTY(),
	}
	os.Exit(app.Run(rest))
}

func isTTY() bool {
	fi, err := os.Stdin.Stat()
	if err != nil {
		return false
	}
	return fi.Mode()&os.ModeCharDevice != 0
}