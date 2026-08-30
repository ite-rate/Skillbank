// DeploymentsManifest + 删除链测试(移植 tests/test_manifest.py 15 条, 语义等价)。
//
// 覆盖: load/save 往返 + 原子写 + version 校验 + JSON 字节兼容(Python 产物全等)、
// upsert 替换/追加、delete_local(cp 目录删/软链 unlink 不动目标/容错/dry_run)、
// 用户手放 skill 不被触碰、pending_deletion 跨机删除链、check_consistency 对账。
package manifest_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/ite-rate/skillbank/internal/manifest"
)

func rec(skill, machine, agent, deployPath, method, irHash string, pending bool) manifest.DeployRecord {
	if deployPath == "" {
		deployPath = "/tmp/nonexistent/demo"
	}
	if irHash == "" {
		irHash = "sha256:abc"
	}
	return manifest.DeployRecord{
		Skill: skill, Machine: machine, Agent: agent,
		DeployPath: deployPath, Method: method, IrHash: irHash,
		PendingDeletion: pending,
	}
}

func writeFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

// --- load / save ---

func TestManifestSaveLoadRoundtrip(t *testing.T) {
	dir := t.TempDir()
	m := &manifest.DeploymentsManifest{Path: filepath.Join(dir, "deployments.json")}
	// 造一个真实文件路径让 consistency 不吵
	skillDir := filepath.Join(dir, "agents", "demo")
	writeFile(t, filepath.Join(skillDir, "SKILL.md"), "---\nname: demo\n---\nbody\n")
	m.Upsert(manifest.DeployRecord{
		Skill: "demo", Machine: "mac-main", Agent: "ClaudeCode",
		DeployPath: filepath.Join(skillDir, "SKILL.md"), Method: "cp", IrHash: "sha256:x",
	})
	if err := m.Save(""); err != nil {
		t.Fatal(err)
	}

	m2, err := manifest.Load(filepath.Join(dir, "deployments.json"))
	if err != nil {
		t.Fatal(err)
	}
	if len(m2.Records) != 1 {
		t.Fatalf("records: %d", len(m2.Records))
	}
	r := m2.Records[0]
	if r.Skill != "demo" || r.Machine != "mac-main" || r.Agent != "ClaudeCode" ||
		r.Method != "cp" || r.IrHash != "sha256:x" {
		t.Fatalf("record 字段丢失: %+v", r)
	}
	if r.DeployedAt == "" {
		t.Fatal("应自动填时间戳")
	}
	// 文件头是 version 字段
	raw, _ := os.ReadFile(filepath.Join(dir, "deployments.json"))
	var d struct {
		Version int `json:"version"`
	}
	if err := json.Unmarshal(raw, &d); err != nil {
		t.Fatal(err)
	}
	if d.Version != manifest.ManifestVersion {
		t.Fatalf("version: %d", d.Version)
	}
}

func TestManifestSaveByteCompatWithPython(t *testing.T) {
	// 字节合同: 与 Python json.dumps(ensure_ascii=False, indent=2)+"\n" 全等
	// (中文直出 / "<&>" 不转义 / 单尾换行)。跨机 git diff 零噪音的硬保证。
	m := &manifest.DeploymentsManifest{}
	m.Upsert(manifest.DeployRecord{
		Skill: "中文演示", Machine: "mac-main", Agent: "ClaudeCode",
		DeployPath: "/x/y <&>/SKILL.md", DeployedAt: "2026-01-01T00:00:00Z",
		Method: "cp", IrHash: "sha256:x", Note: "n",
	})
	dir := t.TempDir()
	m.Path = filepath.Join(dir, "d.json")
	if err := m.Save(""); err != nil {
		t.Fatal(err)
	}
	expected := `{
  "version": 1,
  "records": [
    {
      "skill": "中文演示",
      "machine": "mac-main",
      "agent": "ClaudeCode",
      "deploy_path": "/x/y <&>/SKILL.md",
      "deployed_at": "2026-01-01T00:00:00Z",
      "method": "cp",
      "ir_hash": "sha256:x",
      "note": "n",
      "pending_deletion": false
    }
  ]
}
`
	out, err := os.ReadFile(filepath.Join(dir, "d.json"))
	if err != nil {
		t.Fatal(err)
	}
	if string(out) != expected {
		t.Fatalf("manifest JSON 与 Python 基准字节不等\nGo 产物:\n%s\n期望:\n%s", out, expected)
	}
}

func TestManifestLoadMissingFileReturnsEmpty(t *testing.T) {
	m, err := manifest.Load(filepath.Join(t.TempDir(), "nope.json"))
	if err != nil {
		t.Fatal(err)
	}
	if len(m.Records) != 0 {
		t.Fatal("缺文件应返回空表")
	}
}

func TestManifestLoadBadVersionRaises(t *testing.T) {
	p := filepath.Join(t.TempDir(), "bad.json")
	writeFile(t, p, `{"version": 99, "records": []}`)
	if _, err := manifest.Load(p); err == nil || !strings.Contains(err.Error(), "version") {
		t.Fatalf("应报 version 错, got %v", err)
	}
}

func TestManifestSaveAtomicNoTmpLeft(t *testing.T) {
	dir := t.TempDir()
	m := &manifest.DeploymentsManifest{Path: filepath.Join(dir, "d.json")}
	m.Upsert(rec("", "", "", filepath.Join(dir, "x"), "", "", false))
	if err := m.Save(""); err != nil {
		t.Fatal(err)
	}
	items, _ := os.ReadDir(dir)
	for _, e := range items {
		if strings.HasSuffix(e.Name(), ".tmp") {
			t.Fatalf("原子写不应留 tmp 文件: %s", e.Name())
		}
	}
}

// --- upsert ---

func TestUpsertSameKeyReplaces(t *testing.T) {
	m := manifest.DeploymentsManifest{}
	m.Upsert(rec("demo", "mac-main", "ClaudeCode", "", "", "sha256:old", false))
	m.Upsert(rec("demo", "mac-main", "ClaudeCode", "", "", "sha256:new", false))
	if len(m.Records) != 1 || m.Records[0].IrHash != "sha256:new" {
		t.Fatalf("同 key 应替换: %+v", m.Records)
	}
}

func TestUpsertDifferentKeysAppend(t *testing.T) {
	m := manifest.DeploymentsManifest{}
	m.Upsert(rec("demo", "mac-main", "ClaudeCode", "", "", "", false))
	m.Upsert(rec("demo", "mac-main", "Codex", "", "", "", false))
	m.Upsert(rec("demo", "laptop", "ClaudeCode", "", "", "", false))
	if len(m.Records) != 3 {
		t.Fatalf("不同 key 应追加: %d", len(m.Records))
	}
}

// --- delete_local ---

func TestDeleteLocalRemovesCpDirAndRecord(t *testing.T) {
	// cp 记录: deploy_path 指向 <dir>/SKILL.md → 删整个 skill 目录 + 清记录。
	dir := t.TempDir()
	skillDir := filepath.Join(dir, "claude-skills", "demo")
	writeFile(t, filepath.Join(skillDir, "SKILL.md"), "body")

	m := manifest.DeploymentsManifest{}
	m.Upsert(manifest.DeployRecord{
		Skill: "demo", Machine: "mac-main", Agent: "ClaudeCode",
		DeployPath: filepath.Join(skillDir, "SKILL.md"), Method: "cp",
	})
	actions := m.DeleteLocal("demo", "mac-main", "", false)
	if !anyContains(actions, "deleted") {
		t.Fatalf("actions: %v", actions)
	}
	if _, err := os.Stat(skillDir); !os.IsNotExist(err) {
		t.Fatal("cp 的 skill 目录应被删")
	}
	if len(m.Find("demo", "", "")) != 0 {
		t.Fatal("记录应清")
	}
}

func TestDeleteLocalUnlinksSymlinkNotTarget(t *testing.T) {
	// ln 记录: 删软链本身, 链接目标(canonical)必须完好。
	dir := t.TempDir()
	canonical := filepath.Join(dir, "Skillbank", "skills", "demo")
	writeFile(t, filepath.Join(canonical, "SKILL.md"), "canonical body")

	zcodeSkills := filepath.Join(dir, "zcode-skills")
	if err := os.MkdirAll(zcodeSkills, 0o755); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(zcodeSkills, "demo")
	if err := os.Symlink(canonical, link); err != nil {
		t.Fatal(err)
	}

	m := manifest.DeploymentsManifest{}
	m.Upsert(manifest.DeployRecord{
		Skill: "demo", Machine: "mac-main", Agent: "ZCode",
		DeployPath: link, Method: "ln",
	})
	actions := m.DeleteLocal("demo", "mac-main", "", false)
	if !anyContains(actions, "unlinked") {
		t.Fatalf("actions: %v", actions)
	}
	if _, err := os.Lstat(link); !os.IsNotExist(err) {
		t.Fatal("软链应被删")
	}
	body, err := os.ReadFile(filepath.Join(canonical, "SKILL.md"))
	if err != nil || string(body) != "canonical body" {
		t.Fatal("canonical 目标绝不能被删除链碰到")
	}
}

func TestDeleteLocalMissingPathTolerated(t *testing.T) {
	dir := t.TempDir()
	m := manifest.DeploymentsManifest{}
	m.Upsert(manifest.DeployRecord{
		Skill: "ghost", Machine: "mac-main", Agent: "Codex",
		DeployPath: filepath.Join(dir, "gone", "SKILL.md"), Method: "cp",
	})
	actions := m.DeleteLocal("ghost", "mac-main", "", false)
	if !anyContains(actions, "already gone") {
		t.Fatalf("actions: %v", actions)
	}
	if len(m.Find("ghost", "", "")) != 0 {
		t.Fatal("记录应清")
	}
}

func TestDeleteLocalDryRunNoTouch(t *testing.T) {
	dir := t.TempDir()
	skillDir := filepath.Join(dir, "s", "demo")
	writeFile(t, filepath.Join(skillDir, "SKILL.md"), "b")
	m := manifest.DeploymentsManifest{}
	m.Upsert(manifest.DeployRecord{
		Skill: "demo", Machine: "mac-main", Agent: "ClaudeCode",
		DeployPath: filepath.Join(skillDir, "SKILL.md"), Method: "cp",
	})
	actions := m.DeleteLocal("demo", "mac-main", "", true)
	if !anyContains(actions, "WOULD DELETE") {
		t.Fatalf("actions: %v", actions)
	}
	if _, err := os.Stat(skillDir); err != nil {
		t.Fatal("dry_run 不应动盘")
	}
	if len(m.Find("demo", "", "")) != 1 {
		t.Fatal("dry_run 不应清记录")
	}
}

func TestUserPlacedSkillNeverTouched(t *testing.T) {
	// 删除链只动 manifest 记录的路径; 同目录用户手放的 skill 不受影响。
	dir := t.TempDir()
	sharedRoot := filepath.Join(dir, "claude-skills")
	managed := filepath.Join(sharedRoot, "managed-skill")
	userPlaced := filepath.Join(sharedRoot, "user-skill")
	writeFile(t, filepath.Join(managed, "SKILL.md"), "m")
	writeFile(t, filepath.Join(userPlaced, "SKILL.md"), "u")

	m := manifest.DeploymentsManifest{}
	m.Upsert(manifest.DeployRecord{
		Skill: "managed-skill", Machine: "mac-main", Agent: "ClaudeCode",
		DeployPath: filepath.Join(managed, "SKILL.md"), Method: "cp",
	})
	m.DeleteLocal("managed-skill", "mac-main", "", false)
	if _, err := os.Stat(managed); !os.IsNotExist(err) {
		t.Fatal("managed 应被删")
	}
	body, err := os.ReadFile(filepath.Join(userPlaced, "SKILL.md"))
	if err != nil || string(body) != "u" {
		t.Fatal("用户手放 skill 必须原封不动")
	}
}

// --- pending_deletion 跨机 ---

func TestMarkPendingDeletionExceptLocal(t *testing.T) {
	m := manifest.DeploymentsManifest{}
	m.Upsert(rec("demo", "mac-main", "ClaudeCode", "/tmp/a", "", "", false))
	m.Upsert(rec("demo", "laptop", "ClaudeCode", "/tmp/b", "", "", false))
	m.Upsert(rec("demo", "remote", "Codex", "/tmp/c", "", "", false))
	n := m.MarkPendingDeletion("demo", "mac-main")
	if n != 2 {
		t.Fatalf("应标 2 条, got %d", n)
	}
	if m.Find("demo", "mac-main", "")[0].PendingDeletion {
		t.Fatal("本机记录不应标 pending")
	}
	if !m.Find("demo", "laptop", "")[0].PendingDeletion || !m.Find("demo", "remote", "")[0].PendingDeletion {
		t.Fatal("其它机器记录应标 pending")
	}
}

func TestProcessPendingDeletionsOnLaptop(t *testing.T) {
	// laptop sync 时执行 pending: 删 laptop 盘上的, mac-main 的不动。
	dir := t.TempDir()
	macDir := filepath.Join(dir, "mac", "demo")
	laptopDir := filepath.Join(dir, "laptop", "demo")
	writeFile(t, filepath.Join(macDir, "SKILL.md"), "m")
	writeFile(t, filepath.Join(laptopDir, "SKILL.md"), "l")

	m := manifest.DeploymentsManifest{}
	m.Upsert(manifest.DeployRecord{Skill: "demo", Machine: "mac-main", Agent: "ClaudeCode",
		DeployPath: filepath.Join(macDir, "SKILL.md"), Method: "cp"})
	r := manifest.DeployRecord{Skill: "demo", Machine: "laptop", Agent: "ClaudeCode",
		DeployPath: filepath.Join(laptopDir, "SKILL.md"), Method: "cp", PendingDeletion: true}
	m.Upsert(r)

	actions := m.ProcessPendingDeletions("laptop", false)
	if !anyContains(actions, "pending") {
		t.Fatalf("actions: %v", actions)
	}
	if _, err := os.Stat(laptopDir); !os.IsNotExist(err) {
		t.Fatal("laptop 的 pending 副本应被删")
	}
	if _, err := os.Stat(macDir); err != nil {
		t.Fatal("mac-main(非 pending, 且不在本机)不应被动")
	}
	if len(m.Find("demo", "laptop", "")) != 0 {
		t.Fatal("laptop 记录应清")
	}
	if len(m.Find("demo", "mac-main", "")) != 1 {
		t.Fatal("mac-main 记录应保留")
	}
}

// --- consistency ---

func TestCheckConsistencyFindsMissingOnDisk(t *testing.T) {
	dir := t.TempDir()
	m := manifest.DeploymentsManifest{}
	m.Upsert(manifest.DeployRecord{Skill: "demo", Machine: "mac-main", Agent: "ClaudeCode",
		DeployPath: filepath.Join(dir, "missing", "SKILL.md"), Method: "cp"})
	issues := m.CheckConsistency()
	if !anyContains(issues, "missing on disk") {
		t.Fatalf("issues: %v", issues)
	}
}

func TestCheckConsistencyFindsDuplicates(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, "d", "SKILL.md")
	writeFile(t, p, "b")
	m := manifest.DeploymentsManifest{}
	m.Upsert(manifest.DeployRecord{Skill: "demo", Machine: "mac-main", Agent: "ClaudeCode",
		DeployPath: p, Method: "cp"})
	// 手动注入重复(绕过 upsert 的替换语义)
	m.Records = append(m.Records, m.Records[0])
	issues := m.CheckConsistency()
	if !anyContains(issues, "duplicate") {
		t.Fatalf("issues: %v", issues)
	}
}

func anyContains(list []string, sub string) bool {
	for _, s := range list {
		if strings.Contains(s, sub) {
			return true
		}
	}
	return false
}