// Package bootstrap — 新机器/零仓库用户的一条龙入口。
//
//   bootstrap — 云服务器场景: clone repo → scan 探测 → 绑定身份 → sync
//   init       — 零仓库用户: 当前目录脚手架成新 skillbank repo(skills/ +
//                manifests/ + agents.toml + machines.toml + git init)
package bootstrap

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/BurntSushi/toml"
)

// AppConfig — ~/.config/skillbank/config.toml(用户级, 不进任何 repo)。
type AppConfig struct {
	RepoPath string `toml:"repo_path"` // skillbank repo 的本地绝对路径
	RepoURL  string `toml:"repo_url"`  // 中心仓库 git URL(bootstrap 用)
}

// ConfigPath — 用户级 config.toml 路径。
func ConfigPath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".config", "skillbank", "config.toml"), nil
}

// LoadConfig — 读用户级 config;文件不存在 = 空 config(不是错误)。
func LoadConfig() (AppConfig, string, error) {
	p, err := ConfigPath()
	if err != nil {
		return AppConfig{}, "", err
	}
	var cfg AppConfig
	raw, err := os.ReadFile(p)
	if err != nil {
		if os.IsNotExist(err) {
			return AppConfig{}, p, nil
		}
		return AppConfig{}, p, err
	}
	if err := toml.Unmarshal(raw, &cfg); err != nil {
		return AppConfig{}, p, fmt.Errorf("config.toml 解析失败: %w", err)
	}
	cfg.RepoPath = strings.TrimSpace(cfg.RepoPath)
	cfg.RepoURL = strings.TrimSpace(cfg.RepoURL)
	return cfg, p, nil
}

// SaveConfig — 写用户级 config(原子)。
func SaveConfig(cfg AppConfig) (string, error) {
	p, err := ConfigPath()
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		return "", err
	}
	var b strings.Builder
	b.WriteString("# skillbank 用户级配置(本机; 不进 repo)\n")
	if cfg.RepoPath != "" {
		fmt.Fprintf(&b, "repo_path = %q\n", cfg.RepoPath)
	}
	if cfg.RepoURL != "" {
		fmt.Fprintf(&b, "repo_url = %q\n", cfg.RepoURL)
	}
	b.WriteString("\n")
	tmp := p + ".tmp"
	if err := os.WriteFile(tmp, []byte(b.String()), 0o644); err != nil {
		return "", err
	}
	if err := os.Rename(tmp, p); err != nil {
		return "", err
	}
	return p, nil
}

// Clone — git clone <url> 到 dest(浅克隆)。返回 stderr 摘要(失败时)。
func Clone(url, dest string) error {
	cmd := exec.Command("git", "clone", "--depth", "1", url, dest)
	out, err := cmd.CombinedOutput()
	if err != nil {
		msg := strings.TrimSpace(string(out))
		if len(msg) > 300 {
			msg = msg[:300]
		}
		return fmt.Errorf("git clone 失败: %s", msg)
	}
	return nil
}

// agentsTomlTemplate — init 脚手架用的 agents.toml 模板(等价于中心仓的
// agents.toml;导出供测试等需要影子 7 agent 配置的场景复用)。
const AgentsTomlTemplate = `# Skillbank agents.toml — 7 个 Agent 的集成方式配置
# emitter 读取本文件决定如何把 canonical SKILL.md 部署到各 Agent。
# 全部 Agent 一律 cp 部署(7 个 emitter 均硬编码 cp)。

[agents.ClaudeCode]
display_name = "Claude Code"
install_dir = "~/.claude/skills"
disable_invoke_field = "disable-model-invocation"
disable_invoke_value = true
note = "Anthropic Skill 标准本尊; body 透传"

[agents.ZCode]
display_name = "ZCode"
install_dir = "~/.zcode/skills"
disable_invoke_field = "disable-model-invocation"
disable_invoke_value = true

[agents.QwenWorkCN]
display_name = "QwenWorkCN 千问办公"
install_dir = "~/.qwenworkcn/skills"
disable_invoke_field = "enabled_at"
disable_invoke_value = false

[agents.TeleAgent]
display_name = "TeleAgent"
install_dir = "~/.config/TeleAgent/skills"
disable_invoke_field = "enabled_at"
disable_invoke_value = false

[agents.Hermes]
display_name = "Hermes"
install_dir = "~/.hermes/skills"
default_category = "imported"
disable_invoke_field = "metadata.hermes.disable-model-invocation"
disable_invoke_value = true
description_max = 1024
file_size_max = 100000

[agents.Codex]
display_name = "Codex"
install_dir = "~/.codex/skills"
disable_invoke_field = "disable-model-invocation"
disable_invoke_value = true
description_max = 1024

[agents.kimi-code]
display_name = "kimi-code"
install_dir = "~/.kimi-code/skills"
note = "无 frontmatter 字段需求(走 kimi 默认 discovery)"
`

const machinesTomlTemplate = `# Skillbank machines.toml — 机器档案(每台机器装了哪些 Agent、skills 目录在哪)
# 首次在本机使用: skillbank scan --machine <别名> 探测并自动填写。
`

// InitRepo — 当前目录脚手架成新 skillbank repo(已存在的文件不覆盖)。
// 返回脚手架产物列表。
func InitRepo(dir string) ([]string, error) {
	var created []string
	mk := func(rel, content string) error {
		p := filepath.Join(dir, rel)
		if _, err := os.Stat(p); err == nil {
			return nil // 已存在不覆盖(重复 init 幂等)
		}
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
			return err
		}
		created = append(created, rel)
		return nil
	}
	if err := mk("skills/.gitkeep", ""); err != nil {
		return nil, err
	}
	if err := mk("manifests/.gitkeep", ""); err != nil {
		return nil, err
	}
	if err := mk("agents.toml", AgentsTomlTemplate); err != nil {
		return nil, err
	}
	if err := mk("machines.toml", machinesTomlTemplate); err != nil {
		return nil, err
	}
	if err := mk(".gitignore", "# 本机身份绑定, 不进 git\n.skillbank-machine\n"); err != nil {
		return nil, err
	}
	// git init(已是 repo 则 no-op)
	if _, err := os.Stat(filepath.Join(dir, ".git")); os.IsNotExist(err) {
		cmd := exec.Command("git", "init", dir)
		if out, err := cmd.CombinedOutput(); err != nil {
			return created, fmt.Errorf("git init 失败: %s", strings.TrimSpace(string(out)))
		}
		created = append(created, "(git init)")
	}
	return created, nil
}