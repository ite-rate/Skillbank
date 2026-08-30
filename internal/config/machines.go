// MachinesConfig — machines.toml 加载: 每机器 × 每 Agent 手填完整路径。
//
// 移植合同(对应 Python machines.py):
//   - 显式手填完整绝对路径 > install_dir + home 展开(同一 Agent 跨机器路径不保证一致)
//   - 不列某 Agent = 该机器没装 → sync 跳过不报错
//   - agents.toml 的 install_dir 仅文档参考, 唯一真相源是本文件
//   - load 校验: agent 名必须在 agents.toml(防拼写错); 路径必须以 / 开头
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/BurntSushi/toml"
)

// AgentInstall — 单 Agent 在某机器上的安装位置。
type AgentInstall struct {
	SkillsDir string `toml:"skills_dir"`
}

// MachineConfig — 单机器。
type MachineConfig struct {
	Name        string
	DisplayName string
	Agents      map[string]AgentInstall
	// AgentOrder — agents 声明序(TOML 文档序; render_toml 输出序跟随它,
	// 与 Python dict 插入序等价 — Go map 无序必须显式保留)。
	AgentOrder []string
}

func (m *MachineConfig) HasAgent(agent string) bool {
	_, ok := m.Agents[agent]
	return ok
}

// MachinesConfig — machines.toml 全表。
type MachinesConfig struct {
	Machines map[string]MachineConfig
	Path     string // 落盘位置; 空 = 内存态(测试用)
}

// LoadMachines — 读 + 校验 machines.toml。
// knownAgents 给定时校验配置里的 agent 名都在 agents.toml(拼写错早暴露)。
func LoadMachines(tomlPath string, knownAgents []string) (*MachinesConfig, error) {
	raw, err := os.ReadFile(tomlPath)
	if err != nil {
		return nil, err
	}
	var doc struct {
		Machines map[string]struct {
			DisplayName string `toml:"display_name"`
			Agents      map[string]AgentInstall `toml:"agents"`
		} `toml:"machines"`
	}
	md, err := toml.Decode(string(raw), &doc)
	if err != nil {
		return nil, fmt.Errorf("machines.toml 解析失败: %w", err)
	}
	known := map[string]bool{}
	for _, a := range knownAgents {
		known[a] = true
	}

	cfg := &MachinesConfig{Machines: map[string]MachineConfig{}, Path: tomlPath}
	for mName, mBody := range doc.Machines {
		mc := MachineConfig{
			Name:        mName,
			DisplayName: mBody.DisplayName,
			Agents:      map[string]AgentInstall{},
		}
		if mc.DisplayName == "" {
			mc.DisplayName = mName
		}
		for aName, inst := range mBody.Agents {
			if known != nil && len(knownAgents) > 0 && !known[aName] {
				return nil, fmt.Errorf("machines.toml: machine %q 配了未知 agent %q (不在 agents.toml;检查拼写)", mName, aName)
			}
			if !strings.HasPrefix(inst.SkillsDir, "/") {
				return nil, fmt.Errorf("machines.toml: %s.%s.skills_dir 必须是完整绝对路径(以 / 开头, 不支持 ~), got %q", mName, aName, inst.SkillsDir)
			}
			mc.Agents[aName] = inst
		}
		// agents 声明序(TOML 文档序, via MetaData)
		seen := map[string]bool{}
		for _, key := range md.Keys() {
			// key = [machines <m> agents <a>]
			if len(key) == 4 && key[0] == "machines" && key[1] == mName && key[2] == "agents" && !seen[key[3]] {
				seen[key[3]] = true
				mc.AgentOrder = append(mc.AgentOrder, key[3])
			}
		}
		if len(mc.AgentOrder) != len(mc.Agents) {
			// MetaData 未覆盖(异常兜底): 字典序, 保证 render 确定性
			mc.AgentOrder = nil
			for a := range mc.Agents {
				mc.AgentOrder = append(mc.AgentOrder, a)
			}
			sortStrings(mc.AgentOrder)
		}
		cfg.Machines[mName] = mc
	}
	return cfg, nil
}

// NewMachinesConfig — 空表(测试/内存态用)。
func NewMachinesConfig() *MachinesConfig {
	return &MachinesConfig{Machines: map[string]MachineConfig{}}
}

// GetMachine — 取机器配置(不在 → 错误, 可用名单按字典序, 对应 Python KeyError 文案)。
func (mc *MachinesConfig) GetMachine(machine string) (MachineConfig, error) {
	m, ok := mc.Machines[machine]
	if !ok {
		names := make([]string, 0, len(mc.Machines))
		for n := range mc.Machines {
			names = append(names, n)
		}
		sort.Strings(names)
		return m, fmt.Errorf("machine %q 不在 machines.toml(可用: %v)", machine, names)
	}
	return m, nil
}

// GetSkillsDir — 该机器上该 Agent 的 skills 目录绝对路径; 没配 = 空(没装, 跳过)。
func (mc *MachinesConfig) GetSkillsDir(machine, agent string) string {
	m, ok := mc.Machines[machine]
	if !ok {
		return ""
	}
	inst, ok := m.Agents[agent]
	if !ok {
		return ""
	}
	return inst.SkillsDir
}

// MachinesWithAgent — 配置了该 Agent 的机器名(字典序)。
func (mc *MachinesConfig) MachinesWithAgent(agent string) []string {
	var out []string
	for name, m := range mc.Machines {
		if m.HasAgent(agent) {
			out = append(out, name)
		}
	}
	sort.Strings(out)
	return out
}

// SetSkillsDir — scan 确认后写回内存; 再 RenderTOML+Save 落盘。机器不存在则建。
func (mc *MachinesConfig) SetSkillsDir(machine, agent, skillsDir string) {
	m, ok := mc.Machines[machine]
	if !ok {
		m = MachineConfig{Name: machine, DisplayName: machine, Agents: map[string]AgentInstall{}}
		mc.Machines[machine] = m
	}
	if _, exists := m.Agents[agent]; !exists {
		m.AgentOrder = append(m.AgentOrder, agent)
	}
	m.Agents[agent] = AgentInstall{SkillsDir: skillsDir}
	mc.Machines[machine] = m
}

// RenderTOML — 重新生成 machines.toml 文本(标准头部注释 + 全部机器/Agent)。
// 注意: 会丢弃手写的行内注释 — scan 确认过的值本身就是结论。
func (mc *MachinesConfig) RenderTOML() string {
	var b strings.Builder
	b.WriteString("# Skillbank machines.toml — 每机器 × 每 Agent 手填/scan 确认的完整绝对路径\n")
	b.WriteString("#\n")
	b.WriteString("# 规则:\n")
	b.WriteString("#   - skills_dir 完整绝对路径(不支持 ~);由 `skillbank scan` 在该机器上\n")
	b.WriteString("#     自动探测 + 确认后写入, 也可手改\n")
	b.WriteString("#   - 不列某 Agent = 该机器没装, sync 跳过不报错\n")
	b.WriteString("#   - agents.toml 的 install_dir 仅为文档参考, 唯一真相源是本文件\n")
	b.WriteString("\n")

	names := make([]string, 0, len(mc.Machines))
	for n := range mc.Machines {
		names = append(names, n)
	}
	sort.Strings(names)
	for _, mName := range names {
		m := mc.Machines[mName]
		fmt.Fprintf(&b, "[machines.%s]\n", mName)
		fmt.Fprintf(&b, "display_name = %q\n", m.DisplayName)
		b.WriteString("\n")
		for _, aName := range m.AgentOrder {
			inst := m.Agents[aName]
			fmt.Fprintf(&b, "[machines.%s.agents.%s]\n", mName, aName)
			fmt.Fprintf(&b, "skills_dir = %q\n", inst.SkillsDir)
			b.WriteString("\n")
		}
	}
	return b.String()
}

// Save — RenderTOML 原子写回(tmp + replace)。
func (mc *MachinesConfig) Save(path string) error {
	p := path
	if p == "" {
		p = mc.Path
	}
	if p == "" {
		return fmt.Errorf("no machines.toml path given")
	}
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		return err
	}
	tmp := p + ".tmp"
	if err := os.WriteFile(tmp, []byte(mc.RenderTOML()), 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, p)
}

// CheckPathsExist — doctor 用: 该机器配置的所有 skills_dir 盘上存在性。
//
// 返回 (errors, warnings):
//   - error:   skills_dir 连父目录都没有 → Agent 大概率没装或路径填错
//   - warning: skills_dir 不存在但父目录在 → 正常(目录惰性未建, emitter mkdir 自动创建)
func (mc *MachinesConfig) CheckPathsExist(machine string) ([]string, []string) {
	m, err := mc.GetMachine(machine)
	if err != nil {
		return []string{err.Error()}, nil
	}
	var errs, warns []string
	for _, aName := range m.AgentOrder {
		p := m.Agents[aName].SkillsDir
		if _, err := os.Stat(p); err == nil {
			continue
		}
		if _, err := os.Stat(filepath.Dir(p)); err == nil {
			warns = append(warns, fmt.Sprintf("%s: %s 尚不存在(从未部署过? emitter 会自动创建)", aName, p))
		} else {
			errs = append(errs, fmt.Sprintf("%s: %s 父目录都不存在(Agent 没装? 路径填错?)", aName, p))
		}
	}
	return errs, warns
}