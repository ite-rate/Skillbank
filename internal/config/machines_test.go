// machines.toml 加载器测试(移植 tests/test_machines.py 9 条, 语义等价)。
//
// 资产与配置迁到中心仓后, 工具仓不再自带 agents.toml/machines.toml —
// 全部测试走 fixture(影子一份原 mac-main 的三机清单形态)。
package config_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/ite-rate/skillbank/internal/config"
)

// 7 agent 的最小合法 agents.toml(只作名字表用)。
const agentsTomlFixture = `
[agents.ClaudeCode]
install_dir = "~/.claude/skills"
[agents.ZCode]
install_dir = "~/.zcode/skills"
[agents.QwenWorkCN]
install_dir = "~/.qwenworkcn/skills"
[agents.TeleAgent]
install_dir = "~/.config/TeleAgent/skills"
[agents.Hermes]
install_dir = "~/.hermes/skills"
[agents.Codex]
install_dir = "~/.codex/skills"
[agents.kimi-code]
install_dir = "~/.kimi-code/skills"
`

// 三机影子清单: mac-main 7 agent 全配(与原真机同形), laptop/remote-server 只配 ClaudeCode。
const machinesTomlFixture = `
[machines.mac-main]
display_name = "mac-main"
[machines.mac-main.agents.ClaudeCode]
skills_dir = "/Users/ss/.claude/skills"
[machines.mac-main.agents.ZCode]
skills_dir = "/Users/ss/.zcode/skills"
[machines.mac-main.agents.QwenWorkCN]
skills_dir = "/Users/ss/.qwenworkcn/skills"
[machines.mac-main.agents.TeleAgent]
skills_dir = "/Users/ss/.config/TeleAgent/skills"
[machines.mac-main.agents.Hermes]
skills_dir = "/Users/ss/.hermes/skills"
[machines.mac-main.agents.Codex]
skills_dir = "/Users/ss/.codex/skills"
[machines.mac-main.agents.kimi-code]
skills_dir = "/Users/ss/.kimi-code/skills"

[machines.laptop]
display_name = "laptop"
[machines.laptop.agents.ClaudeCode]
skills_dir = "/home/laptop/.claude/skills"

[machines.remote-server]
display_name = "remote-server"
[machines.remote-server.agents.ClaudeCode]
skills_dir = "/root/.claude/skills"
`

// fixtureDir 写出 shadow agents.toml + machines.toml 并返回目录。
func fixtureDir(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "agents.toml"), []byte(agentsTomlFixture), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "machines.toml"), []byte(machinesTomlFixture), 0o644); err != nil {
		t.Fatal(err)
	}
	return dir
}

// fixtureAgents 返回 7 agent 名单。
func fixtureAgents(t *testing.T) []string {
	t.Helper()
	agents, err := config.LoadAgents(filepath.Join(fixtureDir(t), "agents.toml"))
	if err != nil {
		t.Fatal(err)
	}
	return agents.Names()
}

// loadFixtureMachines — 影子三机清单加载。
func loadFixtureMachines(t *testing.T) *config.MachinesConfig {
	t.Helper()
	dir := fixtureDir(t)
	m, err := config.LoadMachines(filepath.Join(dir, "machines.toml"), fixtureAgents(t))
	if err != nil {
		t.Fatal(err)
	}
	return m
}

func TestMachinesTomlLoads(t *testing.T) {
	m := loadFixtureMachines(t)
	for _, name := range []string{"mac-main", "laptop", "remote-server"} {
		if _, ok := m.Machines[name]; !ok {
			t.Fatalf("machines.toml 缺 %s", name)
		}
	}
}

func TestMacMainHasAllSevenAgents(t *testing.T) {
	m := loadFixtureMachines(t)
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
	m := loadFixtureMachines(t)
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
	m := loadFixtureMachines(t)
	if m.GetSkillsDir("laptop", "QwenWorkCN") != "" {
		t.Fatal("laptop 没配 QwenWorkCN 应返回空")
	}
	if m.GetSkillsDir("remote-server", "kimi-code") != "" {
		t.Fatal("remote-server 没配 kimi-code 应返回空")
	}
}

func TestUnknownMachineRaisesWithHint(t *testing.T) {
	m := loadFixtureMachines(t)
	_, err := m.GetMachine("no-such-machine")
	if err == nil || !strings.Contains(err.Error(), "mac-main") {
		t.Fatalf("未知机器应报错并含可用列表, got %v", err)
	}
}

func TestUnknownAgentNameRejected(t *testing.T) {
	// machines.toml 配了 agents.toml 没有的 agent 名 → 拼写错早暴露。
	agents, err := config.LoadAgents(filepath.Join(fixtureDir(t), "agents.toml"))
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
	agents, err := config.LoadAgents(filepath.Join(fixtureDir(t), "agents.toml"))
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
	m := loadFixtureMachines(t)
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

func TestCheckPathsExistErrsAndWarns(t *testing.T) {
	// 路径检查语义: 盘上存在 = ok;父目录存在(从未部署) = warning;
	// 父目录也没有(Agent 没装/填错) = error。
	home := t.TempDir()
	dir := t.TempDir()
	// 6 个 agent 的 skills 目录真实建出来(父目录随 MumkdirAll 一起存在)
	for _, a := range []string{"claude", "zcode", "qwenworkcn", "teleagent", "hermes", "codex"} {
		if err := os.MkdirAll(filepath.Join(home, "."+a, "skills"), 0o755); err != nil {
			t.Fatal(err)
		}
	}
	content := "[machines.mac-main]\ndisplay_name = \"mac-main\"\n" +
		"[machines.mac-main.agents.ClaudeCode]\nskills_dir = \"" + filepath.Join(home, ".claude/skills") + "\"\n" +
		"[machines.mac-main.agents.QwenWorkCN]\nskills_dir = \"" + filepath.Join(home, ".qwenworkcn/skills") + "\"\n" +
		"[machines.mac-main.agents.kimi-code]\nskills_dir = \"" + filepath.Join(home, ".kimi-code/skills") + "\"\n" +
		"[machines.mac-main.agents.Codex]\nskills_dir = \"" + filepath.Join(home, ".codex-nonexist", "skills") + "\"\n"
	bad := filepath.Join(dir, "machines.toml")
	if err := os.WriteFile(bad, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	m, err := config.LoadMachines(bad, fixtureAgents(t))
	if err != nil {
		t.Fatal(err)
	}
	errs, warns := m.CheckPathsExist("mac-main")
	// kimi: 目录缺但 ~/.kimi-code 也缺 → 需要区分 — 这里父目录一并缺 → err;
	// 已存在 2 个 → 干净。
	if len(errs) != 2 {
		t.Fatalf("kimi(父目录缺)+ codex(路径错) 应各 1 err: %v", errs)
	}
	if len(warns) != 0 {
		t.Fatalf("无 warning 预期: %v", warns)
	}
	// 补齐 ~/.kimi-code 父目录 → kimi 变 warning, codex 仍 err
	if err := os.MkdirAll(filepath.Join(home, ".kimi-code"), 0o755); err != nil {
		t.Fatal(err)
	}
	errs, warns = m.CheckPathsExist("mac-main")
	if len(errs) != 1 || !strings.Contains(strings.Join(errs, ";"), "Codex") {
		t.Fatalf("剩 Codex 1 err: %v", errs)
	}
	if len(warns) != 1 || !strings.Contains(warns[0], "kimi-code") {
		t.Fatalf("kimi 应转 warning: %v", warns)
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