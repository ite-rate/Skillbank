// Package identity — 本机身份绑定(这台 clone 所在的机器是谁)。
//
// 移植合同(对应 Python identity.py, 2026-08-30 修 #1):
// 此前 --machine 硬编码默认 "mac-main", 在另一台机器上裸跑 sync/rm 会按
// mac-main 的 manifest 记录操作本机磁盘文件 → 删错机器上的副本。
//
// 机制: repo 内 gitignored 文件 `.skillbank-machine` 存一行机器别名。
//   - 绑定: `skillbank use <别名>` 或 `skillbank scan --machine <别名>`
//   - 解析: 显式 flag > 绑定值; 未绑定/绑定过期 → 错误 + 指引, 不静默回退
//   - 显式 flag ≠ 绑定值: CLI 层对动本机磁盘的命令打 ⚠ 警告
package identity

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/ite-rate/skillbank/internal/config"
)

// BindingFilename — repo 内 gitignored 绑定文件名。
const BindingFilename = ".skillbank-machine"

// BindingPath — 绑定文件路径。
func BindingPath(repoRoot string) string {
	return filepath.Join(repoRoot, BindingFilename)
}

// ReadBinding — 本机绑定的机器别名; 文件缺失/空 → ""(未绑定)。
func ReadBinding(repoRoot string) string {
	raw, err := os.ReadFile(BindingPath(repoRoot))
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(raw))
}

// WriteBinding — 原子写绑定文件(tmp + rename); 返回绑定文件路径。
func WriteBinding(repoRoot, alias string) (string, error) {
	p := BindingPath(repoRoot)
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		return "", err
	}
	tmp := p + ".tmp"
	if err := os.WriteFile(tmp, []byte(strings.TrimSpace(alias)+"\n"), 0o644); err != nil {
		return "", err
	}
	if err := os.Rename(tmp, p); err != nil {
		return "", err
	}
	return p, nil
}

func sortedMachines(machines *config.MachinesConfig) []string {
	names := make([]string, 0, len(machines.Machines))
	for n := range machines.Machines {
		names = append(names, n)
	}
	sort.Strings(names)
	return names
}

// ResolveMachine — 解析本次命令作用的 machine 别名。
//
//   - explicit 传了: 校验在 machines.toml 里后返回(flag 显式 > 绑定)
//   - 否则读本机绑定: 未绑定 / 绑定值已不在 machines.toml → 错误(人话指引)
func ResolveMachine(repoRoot string, machines *config.MachinesConfig,
	explicit string) (string, error) {
	if explicit != "" {
		if _, ok := machines.Machines[explicit]; !ok {
			return "", fmt.Errorf("未知机器 %q(machines.toml: %v);先 `skillbank scan --machine <别名>` 注册",
				explicit, sortedMachines(machines))
		}
		return explicit, nil
	}

	bound := ReadBinding(repoRoot)
	if bound == "" {
		return "", fmt.Errorf("本机身份未绑定 — 拒绝按默认机器操作(防在别的机器上误动 mac-main 的记录)。"+
			"首次在本机使用: `skillbank use <别名>` 或 `skillbank scan --machine <别名>`(可用: %v)",
			sortedMachines(machines))
	}
	if _, ok := machines.Machines[bound]; !ok {
		return "", fmt.Errorf("本机绑定 %q 已不在 machines.toml(过期/被删)。"+
			"重新绑定: `skillbank use <别名>` 或 `skillbank scan --machine <别名>`(可用: %v)",
			bound, sortedMachines(machines))
	}
	return bound, nil
}