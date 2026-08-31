// CLI 测试 — App 级冒烟(移植 tests/test_identity.py 的 2 条 CLI 测试 +
// sync/set-level/rm 的走线冒烟)。
//
// App 可注入 RepoRoot/TTY/In, 假 repo + 捕获 stdout, 不动真 repo。
package cli_test

import (
	"bufio"
	"io"
	"os"
	"os/exec"
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

// --- install 一条龙(v2.1) ---

// mkGitSkillRepo — 一个含单 skill 的本地 git 仓, 返回 file:// URL。
func mkGitSkillRepo(t *testing.T, base string) string {
	t.Helper()
	src := filepath.Join(base, "skill-src")
	if err := os.MkdirAll(src, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(src, "SKILL.md"),
		[]byte("---\nname: git-skill\ndescription: From git via install\n---\n## body\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	git := func(args ...string) {
		t.Helper()
		out, err := exec.Command("git", append([]string{"-C", src}, args...)...).CombinedOutput()
		if err != nil {
			t.Fatalf("git %v: %v\n%s", args, err, out)
		}
	}
	git("init", "-q", "-b", "main")
	git("config", "user.email", "t@t")
	git("config", "user.name", "t")
	git("add", "-A")
	git("commit", "-qm", "init")
	return "file://" + src
}

func TestCliInstallImportsAndSyncsOnlyNewSkill(t *testing.T) {
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
	// 预置一个既有 canonical skill(不应被 install 顺带部署)
	existing := filepath.Join(repo, "skills", "already-there")
	if err := os.MkdirAll(existing, 0o755); err != nil {
		t.Fatal(err)
	}
	irIn := &sbir.SkillIR{Name: "already-there", Description: "pre-existing",
		Body: []byte("## pre\n"), Level: sbir.Auto, Requires: []string{}}
	if err := emit.EmitCanonical(irIn, filepath.Join(existing, "SKILL.md")); err != nil {
		t.Fatal(err)
	}

	url := mkGitSkillRepo(t, tmp)
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}

	rc := run(a, "install", url, "--machine", "m1", "--yes")
	if rc != 0 {
		t.Fatalf("install rc=%d", rc)
	}
	// canonical 已带 source
	raw, err := os.ReadFile(filepath.Join(repo, "skills", "git-skill", "SKILL.md"))
	if err != nil {
		t.Fatalf("导入应完成: %v", err)
	}
	if !strings.Contains(string(raw), "source: file://") {
		t.Fatalf("canonical 应含 source:\n%s", raw)
	}
	// 只有新 skill 被部署
	if _, err := os.Stat(filepath.Join(cc, "git-skill", "SKILL.md")); err != nil {
		t.Fatal("新 skill 应被部署到 agent 目录")
	}
	if _, err := os.Stat(filepath.Join(cc, "already-there")); err == nil {
		t.Fatal("既有 canonical 不应被 install 顺带部署")
	}
}

func TestCliInstallRejectsLocalPath(t *testing.T) {
	repo := fakeRepo(t)
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}
	var rc int
	_ = capture(t, func() { rc = run(a, "install", "/some/local/dir") }) // 报错走 stderr
	if rc != 2 {
		t.Fatalf("本地路径应 exit 2, got %d", rc)
	}
}

func TestCliInstallMachineUnresolvedStillImports(t *testing.T) {
	// machines.toml 未配置 → 导入照做, 提示先 scan, exit 0
	repo := fakeRepo(t)
	tmp := t.TempDir()
	url := mkGitSkillRepo(t, tmp)
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}

	var rc int
	out := capture(t, func() { rc = run(a, "install", url, "--yes") })
	if rc != 0 {
		t.Fatalf("导入成功但机器未解析应 exit 0, got %d:\n%s", rc, out)
	}
	if _, err := os.Stat(filepath.Join(repo, "skills", "git-skill", "SKILL.md")); err != nil {
		t.Fatalf("导入应已完成: %v", err)
	}
	if !strings.Contains(out, "未同步") {
		t.Fatalf("应提示未同步原因:\n%s", out)
	}
}

// --- pull 一键日常动线(v2.1) ---

// mkGitCenterRepo — fakeRepo 基础上 git init + 全部提交(中心仓 git 形态)。
func mkGitCenterRepo(t *testing.T, dir string) {
	t.Helper()
	git := func(args ...string) {
		t.Helper()
		out, err := exec.Command("git", append([]string{"-C", dir}, args...)...).CombinedOutput()
		if err != nil {
			t.Fatalf("git %v: %v\n%s", args, err, out)
		}
	}
	git("init", "-q", "-b", "main")
	git("config", "user.email", "t@t")
	git("config", "user.name", "t")
	git("add", "-A")
	git("commit", "-qm", "init")
}

// mkGitCenterRepoCommits — 后续改动(改 machines.toml 等)再提交一次。
func mkGitCenterRepoCommits(t *testing.T, dir string) {
	t.Helper()
	git := []string{"-C", dir}
	for _, args := range [][]string{{"add", "-A"}, {"commit", "-qm", "update"}} {
		if out, err := exec.Command("git", append(git, args...)...).CombinedOutput(); err != nil {
			if !strings.Contains(strings.ToLower(string(out)), "nothing to commit") {
				t.Fatalf("git %v: %v\n%s", args, err, out)
			}
		}
	}
}

func TestCliPullDryRunNoRemoteSkipsPullGracefully(t *testing.T) {
	repo := fakeRepo(t)
	mkGitCenterRepo(t, repo) // 无 remote: skillbank init 形态
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
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}
	if rc := run(a, "use", "m1"); rc != 0 {
		t.Fatalf("use rc=%d", rc)
	}
	d := filepath.Join(repo, "skills", "demo")
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := emit.EmitCanonical(&sbir.SkillIR{Name: "demo", Description: "d",
		Body: []byte("## b\n"), Level: sbir.Auto, Requires: []string{}},
		filepath.Join(d, "SKILL.md")); err != nil {
		t.Fatal(err)
	}

	var rc int
	out := capture(t, func() { rc = run(a, "pull", "--dry-run") })
	if rc != 0 {
		t.Fatalf("pull --dry-run rc=%d\n%s", rc, out)
	}
	if !strings.Contains(out, "跳过 pull") {
		t.Fatalf("无 remote 应跳过 pull:\n%s", out)
	}
	if _, err := os.Stat(filepath.Join(cc, "demo")); err == nil {
		t.Fatal("dry-run 不应部署")
	}
}

func TestCliPullAbortsOnDirtyTree(t *testing.T) {
	repo := fakeRepo(t)
	mkGitCenterRepo(t, repo)
	if err := os.WriteFile(filepath.Join(repo, "dirty.md"), []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}
	src := filepath.Join(t.TempDir(), "origin")
	if out, err := exec.Command("git", "init", "-q", "--bare", "-b", "main", src).CombinedOutput(); err != nil {
		t.Fatalf("git init --bare: %v %s", err, out)
	}
	if out, err := exec.Command("git", "-C", repo, "remote", "add", "origin", src).
		CombinedOutput(); err != nil {
		t.Fatalf("git remote add: %v %s", err, out)
	}

	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}
	if rc := run(a, "use", "m1"); rc != 0 {
		t.Fatalf("use rc=%d", rc)
	}
	var rc int
	out := capture(t, func() { rc = run(a, "pull", "--yes") })
	if rc != 1 {
		t.Fatalf("脏工作区应 exit 1, got %d\n%s", rc, out)
	}
	if !strings.Contains(out, "未提交改动") {
		t.Fatalf("应说明中止原因:\n%s", out)
	}
}

func TestCliPullFastForward(t *testing.T) {
	// 双 clone: A 推新 skill → B pull 拉到并部署到本机 agent 目录。
	origin := filepath.Join(t.TempDir(), "origin")
	if out, err := exec.Command("git", "init", "-q", "--bare", "-b", "main", origin).CombinedOutput(); err != nil {
		t.Fatalf("git init --bare: %v %s", err, out)
	}
	repoB := fakeRepo(t)
	mkGitCenterRepo(t, repoB)
	if out, err := exec.Command("git", "-C", repoB, "remote", "add", "origin", origin).
		CombinedOutput(); err != nil {
		t.Fatalf("git remote add: %v %s", err, out)
	}
	if out, err := exec.Command("git", "-C", repoB, "push", "-q", "-u", origin, "main").
		CombinedOutput(); err != nil {
		t.Fatalf("git push -u: %v %s", err, out)
	}
	tmp := t.TempDir()
	ccB := filepath.Join(tmp, "claude", "skills")
	if err := os.MkdirAll(ccB, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(repoB, "machines.toml"),
		[]byte("[machines.m1]\ndisplay_name = \"m1\"\n\n"+
			"[machines.m1.agents.ClaudeCode]\nskills_dir = \""+ccB+"\"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	a := &cli.App{RepoRoot: repoB, In: bufio.NewReader(strings.NewReader(""))}
	if rc := run(a, "use", "m1"); rc != 0 {
		t.Fatalf("use rc=%d", rc)
	}
	// B 提交自己的 machines.toml 改动(否则 pull 被自己的脏树中止 —— 预期语义)
	// 并推上去; 不推的话 origin 与 B 就真分叉了(pull --ff-only 拒绝非祖先)
	mkGitCenterRepoCommits(t, repoB)
	if out, err := exec.Command("git", "-C", repoB, "push", "-q", "origin", "main").
		CombinedOutput(); err != nil {
		t.Fatalf("git push B: %v %s", err, out)
	}

	// A: clone origin → 加 skill → push
	repoA := filepath.Join(t.TempDir(), "repoA")
	if out, err := exec.Command("git", "clone", "-q", origin, repoA).CombinedOutput(); err != nil {
		t.Fatalf("git clone A: %v %s", err, out)
	}
	for _, f := range []string{"agents.toml", "machines.toml"} {
		b, err := os.ReadFile(filepath.Join(repoB, f))
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(repoA, f), b, 0o644); err != nil {
			t.Fatal(err)
		}
	}
	d := filepath.Join(repoA, "skills", "new-skill")
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(d, "SKILL.md"),
		[]byte("---\nname: new-skill\ndescription: Fresh from A\n---\n## body\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	gitA := func(args ...string) {
		t.Helper()
		out, err := exec.Command("git", append([]string{"-C", repoA}, args...)...).CombinedOutput()
		if err != nil {
			t.Fatalf("git(A) %v: %v\n%s", args, err, out)
		}
	}
	gitA("config", "user.email", "a@t")
	gitA("config", "user.name", "a")
	gitA("add", "-A")
	gitA("commit", "-qm", "add new-skill")
	if out, err := exec.Command("git", "-C", repoA, "push", "-q", origin, "main").
		CombinedOutput(); err != nil {
		t.Fatalf("git push A: %v %s", err, out)
	}

	rc := run(a, "pull", "--yes", "--no-doctor")
	if rc != 0 {
		t.Fatalf("pull rc=%d", rc)
	}
	if _, err := os.Stat(filepath.Join(repoB, "skills", "new-skill", "SKILL.md")); err != nil {
		t.Fatalf("pull 应拉到 new-skill: %v", err)
	}
	if _, err := os.Stat(filepath.Join(ccB, "new-skill", "SKILL.md")); err != nil {
		t.Fatal("pull --yes 应链式部署到 agent 目录")
	}
}

// --- 回归: -s/-a 别名曾只注册未绑定指针, `sync -s <名>` 直接 SIGSEGV(v2.0 起潜伏) ---

func TestCliSyncShortFlagAliasesNoPanic(t *testing.T) {
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
	for _, n := range []string{"demo", "other"} {
		d := filepath.Join(repo, "skills", n)
		if err := os.MkdirAll(d, 0o755); err != nil {
			t.Fatal(err)
		}
		if err := emit.EmitCanonical(&sbir.SkillIR{Name: n, Description: "d",
			Body: []byte("## b\n"), Level: sbir.Auto, Requires: []string{}},
			filepath.Join(d, "SKILL.md")); err != nil {
			t.Fatal(err)
		}
	}
	a := &cli.App{RepoRoot: repo, In: bufio.NewReader(strings.NewReader(""))}
	if rc := run(a, "use", "m1"); rc != 0 {
		t.Fatalf("use rc=%d", rc)
	}
	var rc int
	out := capture(t, func() { rc = run(a, "sync", "-s", "demo", "--dry-run", "--yes") })
	if rc != 0 {
		t.Fatalf("'-s demo' 应正常解析(回归: 曾 panic), rc=%d\n%s", rc, out)
	}
	if !strings.Contains(out, "demo") {
		t.Fatalf("计划应含 demo:\n%s", out)
	}
	if strings.Contains(out, "other") {
		t.Fatalf("-s demo 不应带出 other:\n%s", out)
	}
}
