// machines.toml 加载器测试(移植 tests/test_machines.py 9 条, 语义等价)。
package config_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/ite-rate/skillbank/internal/config"
)

func repoRoot(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, "agents.toml")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatal("找不到 repo 根(agents.toml)")
		}
		dir = parent
	}
}

func loadRealMachines(t *testing.T) *config.MachinesConfig {
	t.Helper()
	agents, err := config.LoadAgents(filepath.Join(repoRoot(t), "agents.toml"))
	if err != nil {
		t.Fatal(err)
	}
	m, err := config.LoadMachines(filepath.Join(repoRoot(t), "machines.toml"), agents.Names())
	if err != nil {
		t.Fatal(err)
	}
	return m
}

func TestRealMachinesTomlLoads(t *testing.T) {
	m := loadRealMachines(t)
	for _, name := range []string{"mac-main", "laptop", "remote-server"} {
		if _, ok := m.Machines[name]; !ok {
			t.Fatalf("machines.toml 缺 %s", name)
		}
	}
}

func TestMacMainHasAllSevenAgents(t *testing.T) {
	m := loadRealMachines(t)
	mac, err := m.GetMachine("mac-main")
	if err != nil {
		t.Fatal(err)
	}
	expected := []string{"ClaudeCode", "ZCode", "QwenWorkCN", "TeleAgent", "Hermes", "Codex", "kimi-code"}
	if len(mac.Agents) != len(expected) {
		t.Fatalf("mac-main agent 数: %d", len(mac.Agents))
	}
	for _, a := range expected {
		if !mac.HasAgent(a) {
			t.Fatalf("mac-main 缺 agent %s", a)
		}
	}
}

func TestGetSkillsDirAbsolutePath(t *testing.T) {
	m := loadRealMachines(t)
	p := m.GetSkillsDir("mac-main", "QwenWorkCN")
	if p != "/Users/ss/.qwenworkcn/skills" {
		t.Fatalf("skills_dir: %q", p)
	}
	if !filepath.IsAbs(p) {
		t.Fatal("应为绝对路径")
	}
}

func TestUnconfiguredAgentReturnsNone(t *testing.T) {
	// 没配 = 空(sync 时跳过, 不报错)。
	m := loadRealMachines(t)
	if m.GetSkillsDir("laptop", "QwenWorkCN") != "" {
		t.Fatal("laptop 没配 QwenWorkCN 应返回空")
	}
	if m.GetSkillsDir("remote-server", "kimi-code") != "" {
		t.Fatal("remote-server 没配 kimi-code 应返回空")
	}
}

func TestUnknownMachineRaisesWithHint(t *testing.T) {
	m := loadRealMachines(t)
	_, err := m.GetMachine("no-such-machine")
	if err == nil || !strings.Contains(err.Error(), "mac-main") {
		t.Fatalf("未知机器应报错并含可用列表, got %v", err)
	}
}

func TestUnknownAgentNameRejected(t *testing.T) {
	// machines.toml 配了 agents.toml 没有的 agent 名 → 拼写错早暴露。
	agents, err := config.LoadAgents(filepath.Join(repoRoot(t), "agents.toml"))
	if err != nil {
		t.Fatal(err)
	}
	dir := t.TempDir()
	bad := filepath.Join(dir, "machines.toml")
	content := "[machines.m]\ndisplay_name = \"m\"\n" +
		"[machines.m.agents.ClaudeCodee]\nskills_dir = \"/x\"\n" // 拼错: 多个 e
	if err := os.WriteFile(bad, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	_, err = config.LoadMachines(bad, agents.Names())
	if err == nil || !strings.Contains(err.Error(), "未知 agent") {
		t.Fatalf("应报未知 agent, got %v", err)
	}
}

func TestRelativeOrTildePathRejected(t *testing.T) {
	// skills_dir 必须以 / 开头(手填完整路径, ~ 不支持)。
	agents, err := config.LoadAgents(filepath.Join(repoRoot(t), "agents.toml"))
	if err != nil {
		t.Fatal(err)
	}
	for _, badDir := range []string{"~/.claude/skills", "relative/skills"} {
		dir := t.TempDir()
		bad := filepath.Join(dir, "machines.toml")
		content := "[machines.m]\n[machines.m.agents.ClaudeCode]\nskills_dir = \"" + badDir + "\"\n"
		if err := os.WriteFile(bad, []byte(content), 0o644); err != nil {
			t.Fatal(err)
		}
		_, err := config.LoadMachines(bad, agents.Names())
		if err == nil || !strings.Contains(err.Error(), "绝对路径") {
			t.Fatalf("badDir=%q 应报绝对路径错, got %v", badDir, err)
		}
	}
}

func TestMachinesWithAgent(t *testing.T) {
	m := loadRealMachines(t)
	macs := m.MachinesWithAgent("ClaudeCode")
	found := map[string]bool{}
	for _, n := range macs {
		found[n] = true
	}
	if !found["mac-main"] || !found["laptop"] || !found["remote-server"] {
		t.Fatalf("ClaudeCode machines: %v", macs)
	}
	qw := m.MachinesWithAgent("QwenWorkCN")
	if len(qw) != 1 || qw[0] != "mac-main" {
		t.Fatalf("QwenWorkCN machines: %v", qw)
	}
}

func TestMacMainPathsExistOnThisMachine(t *testing.T) {
	// 本机(Mac 主力)实测: 7 个手填路径无 error(配置与真实环境一致)。
	// kimi-code 允许 warning: ~/.kimi-code/skills 是惰性目录。
	m := loadRealMachines(t)
	errs, warns := m.CheckPathsExist("mac-main")
	if len(errs) != 0 {
		t.Fatalf("mac-main 路径配置与实际环境不符: %v", errs)
	}
	for _, w := range warns {
		if !strings.Contains(w, "kimi-code") {
			t.Fatalf("意外 warning: %v", warns)
		}
	}
}

// --- render → load 往返(移植 test_scan.py 的回写部分) ---

func TestRenderLoadRoundtrip(t *testing.T) {
	dir := t.TempDir()
	home := filepath.Join(dir, "home")
	if err := os.MkdirAll(home, 0o755); err != nil {
		t.Fatal(err)
	}
	m := config.NewMachinesConfig()
	m.SetSkillsDir("mac-main", "ClaudeCode", filepath.Join(home, ".claude", "skills"))
	m.SetSkillsDir("mac-main", "kimi-code", filepath.Join(home, ".kimi-code", "skills"))
	mc := m.Machines["mac-main"]
	mc.DisplayName = "Mac 主力机"
	m.Machines["mac-main"] = mc

	out := filepath.Join(dir, "machines.toml")
	if err := m.Save(out); err != nil {
		t.Fatal(err)
	}
	// 再 load 回对象, 值不丢
	m2, err := config.LoadMachines(out, []string{"ClaudeCode", "kimi-code"})
	if err != nil {
		t.Fatal(err)
	}
	if m2.GetSkillsDir("mac-main", "ClaudeCode") != filepath.Join(home, ".claude", "skills") {
		t.Fatalf("ClaudeCode skills_dir 往返丢失")
	}
	if m2.GetSkillsDir("mac-main", "kimi-code") != filepath.Join(home, ".kimi-code", "skills") {
		t.Fatalf("kimi-code skills_dir 往返丢失")
	}
	if m2.Machines["mac-main"].DisplayName != "Mac 主力机" {
		t.Fatalf("display_name 往返丢失: %q", m2.Machines["mac-main"].DisplayName)
	}
	// agents 声明序保序
	if m2.Machines["mac-main"].AgentOrder[0] != "ClaudeCode" {
		t.Fatalf("agent 序应保文档序: %v", m2.Machines["mac-main"].AgentOrder)
	}
}

func TestSaveAtomicNoTmp(t *testing.T) {
	dir := t.TempDir()
	m := config.NewMachinesConfig()
	m.SetSkillsDir("m", "ClaudeCode", "/x")
	if err := m.Save(filepath.Join(dir, "machines.toml")); err != nil {
		t.Fatal(err)
	}
	items, _ := os.ReadDir(dir)
	for _, e := range items {
		if strings.HasSuffix(e.Name(), ".tmp") {
			t.Fatalf("原子写不应留 tmp: %s", e.Name())
		}
	}
}