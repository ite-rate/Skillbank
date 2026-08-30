// sync 引擎测试(移植 tests/test_sync.py 10 条, 语义等价)。
//
// 用假 repo(skills/ + manifests/) + 内存 MachinesConfig(指向 tmp 目录)跑:
// deploy/keep 真跳过/disable 清理/孤儿清理/Hermes 超限/ZCode cp/未装 skip。
package sync_test

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/ite-rate/skillbank/internal/bootstrap"
	"github.com/ite-rate/skillbank/internal/config"
	"github.com/ite-rate/skillbank/internal/emit"
	sbir "github.com/ite-rate/skillbank/internal/ir"
	"github.com/ite-rate/skillbank/internal/manifest"
	"github.com/ite-rate/skillbank/internal/sync"
)

func repoRoot(t *testing.T) string {
	t.Helper()
	// 工具仓不再自带 agents.toml — 影子 7 agent 配置写临时目录。
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "agents.toml"),
		[]byte(bootstrap.AgentsTomlTemplate), 0o644); err != nil {
		t.Fatal(err)
	}
	return dir
}

func writeCanonical(t *testing.T, repo, name string, body string,
	level string, resources map[string]string) string {
	t.Helper()
	if level == "" {
		level = "auto"
	}
	d := filepath.Join(repo, "skills", name)
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	in := &sbir.SkillIR{
		Name: name, Description: "a skill", Body: []byte(body),
		Level: sbir.Level(level), Requires: []string{},
	}
	if err := emit.EmitCanonical(in, filepath.Join(d, "SKILL.md")); err != nil {
		t.Fatal(err)
	}
	for rel, content := range resources {
		p := filepath.Join(d, filepath.FromSlash(rel))
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	return d
}

type fakeEnv struct {
	repo      string
	agentsCfg *config.AgentsConfig
	machines  *config.MachinesConfig
	manifest  *manifest.DeploymentsManifest
	tmp       string
}

func newFakeEnv(t *testing.T) *fakeEnv {
	tmp := t.TempDir()
	repo := filepath.Join(tmp, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	agentsCfg, err := config.LoadAgents(filepath.Join(repoRoot(t), "agents.toml"))
	if err != nil {
		t.Fatal(err)
	}
	machines := config.NewMachinesConfig()
	machines.SetSkillsDir("m1", "ClaudeCode", filepath.Join(tmp, "claude"))
	machines.SetSkillsDir("m1", "ZCode", filepath.Join(tmp, "zcode"))
	machines.SetSkillsDir("m1", "Hermes", filepath.Join(tmp, "hermes"))
	machines.SetSkillsDir("m2", "ClaudeCode", filepath.Join(tmp, "claude2"))
	return &fakeEnv{
		repo: repo, agentsCfg: agentsCfg, machines: machines,
		manifest: &manifest.DeploymentsManifest{
			Path: filepath.Join(repo, "manifests", "deployments.json")},
		tmp: tmp,
	}
}

func (e *fakeEnv) collect(t *testing.T, skillsFilter, agentsFilter []string, force bool) *sync.SyncContext {
	t.Helper()
	ctx, err := sync.Collect(e.repo, "m1", skillsFilter, agentsFilter,
		e.machines, e.agentsCfg, e.manifest, force)
	if err != nil {
		t.Fatal(err)
	}
	return ctx
}

func (e *fakeEnv) execute(t *testing.T, ctx *sync.SyncContext) int {
	t.Helper()
	return sync.Execute(e.repo, "m1", ctx, e.machines, e.agentsCfg, e.manifest)
}

func anyItem(plan []sync.PlanItem, pred func(sync.PlanItem) bool) bool {
	for _, it := range plan {
		if pred(it) {
			return true
		}
	}
	return false
}

// --- 测试 ---

func TestSyncDeploysAndBodyZeroLoss(t *testing.T) {
	e := newFakeEnv(t)
	body := "## Step\n\nline\r\nCRLF\n"
	writeCanonical(t, e.repo, "demo", body, "", map[string]string{"scripts/run.py": "print(1)\n"})

	ctx := e.collect(t, nil, nil, false)
	if !anyItem(ctx.Plan, func(i sync.PlanItem) bool {
		return i.Skill == "demo" && (i.Kind == "deploy" || i.Kind == "keep")
	}) {
		t.Fatalf("plan: %+v", ctx.Plan)
	}
	if rc := e.execute(t, ctx); rc != 0 {
		t.Fatalf("rc: %d", rc)
	}
	// ClaudeCode 落盘 + body 字节等值
	raw, err := os.ReadFile(filepath.Join(e.tmp, "claude", "demo", "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasSuffix(string(raw), body) {
		t.Fatalf("deployed body 必须与 canonical 字节等值: %q", raw)
	}
	// 资源结构保真
	rb, err := os.ReadFile(filepath.Join(e.tmp, "claude", "demo", "scripts", "run.py"))
	if err != nil || string(rb) != "print(1)\n" {
		t.Fatalf("scripts 镜像: %v %q", err, rb)
	}
	// manifest 记录
	recs := e.manifest.Find("demo", "m1", "ClaudeCode")
	if len(recs) != 1 || recs[0].Method != "cp" ||
		!strings.HasPrefix(recs[0].IrHash, "sha256:") {
		t.Fatalf("recs: %+v", recs)
	}
	// Hermes 也部署了(默认 category)
	if _, err := os.Stat(filepath.Join(e.tmp, "hermes", "imported", "demo", "SKILL.md")); err != nil {
		t.Fatal("Hermes imported/demo 应存在")
	}
}

func TestSyncKeepWhenHashSame(t *testing.T) {
	e := newFakeEnv(t)
	writeCanonical(t, e.repo, "demo", "## body\n", "", nil)
	e.execute(t, e.collect(t, nil, nil, false))

	ctx2 := e.collect(t, nil, nil, false)
	if !anyItem(ctx2.Plan, func(i sync.PlanItem) bool {
		return i.Kind == "keep" && i.Skill == "demo"
	}) {
		t.Fatalf("plan: %+v", ctx2.Plan)
	}
}

func TestSyncKeepDoesNotRewriteOrDirtyManifest(t *testing.T) {
	// keep 项真跳过:不重写 deployed 文件、不刷 manifest(deployed_at 不变)、不 save manifest。
	e := newFakeEnv(t)
	writeCanonical(t, e.repo, "demo", "## body\n", "", nil)
	e.execute(t, e.collect(t, nil, nil, false))

	deployed := filepath.Join(e.tmp, "claude", "demo", "SKILL.md")
	deployedMtime := mtime(t, deployed)
	manifestPath := e.manifest.Path
	if err := e.manifest.Save(""); err != nil {
		t.Fatal(err)
	} // 确保落盘, 固定基准 mtime
	manifestMtime := mtime(t, manifestPath)
	deployedAt := e.manifest.Find("demo", "m1", "ClaudeCode")[0].DeployedAt

	time.Sleep(20 * time.Millisecond)

	// 第二次 sync:body 未变 → keep
	ctx2 := e.collect(t, nil, nil, false)
	if !anyItem(ctx2.Plan, func(i sync.PlanItem) bool {
		return i.Kind == "keep" && i.Skill == "demo"
	}) {
		t.Fatal("应识别为 keep")
	}
	if hasPair(ctx2.DeployPairs, "demo", "ClaudeCode") {
		t.Fatal("keep 项不应进 deploy_pairs")
	}
	e.execute(t, ctx2)

	// deployed 文件 mtime 不变(未重写)
	if mtime(t, deployed) != deployedMtime {
		t.Fatal("keep 项不应重写 deployed 文件")
	}
	// manifest 文件 mtime 不变(未 save)
	if mtime(t, manifestPath) != manifestMtime {
		t.Fatal("keep 项不应 save manifest")
	}
	// deployed_at 不变(未 upsert 刷新)
	if got := e.manifest.Find("demo", "m1", "ClaudeCode")[0].DeployedAt; got != deployedAt {
		t.Fatalf("deployed_at 被刷新: %s → %s", deployedAt, got)
	}
}

func TestSyncKeepThenBodyChangeRedeploys(t *testing.T) {
	// keep 跳过后改 body, 第三次 sync 应重新 deploy 并刷新 hash。
	e := newFakeEnv(t)
	writeCanonical(t, e.repo, "demo", "## body v1\n", "", nil)
	e.execute(t, e.collect(t, nil, nil, false))

	ctx2 := e.collect(t, nil, nil, false)
	if hasPair(ctx2.DeployPairs, "demo", "ClaudeCode") {
		t.Fatal("body 未变不应重部署")
	}
	hash1 := e.manifest.Find("demo", "m1", "ClaudeCode")[0].IrHash

	// 第三次:body 变了 → 应重新 deploy
	writeCanonical(t, e.repo, "demo", "## body v2\n", "", nil)
	ctx3 := e.collect(t, nil, nil, false)
	if !hasPair(ctx3.DeployPairs, "demo", "ClaudeCode") {
		t.Fatal("body 变了应重新 deploy")
	}
	e.execute(t, ctx3)
	rec3 := e.manifest.Find("demo", "m1", "ClaudeCode")[0]
	if rec3.IrHash == hash1 {
		t.Fatal("重部署后 hash 应刷新")
	}
	raw, _ := os.ReadFile(filepath.Join(e.tmp, "claude", "demo", "SKILL.md"))
	if !strings.HasSuffix(string(raw), "## body v2\n") {
		t.Fatalf("deployed body: %q", raw)
	}
}

func TestSyncDisableCleansLocalAndPendsRemote(t *testing.T) {
	e := newFakeEnv(t)
	// 先部署到 m1
	writeCanonical(t, e.repo, "demo", "## body\n", "", nil)
	e.execute(t, e.collect(t, nil, nil, false))
	// 模拟 m2 也部署过(m2 有 ClaudeCode)
	m2Dir := filepath.Join(e.tmp, "claude2", "demo")
	if err := os.MkdirAll(m2Dir, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(m2Dir, "SKILL.md"), []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}
	e.manifest.Upsert(manifest.DeployRecord{
		Skill: "demo", Machine: "m2", Agent: "ClaudeCode",
		DeployPath: filepath.Join(m2Dir, "SKILL.md"), Method: "cp"})

	// canonical 改 disable
	writeCanonical(t, e.repo, "demo", "## body\n", "disable", nil)

	ctx := e.collect(t, nil, nil, false)
	if !anyItem(ctx.Plan, func(i sync.PlanItem) bool { return i.Kind == "delete" && i.Skill == "demo" }) ||
		!anyItem(ctx.Plan, func(i sync.PlanItem) bool { return i.Kind == "pending" && i.Skill == "demo" }) {
		t.Fatalf("plan: %+v", ctx.Plan)
	}
	e.execute(t, ctx)

	if _, err := os.Stat(filepath.Join(e.tmp, "claude", "demo")); !os.IsNotExist(err) {
		t.Fatal("m1 副本应被清")
	}
	recM2 := e.manifest.Find("demo", "m2", "")
	if len(recM2) == 0 || !recM2[0].PendingDeletion {
		t.Fatal("m2 应标 pending_deletion")
	}
	// m2 sync 时执行 pending
	e.manifest.ProcessPendingDeletions("m2", false)
	if _, err := os.Stat(m2Dir); !os.IsNotExist(err) {
		t.Fatal("m2 pending 副本应被删")
	}
}

func TestSyncOrphanRecordCleaned(t *testing.T) {
	// manifest 有记录但 canonical 已删(git rm 后 sync)→ 自动清理。
	e := newFakeEnv(t)
	d := filepath.Join(e.tmp, "claude", "ghost")
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(d, "SKILL.md"), []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}
	e.manifest.Upsert(manifest.DeployRecord{
		Skill: "ghost", Machine: "m1", Agent: "ClaudeCode",
		DeployPath: filepath.Join(d, "SKILL.md"), Method: "cp"})

	ctx := e.collect(t, nil, nil, false)
	if !anyItem(ctx.Plan, func(i sync.PlanItem) bool {
		return i.Kind == "delete" && i.Skill == "ghost"
	}) {
		t.Fatalf("plan: %+v", ctx.Plan)
	}
	e.execute(t, ctx)
	if _, err := os.Stat(d); !os.IsNotExist(err) {
		t.Fatal("孤儿副本应被清")
	}
	if len(e.manifest.Find("ghost", "", "")) != 0 {
		t.Fatal("记录应清")
	}
}

func TestSyncHermesOversizeSkippedAndStaleCleaned(t *testing.T) {
	e := newFakeEnv(t)
	huge := strings.Repeat("line\n", 20_100)
	writeCanonical(t, e.repo, "big", huge, "", nil)

	// 第一次: Hermes skip, 但 ClaudeCode cp
	ctx := e.collect(t, []string{"big"}, nil, false)
	e.execute(t, ctx)
	if _, err := os.Stat(filepath.Join(e.tmp, "claude", "big", "SKILL.md")); err != nil {
		t.Fatal("ClaudeCode 应部署")
	}
	if _, err := os.Stat(filepath.Join(e.tmp, "hermes", "imported", "big")); !os.IsNotExist(err) {
		t.Fatal("Hermes 超限不应部署")
	}
	if len(e.manifest.Find("big", "m1", "Hermes")) != 0 {
		t.Fatal("Hermes 不应有记录")
	}

	// 伪造一份旧的 Hermes 记录(历史部署过), 再 sync 应清掉
	stale := filepath.Join(e.tmp, "hermes", "imported", "big")
	if err := os.MkdirAll(stale, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(stale, "SKILL.md"), []byte("old"), 0o644); err != nil {
		t.Fatal(err)
	}
	e.manifest.Upsert(manifest.DeployRecord{
		Skill: "big", Machine: "m1", Agent: "Hermes",
		DeployPath: filepath.Join(stale, "SKILL.md"), Method: "cp"})
	ctx2 := e.collect(t, []string{"big"}, nil, false)
	e.execute(t, ctx2)
	if _, err := os.Stat(stale); !os.IsNotExist(err) {
		t.Fatal("Hermes skip 后旧副本应清")
	}
	if len(e.manifest.Find("big", "m1", "Hermes")) != 0 {
		t.Fatal("Hermes 旧记录应清")
	}
}

func TestSyncZcodeCpOverwriteAndCleanTarget(t *testing.T) {
	// ZCode 改 cp 后: 真实目录被 cp 覆盖, 干净目标 cp 部署。
	e := newFakeEnv(t)
	writeCanonical(t, e.repo, "demo", "## body\n", "", nil)

	// 真实目录 → cp 覆盖(不再 deferred)
	real := filepath.Join(e.tmp, "zcode", "demo")
	if err := os.MkdirAll(real, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(real, "SKILL.md"), []byte("user real"), 0o644); err != nil {
		t.Fatal(err)
	}
	ctx := e.collect(t, []string{"demo"}, []string{"ZCode"}, false)
	e.execute(t, ctx)
	rb, _ := os.ReadFile(filepath.Join(real, "SKILL.md"))
	if strings.Contains(string(rb), "user real") {
		t.Fatal("应被 cp 覆盖")
	}
	rec := e.manifest.Find("demo", "m1", "ZCode")
	if len(rec) != 1 || rec[0].Method != "cp" {
		t.Fatalf("rec: %+v", rec)
	}

	// 干净目标 → cp(真实目录不是软链)
	real2 := filepath.Join(e.tmp, "zcode", "fresh")
	writeCanonical(t, e.repo, "fresh", "## body\n", "", nil)
	ctx2 := e.collect(t, []string{"fresh"}, []string{"ZCode"}, false)
	e.execute(t, ctx2)
	fi, err := os.Lstat(real2)
	if err != nil || !fi.IsDir() {
		t.Fatalf("应是真实目录不是软链: %v", err)
	}
	if _, err := os.Stat(filepath.Join(real2, "SKILL.md")); err != nil {
		t.Fatal("SKILL.md 应存在")
	}
	rec2 := e.manifest.Find("fresh", "m1", "ZCode")
	if len(rec2) != 1 || rec2[0].Method != "cp" {
		t.Fatalf("rec2: %+v", rec2)
	}
}

func TestSyncAgentNotOnMachineNotPlanned(t *testing.T) {
	// 机器没配的 Agent(如 m1 无 Codex)不出现在计划。
	e := newFakeEnv(t)
	writeCanonical(t, e.repo, "demo", "## body\n", "", nil)
	ctx := e.collect(t, nil, nil, false)
	for _, it := range ctx.Plan {
		if it.Agent == "Codex" {
			t.Fatalf("m1 没配 Codex, 不应出现: %+v", it)
		}
	}
}

func TestSyncAgentNotInstalledSkippedNoOrphanDirs(t *testing.T) {
	// 机器配置了 agent 但其 home 目录不存在(没装)→ skip 且绝不 mkdir 造孤儿目录。
	e := newFakeEnv(t)
	e.machines.SetSkillsDir("m1", "Codex", filepath.Join(e.tmp, "nope", ".codex", "skills"))
	writeCanonical(t, e.repo, "demo", "## body\n", "", nil)
	ctx := e.collect(t, nil, nil, false)
	skips := []sync.PlanItem{}
	for _, it := range ctx.Plan {
		if it.Kind == "skip" && it.Agent == "Codex" {
			skips = append(skips, it)
		}
	}
	if len(skips) == 0 || !strings.Contains(skips[0].Detail, "未安装") {
		t.Fatalf("skips: %+v", skips)
	}
	e.execute(t, ctx)
	if _, err := os.Stat(filepath.Join(e.tmp, "nope")); !os.IsNotExist(err) {
		t.Fatal("不允许为没装的 agent 造目录")
	}
	if len(e.manifest.Find("demo", "m1", "Codex")) != 0 {
		t.Fatal("没装的 agent 不应有记录")
	}
	// 对照: ClaudeCode 正常部署
	if _, err := os.Stat(filepath.Join(e.tmp, "claude", "demo", "SKILL.md")); err != nil {
		t.Fatal("ClaudeCode 应正常部署")
	}
}

func hasPair(pairs [][2]string, skill, agent string) bool {
	for _, p := range pairs {
		if p[0] == skill && p[1] == agent {
			return true
		}
	}
	return false
}

func mtime(t *testing.T, path string) int64 {
	t.Helper()
	fi, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	return fi.ModTime().UnixNano()
}

// --- 零损耗部署语义回归锁(移植 tests/test_deploy_semantics.py) ---

func TestDeployedZeroLossSemantics(t *testing.T) {
	// 正确口径(ClaudeCode, 不注入前言):
	//   deployed = frontmatter块 + canonical body, body 完整出现在文件末尾。
	// 前言注入(native 提示🪧/能力警告⚠️)从未实现;本测试锁的就是"不注入"。
	tmp := t.TempDir()
	repo := filepath.Join(tmp, "repo")
	canonDir := filepath.Join(repo, "skills", "img")
	if err := os.MkdirAll(filepath.Join(canonDir, "scripts"), 0o755); err != nil {
		t.Fatal(err)
	}
	body := []byte("## gen\n\nmake image\r\nCRLF kept\n")
	native := "Hermes"
	in := &sbir.SkillIR{
		Name: "img", Description: "d", Body: body, Level: sbir.Auto,
		NativeAgent: &native, Requires: []string{"image_generation"},
	}
	if err := emit.EmitCanonical(in, filepath.Join(canonDir, "SKILL.md")); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(canonDir, "scripts", "run.py"),
		[]byte("print(1)\n"), 0o644); err != nil {
		t.Fatal(err)
	}

	agentsCfg, err := config.LoadAgents(filepath.Join(repoRoot(t), "agents.toml"))
	if err != nil {
		t.Fatal(err)
	}
	machines := config.NewMachinesConfig()
	machines.SetSkillsDir("m", "ClaudeCode", filepath.Join(tmp, "cc"))
	m := &manifest.DeploymentsManifest{Path: filepath.Join(repo, "manifests", "d.json")}

	ctx, err := sync.Collect(repo, "m", nil, nil, machines, agentsCfg, m, false)
	if err != nil {
		t.Fatal(err)
	}
	if rc := sync.Execute(repo, "m", ctx, machines, agentsCfg, m); rc != 0 {
		t.Fatalf("rc: %d", rc)
	}

	raw, err := os.ReadFile(filepath.Join(tmp, "cc", "img", "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasSuffix(string(raw), string(body)) {
		t.Fatal("canonical body 必须完整在 deployed 文件末尾")
	}
	// 前言注入未实现:fm 只含 {name, description}, 不应有 🪧 native 提示
	fmPart := strings.SplitN(string(raw), "---\n", 3)[1]
	for _, k := range []string{"name:", "description:"} {
		if !strings.Contains(fmPart, k) {
			t.Fatalf("fm 应含 %s:\n%s", k, fmPart)
		}
	}
	for _, bad := range []string{"native_agent", "requires", "🪧"} {
		if strings.Contains(fmPart, bad) || strings.Contains(string(raw), "🪧") {
			t.Fatalf("前言注入未实现, 不应有 %s:\n%s", bad, fmPart)
		}
	}
	// 资源镜像
	rb, err := os.ReadFile(filepath.Join(tmp, "cc", "img", "scripts", "run.py"))
	if err != nil || string(rb) != "print(1)\n" {
		t.Fatalf("scripts 镜像: %v %q", err, rb)
	}
	// manifest: ir_hash = sha256(body)
	rec := m.Find("img", "m", "ClaudeCode")[0]
	sum := sha256.Sum256(body)
	if rec.Method != "cp" || rec.IrHash != "sha256:"+hex.EncodeToString(sum[:]) {
		t.Fatalf("rec: %+v", rec)
	}
}
