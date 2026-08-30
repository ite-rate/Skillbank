// Package config — agents.toml / machines.toml 加载 + skillbank 用户 config。
//
// agents.toml(对应 Python agents.py): 每 Agent 的集成方式。
// install_dir 仅文档参考, 部署路径唯一真相源是 machines.toml 手填 skills_dir。
package config

import (
	"os"

	"github.com/BurntSushi/toml"
)

// AgentConfig — 单个 Agent 的集成方式(agents.toml [agents.<name>])。
type AgentConfig struct {
	Name              string `toml:"-"`
	DisplayName       string `toml:"display_name"`
	InstallDir        string `toml:"install_dir"` // 仅文档参考, 部署不用
	DisableInvokeField string `toml:"disable_invoke_field"`
	DisableInvokeValue any    `toml:"disable_invoke_value"`
	DescriptionMax    int    `toml:"description_max"`  // 0 = 无限制
	FileSizeMax       int    `toml:"file_size_max"`    // 0 = 无限制
	DefaultCategory   string `toml:"default_category"`
	SkillsDirConfigKey string `toml:"skills_dir_config_key"`
	Note              string `toml:"note"`
}

// NeedsDisableInvoke — level 非 auto 时写 DisableInvokeField(空 = 该 Agent 无此字段, 如 kimi)。
func (c *AgentConfig) NeedsDisableInvoke(level string) bool {
	return c.DisableInvokeField != "" &&
		(level == "manual" || level == "experimental" || level == "disable")
}

// AgentsConfig — agents.toml 全表。
type AgentsConfig struct {
	Agents map[string]AgentConfig `toml:"agents"`
	// Order — agents.toml 声明序(Go map 无序, 用 toml MetaData 保留文档顺序;
	// sync 部署序 / list 列序跟随它, 与 Python dict 序等价)。
	Order []string `toml:"-"`
}

// LoadAgents — 读 agents.toml。
func LoadAgents(path string) (*AgentsConfig, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cfg AgentsConfig
	md, err := toml.Decode(string(raw), &cfg)
	if err != nil {
		return nil, err
	}
	for name, a := range cfg.Agents {
		a.Name = name
		cfg.Agents[name] = a
	}
	// 保留 agents 声明序(文档顺序)
	seen := map[string]bool{}
	for _, key := range md.Keys() {
		if len(key) == 2 && key[0] == "agents" && !seen[key[1]] {
			seen[key[1]] = true
			cfg.Order = append(cfg.Order, key[1])
		}
	}
	return &cfg, nil
}

// Get — 按 agent 名取配置(不存在 panic 同 Python KeyError 语义, 调用方保证存在)。
func (ac *AgentsConfig) Get(name string) *AgentConfig {
	a, ok := ac.Agents[name]
	if !ok {
		return &AgentConfig{Name: name}
	}
	return &a
}

// Names — agents 声明序(agents.toml 文档顺序;缺 Order 时按字典序兜底)。
func (ac *AgentsConfig) Names() []string {
	if len(ac.Order) == len(ac.Agents) && len(ac.Order) > 0 {
		return ac.Order
	}
	out := make([]string, 0, len(ac.Agents))
	for name := range ac.Agents {
		out = append(out, name)
	}
	sortStrings(out)
	return out
}

func sortStrings(s []string) {
	for i := 1; i < len(s); i++ {
		for j := i; j > 0 && s[j] < s[j-1]; j-- {
			s[j], s[j-1] = s[j-1], s[j]
		}
	}
}