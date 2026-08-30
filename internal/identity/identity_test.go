// Identity(本机身份绑定)测试(移植 tests/test_identity.py 非 CLI 的 8 条)。
// CLI `use` 绑定两条随 M3 CLI 移植。
package identity_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/ite-rate/skillbank/internal/config"
	"github.com/ite-rate/skillbank/internal/identity"
)

func mkMachines(names ...string) *config.MachinesConfig {
	m := config.NewMachinesConfig()
	for _, name := range names {
		m.SetSkillsDir(name, "ClaudeCode", "/tmp/nowhere-"+name+"/skills")
	}
	return m
}

// --- binding 读写回环 ---

func TestBindingRoundtrip(t *testing.T) {
	dir := t.TempDir()
	p, err := identity.WriteBinding(dir, "laptop")
	if err != nil {
		t.Fatal(err)
	}
	if p != identity.BindingPath(dir) {
		t.Fatalf("路径: %s", p)
	}
	if filepath.Base(p) != identity.BindingFilename {
		t.Fatalf("文件名: %s", filepath.Base(p))
	}
	raw, _ := os.ReadFile(p)
	if string(raw) != "laptop\n" {
		t.Fatalf("内容: %q", raw)
	}
	if identity.ReadBinding(dir) != "laptop" {
		t.Fatal("读回环失败")
	}
}

func TestBindingOverwriteAndStrip(t *testing.T) {
	dir := t.TempDir()
	if _, err := identity.WriteBinding(dir, "m1"); err != nil {
		t.Fatal(err)
	}
	if _, err := identity.WriteBinding(dir, "  m2  "); err != nil {
		t.Fatal(err)
	}
	if identity.ReadBinding(dir) != "m2" {
		t.Fatalf("应 strip: %q", identity.ReadBinding(dir))
	}
}

func TestBindingMissingOrEmpty(t *testing.T) {
	dir := t.TempDir()
	if identity.ReadBinding(dir) != "" {
		t.Fatal("缺文件应为未绑定")
	}
	if err := os.WriteFile(identity.BindingPath(dir), []byte("\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if identity.ReadBinding(dir) != "" {
		t.Fatal("空文件应为未绑定")
	}
}

// --- resolve_machine ---

func TestResolveExplicitWinsWithoutBinding(t *testing.T) {
	// 未绑定但显式传 machine 的命令可用(旧行为保留)。
	dir := t.TempDir()
	got, err := identity.ResolveMachine(dir, mkMachines("m1", "m2"), "m2")
	if err != nil || got != "m2" {
		t.Fatalf("got %q, err %v", got, err)
	}
}

func TestResolveExplicitUnknownMachineErrors(t *testing.T) {
	dir := t.TempDir()
	_, err := identity.ResolveMachine(dir, mkMachines("m1"), "ghost")
	if err == nil || !strings.Contains(err.Error(), "未知机器") {
		t.Fatalf("got %v", err)
	}
}

func TestResolveUsesBinding(t *testing.T) {
	dir := t.TempDir()
	if _, err := identity.WriteBinding(dir, "m1"); err != nil {
		t.Fatal(err)
	}
	got, err := identity.ResolveMachine(dir, mkMachines("m1", "m2"), "")
	if err != nil || got != "m1" {
		t.Fatalf("got %q, err %v", got, err)
	}
}

func TestResolveUnboundGivesGuidance(t *testing.T) {
	dir := t.TempDir()
	_, err := identity.ResolveMachine(dir, mkMachines("m1", "m2"), "")
	if err == nil || !strings.Contains(err.Error(), "skillbank use") {
		t.Fatalf("应给 use 指引, got %v", err)
	}
}

func TestResolveStaleBindingErrors(t *testing.T) {
	dir := t.TempDir()
	if _, err := identity.WriteBinding(dir, "gone"); err != nil {
		t.Fatal(err)
	}
	_, err := identity.ResolveMachine(dir, mkMachines("m1"), "")
	if err == nil || !strings.Contains(err.Error(), "不在 machines.toml") {
		t.Fatalf("应报过期绑定, got %v", err)
	}
}