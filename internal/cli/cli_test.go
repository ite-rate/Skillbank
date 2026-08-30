// CLI 测试 — App 级冒烟(移植 tests/test_identity.py 的 2 条 CLI 测试 +
// sync/set-level/rm 的走线冒烟)。
//
// App 可注入 RepoRoot/TTY/In, 假 repo + 捕获 stdout, 不动真 repo。
package cli_test

import (
	"bufio"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/ite-rate/skillbank/internal/cli"
	"github.com/ite-rate/skillbank/internal/emit"
	"github.com/ite-rate/skillbank/internal/identity"
	sbir "github.com/ite-rate/skillbank/internal/ir"
)

func fakeRepo(t *testing.T) string {
	t.Helper()
	repo := filepath.Join(t.TempDir(), "repo")
	if err := os.MkdirAll(filepath.Join(repo, "skills"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(repo, "agents.toml"),
		[]byte("[agents.ClaudeCode]\ninstall_dir = \"~/.claude/skills\"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(repo, "machines.toml"),
		[]byte("[machines.m1]\ndisplay_name = \"m1\"\n\n"+
			"[machines.m1.agents.ClaudeCode]\nskills_dir = \"/tmp/nowhere-m1/skills\"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	return repo
}

// capture — 捕获 stdout 执行 fn, 返回输出。
func capture(t *testing.T, fn func()) string {
	t.Helper()
	old := os.Stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	os.Stdout = w
	done := make(chan string)
	go func() {
		var sb strings.Builder
		_, _ = io.Copy(&sb, r)
		done <- sb.String()
	}()
	fn()
	w.Close()
	os.Stdout = old
	return <-done
}

func run(a *cli.App, args ...string) int {
	return a.Run(args)
}

// --- use 绑定 + list 用绑定默认值(移植 test_cli_use_and_list_use_binding) ---

func TestCliUseAndListUseBinding(t *testing.T) {
	repo := fakeRepo(t)
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}

	// 未绑定: list 拒绝执行并给指引
	var out string
	rc := 0
	out = capture(t, func() { rc = run(a, "list") })
	if rc != 2 {
		t.Fatalf("未绑定应 exit 2, got %d", rc)
	}
	if !strings.Contains(out, "skillbank use") {
		t.Fatalf("应给 use 指引:\n%s", out)
	}

	// use 绑定 → 后续命令默认走 m1;list 空 manifest 但不再报错
	if out2 := capture(t, func() { rc = run(a, "use", "m1") }); rc != 0 {
		t.Fatalf("use m1 rc=%d\n%s", rc, out2)
	}
	raw, err := os.ReadFile(identity.BindingPath(repo))
	if err != nil || string(raw) != "m1\n" {
		t.Fatalf("绑定文件内容: %q %v", raw, err)
	}
	out = capture(t, func() { rc = run(a, "list") })
	if rc != 0 {
		t.Fatalf("list rc=%d\n%s", rc, out)
	}
	if !strings.Contains(out, "[list] machine=m1") {
		t.Fatalf("list 应用绑定:\n%s", out)
	}

	// use 无参数 = 查看当前绑定
	out = capture(t, func() { rc = run(a, "use") })
	if rc != 0 || !strings.Contains(out, "当前绑定") {
		t.Fatalf("use 查看: rc=%d\n%s", rc, out)
	}
}

// --- use 未知机器(移植 test_cli_use_unknown_machine) ---

func TestCliUseUnknownMachine(t *testing.T) {
	repo := fakeRepo(t)
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}
	var rc int
	out := capture(t, func() { rc = run(a, "use", "ghost") })
	if rc != 2 {
		t.Fatalf("rc: %d", rc)
	}
	if !strings.Contains(out, "未知机器") {
		t.Fatalf("应含未知机器提示:\n%s", out)
	}
}

// --- 走线冒烟(Python 侧无对应, Go 补的 App 级冒烟) ---

func TestCliSyncDryRunNoWrite(t *testing.T) {
	repo := fakeRepo(t)
	tmp := t.TempDir()
	cc := filepath.Join(tmp, "claude", "skills")
	if err := os.MkdirAll(cc, 0o755); err != nil {
		t.Fatal(err)
	}
	// 机器 m1 的 ClaudeCode 指向 tmp(父目录存在 = 已装)
	if err := os.WriteFile(filepath.Join(repo, "machines.toml"),
		[]byte("[machines.m1]\ndisplay_name = \"m1\"\n\n"+
			"[machines.m1.agents.ClaudeCode]\nskills_dir = \""+cc+"\"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	// canonical demo
	d := filepath.Join(repo, "skills", "demo")
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	in := &sbir.SkillIR{Name: "demo", Description: "d", Body: []byte("## b\n"),
		Level: sbir.Auto, Requires: []string{}}
	if err := emit.EmitCanonical(in, filepath.Join(d, "SKILL.md")); err != nil {
		t.Fatal(err)
	}
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}
	if _, err := identity.WriteBinding(repo, "m1"); err != nil {
		t.Fatal(err)
	}

	var rc int
	out := capture(t, func() { rc = run(a, "sync", "--dry-run") })
	if rc != 0 {
		t.Fatalf("rc=%d\n%s", rc, out)
	}
	if !strings.Contains(out, "deploy") || !strings.Contains(out, "demo") {
		t.Fatalf("计划应含 demo deploy:\n%s", out)
	}
	if !strings.Contains(out, "dry-run 结束") {
		t.Fatalf("应提示 dry-run:\n%s", out)
	}
	// 不落盘
	if _, err := os.Stat(filepath.Join(cc, "demo")); !os.IsNotExist(err) {
		t.Fatal("dry-run 不应写盘")
	}
	if _, err := os.Stat(filepath.Join(repo, "manifests")); !os.IsNotExist(err) {
		t.Fatal("dry-run 不应写 manifest")
	}

	// 真 sync --yes
	out = capture(t, func() { rc = run(a, "sync", "--yes") })
	if rc != 0 {
		t.Fatalf("rc=%d\n%s", rc, out)
	}
	if _, err := os.Stat(filepath.Join(cc, "demo", "SKILL.md")); err != nil {
		t.Fatal("sync 应部署")
	}
	// 第二次 sync 全 keep
	out = capture(t, func() { rc = run(a, "sync", "--yes") })
	if rc != 0 || !strings.Contains(out, "keep") {
		t.Fatalf("第二次应全 keep:\n%s", out)
	}
}

func TestCliSetLevelRoundtrip(t *testing.T) {
	repo := fakeRepo(t)
	d := filepath.Join(repo, "skills", "demo")
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	in := &sbir.SkillIR{Name: "demo", Description: "d", Body: []byte("## b\n"),
		Level: sbir.Auto, Requires: []string{}}
	skillMD := filepath.Join(d, "SKILL.md")
	if err := emit.EmitCanonical(in, skillMD); err != nil {
		t.Fatal(err)
	}
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}

	var rc int
	out := capture(t, func() { rc = run(a, "set-level", "demo", "manual") })
	if rc != 0 || !strings.Contains(out, "auto → manual") {
		t.Fatalf("rc=%d\n%s", rc, out)
	}
	// body 零损耗 + level 已变
	raw, _ := os.ReadFile(skillMD)
	if !strings.HasSuffix(string(raw), "## b\n") {
		t.Fatalf("body 应零损耗: %q", raw)
	}
	if !strings.Contains(string(raw), "level: manual") {
		t.Fatalf("level 应已写: %s", raw)
	}
	// 再 set 同级 → 无变化
	out = capture(t, func() { rc = run(a, "set-level", "demo", "manual") })
	if rc != 0 || !strings.Contains(out, "无变化") {
		t.Fatalf("rc=%d\n%s", rc, out)
	}
}

func TestCliRmFlow(t *testing.T) {
	repo := fakeRepo(t)
	tmp := t.TempDir()
	cc := filepath.Join(tmp, "claude", "skills")
	if err := os.MkdirAll(cc, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(repo, "machines.toml"),
		[]byte("[machines.m1]\ndisplay_name = \"m1\"\n\n"+
			"[machines.m1.agents.ClaudeCode]\nskills_dir = \""+cc+"\"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	d := filepath.Join(repo, "skills", "demo")
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	in := &sbir.SkillIR{Name: "demo", Description: "d", Body: []byte("## b\n"),
		Level: sbir.Auto, Requires: []string{}}
	if err := emit.EmitCanonical(in, filepath.Join(d, "SKILL.md")); err != nil {
		t.Fatal(err)
	}
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}
	if _, err := identity.WriteBinding(repo, "m1"); err != nil {
		t.Fatal(err)
	}
	var rc int
	capture(t, func() { rc = run(a, "sync", "--yes") })
	if rc != 0 {
		t.Fatalf("sync rc=%d", rc)
	}

	// rm 无该 skill 记录 → 无动作
	out := capture(t, func() { rc = run(a, "rm", "ghost") })
	if rc != 0 || !strings.Contains(out, "无 manifest 部署记录") {
		t.Fatalf("rc=%d\n%s", rc, out)
	}
	// rm --dry-run 不动盘
	out = capture(t, func() { rc = run(a, "rm", "demo", "--dry-run") })
	if rc != 0 || !strings.Contains(out, "[dry-run]") {
		t.Fatalf("rc=%d\n%s", rc, out)
	}
	if _, err := os.Stat(filepath.Join(cc, "demo")); err != nil {
		t.Fatal("dry-run 不应删副本")
	}
	// rm 真删: 副本清, canonical 保留
	out = capture(t, func() { rc = run(a, "rm", "demo") })
	if rc != 0 || !strings.Contains(out, "canonical 保留") {
		t.Fatalf("rc=%d\n%s", rc, out)
	}
	if _, err := os.Stat(filepath.Join(cc, "demo")); !os.IsNotExist(err) {
		t.Fatal("副本应被清")
	}
	if _, err := os.Stat(filepath.Join(d, "SKILL.md")); err != nil {
		t.Fatal("canonical 应保留")
	}
}

// --- scan 新别名注册(回归: 零探测到 agent 时别名也必须落盘, 否则绑定与
// machines.toml 不一致, 后续 sync 拒绝执行) ---

func TestCliScanRegistersNewAliasEvenWithNoAgents(t *testing.T) {
	repo := fakeRepo(t)
	// HOME 隔离: 探测不到任何 agent 目录
	home := t.TempDir()
	t.Setenv("HOME", home)
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}

	var rc int
	out := capture(t, func() { rc = run(a, "scan", "--machine", "fresh-laptop", "--yes") })
	if rc != 0 {
		t.Fatalf("rc=%d\n%s", rc, out)
	}
	// machines.toml 应含新别名(不因零变更跳过保存)
	raw, err := os.ReadFile(filepath.Join(repo, "machines.toml"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(raw), "fresh-laptop") {
		t.Fatalf("新别名应写进 machines.toml:\n%s", raw)
	}
	// 绑定同步写
	bound, err := os.ReadFile(identity.BindingPath(repo))
	if err != nil || strings.TrimSpace(string(bound)) != "fresh-laptop" {
		t.Fatalf("绑定: %q %v", bound, err)
	}
	// 已注册别名 + 已绑定 → 后续命令不再拒绝
	out = capture(t, func() { rc = run(a, "use") })
	if rc != 0 || !strings.Contains(out, "fresh-laptop") {
		t.Fatalf("use 应显示绑定: rc=%d\n%s", rc, out)
	}
}