// Package bootstrap 的 git 助手 — pull 命令的工作区/远端操作。
// (Clone 之邻, 同款 CombinedOutput + 300 字截断纪律)
package bootstrap

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// HasGitDir — repoRoot 是否是 git 仓(有 .git)。
func HasGitDir(repoRoot string) bool {
	_, err := os.Stat(filepath.Join(repoRoot, ".git"))
	return err == nil
}

// IsDirty — git status --porcelain 非空 = 有未提交改动。
func IsDirty(repoRoot string) (bool, error) {
	out, err := exec.Command("git", "-C", repoRoot, "status", "--porcelain").Output()
	if err != nil {
		return false, err
	}
	return len(strings.TrimSpace(string(out))) > 0, nil
}

// HasRemote — 是否配置了 remote(空输出 = 本地-only 仓库)。
func HasRemote(repoRoot string) bool {
	out, err := exec.Command("git", "-C", repoRoot, "remote").Output()
	return err == nil && strings.TrimSpace(string(out)) != ""
}

// PullFastForward — git pull --ff-only(单人仓合同; 绝不 reset/merge 造提交)。
func PullFastForward(repoRoot string) error {
	out, err := exec.Command("git", "-C", repoRoot, "pull", "--ff-only").CombinedOutput()
	if err != nil {
		msg := strings.TrimSpace(string(out))
		if len(msg) > 300 {
			msg = msg[:300]
		}
		return fmt.Errorf("git pull --ff-only 失败: %s", msg)
	}
	return nil
}