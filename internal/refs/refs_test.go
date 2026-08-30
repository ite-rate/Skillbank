// 资源统计 + body 引用一致性 check 测试(移植 tests/test_refs.py 9 条 +
// test_refs_skill_dir.py 2 条)。
package refs_test

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/ite-rate/skillbank/internal/refs"
)

func writeFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

// --- resource_stats ---

func TestResourceStatsEmptyDirReturnsEmpty(t *testing.T) {
	if refs.ResourceStats(filepath.Join(t.TempDir(), "no")) != "" {
		t.Fatal("不存在目录应返回空")
	}
}

func TestResourceStatsClassification(t *testing.T) {
	// 混合目录: scripts/N references/M + 散文件(N 文件入 files/N)。
	d := filepath.Join(t.TempDir(), "skill")
	writeFile(t, filepath.Join(d, "SKILL.md"), "x") // 应排除
	writeFile(t, filepath.Join(d, "scripts", "a.py"), "x")
	writeFile(t, filepath.Join(d, "scripts", "b.py"), "x")
	writeFile(t, filepath.Join(d, "references", "ref.md"), "y")
	writeFile(t, filepath.Join(d, "LICENSE.txt"), "L") // 散文件
	if err := os.MkdirAll(filepath.Join(d, ".agent_overrides"), 0o755); err != nil {
		t.Fatal(err)
	}

	s := refs.ResourceStats(d)
	for _, want := range []string{"scripts/2", "references/1", "files/1"} {
		if !strings.Contains(s, want) {
			t.Fatalf("stats 应含 %s: %q", want, s)
		}
	}
	if strings.Contains(s, "SKILL.md") || strings.Contains(s, "agent_overrides") {
		t.Fatalf("SKILL.md/.agent_overrides 不应计入: %q", s)
	}
}

func TestResourceStatsNestedSubdirs(t *testing.T) {
	d := filepath.Join(t.TempDir(), "s")
	writeFile(t, filepath.Join(d, "scripts", "sub", "b.py"), "x")
	writeFile(t, filepath.Join(d, "scripts", "a.py"), "x")
	s := refs.ResourceStats(d)
	if !strings.Contains(s, "scripts/2") {
		t.Fatalf("stats: %q", s)
	}
}

// --- check_body_refs ---

func TestCheckBodyRefsOk(t *testing.T) {
	d := filepath.Join(t.TempDir(), "s")
	writeFile(t, filepath.Join(d, "scripts", "run.py"), "print(1)")
	body := []byte("## Step\n\nRun `scripts/run.py`\n")
	issues := refs.CheckBodyRefs(body, d)
	if len(issues) != 1 || issues[0].Severity != "ok" || issues[0].Ref != "scripts/run.py" {
		t.Fatalf("issues: %v", issues)
	}
}

func TestCheckBodyRefsMissing(t *testing.T) {
	// 引用 scripts/missing.py 但镜像目录没有 → missing(silent failure 可感)。
	d := filepath.Join(t.TempDir(), "s")
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	body := []byte("## Step\n\ncall `scripts/missing.py` --opt\n")
	issues := refs.CheckBodyRefs(body, d)
	if len(issues) != 1 || issues[0].Severity != "missing" || !strings.Contains(issues[0].Detail, "missing.py") {
		t.Fatalf("issues: %v", issues)
	}
}

func TestCheckBodyRefsExcludesAbsoluteAndParent(t *testing.T) {
	// 绝对路径 / https URL / ../ 引用都不查(scan_body_paths 管)。
	d := filepath.Join(t.TempDir(), "s")
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	body := []byte("## Step\n\nRun /Users/x/run.py ; " +
		"see <https://example.com/data.json> ; " +
		"ref `../shared/templates/foo.json`\n")
	if issues := refs.CheckBodyRefs(body, d); len(issues) != 0 {
		t.Fatalf("绝对/URL/../ 跨目录引用应不归本层 check: %v", issues)
	}
}

func TestCheckBodyRefsMultipleExtensions(t *testing.T) {
	d := filepath.Join(t.TempDir(), "s")
	for _, ext := range []string{"py", "sh", "json", "md", "yaml", "png", "ttf"} {
		writeFile(t, filepath.Join(d, "templates", "x."+ext), "x")
	}
	var refsList []string
	for _, ext := range []string{"py", "sh", "json", "md", "yaml", "png", "ttf"} {
		refsList = append(refsList, fmt.Sprintf("`templates/x.%s`", ext))
	}
	body := []byte("## Step\n\nRefer to " + strings.Join(refsList, ", ") + "\n")
	issues := refs.CheckBodyRefs(body, d)
	if len(issues) != 7 {
		t.Fatalf("issues: %v", issues)
	}
	for _, i := range issues {
		if i.Severity != "ok" {
			t.Fatalf("应全 ok: %v", issues)
		}
	}
}

func TestCheckBodyRefsDedup(t *testing.T) {
	// 同一引用在 body 多次出现, 只报一次。
	d := filepath.Join(t.TempDir(), "s")
	writeFile(t, filepath.Join(d, "scripts", "a.py"), "x")
	body := []byte("Run `scripts/a.py` then `scripts/a.py` again\n")
	if issues := refs.CheckBodyRefs(body, d); len(issues) != 1 {
		t.Fatalf("应去重: %v", issues)
	}
}

func TestCheckBodyRefsKnownSubdirsCollected(t *testing.T) {
	// scripts/references/resources/templates/prompts/fonts/rooms/agents/protocol 都检。
	d := filepath.Join(t.TempDir(), "s")
	subdirs := []string{"scripts", "references", "resources", "templates",
		"prompts", "fonts", "rooms", "agents", "protocol"}
	for _, sd := range subdirs {
		writeFile(t, filepath.Join(d, sd, "f.json"), "{}")
	}
	var parts []string
	for _, sd := range subdirs {
		parts = append(parts, fmt.Sprintf("`%s/f.json`", sd))
	}
	body := []byte("## Step\n\n" + strings.Join(parts, "    ") + "\n")
	issues := refs.CheckBodyRefs(body, d)
	if len(issues) != 9 {
		t.Fatalf("issues: %v", issues)
	}
	for _, i := range issues {
		if i.Severity != "ok" {
			t.Fatalf("应全 ok: %v", issues)
		}
	}
}

// --- SKILL_DIR 变量引用(data-report 真实场景) ---

func TestCheckBodyRefsSkillDirVar(t *testing.T) {
	d := filepath.Join(t.TempDir(), "s")
	writeFile(t, filepath.Join(d, "scripts", "run.py"), "x")
	// 形式 1: ${SKILL_DIR}/scripts/run.py (花括号形式)
	issues := refs.CheckBodyRefs([]byte("Run ${SKILL_DIR}/scripts/run.py to start\n"), d)
	if !anyRef(issues, "scripts/run.py") {
		t.Fatalf("应识 ${{SKILL_DIR}}/scripts 引用: %v", issues)
	}
	// 形式 2: "$SKILL_DIR/scripts/run.py" (双引号里裸变量)
	issues2 := refs.CheckBodyRefs([]byte(`python "$SKILL_DIR/scripts/run.py" --opt`+"\n"), d)
	if !anyRef(issues2, "scripts/run.py") {
		t.Fatalf("应识 $SKILL_DIR/scripts 引用: %v", issues2)
	}
	// 形式 3: $SKILL_DIR 不带花括号也不带引号
	issues3 := refs.CheckBodyRefs([]byte("exec $SKILL_DIR/scripts/run.py arg\n"), d)
	if !anyRef(issues3, "scripts/run.py") {
		t.Fatalf("应识无花括号形式: %v", issues3)
	}
}

func TestCheckBodyRefsDataReportRealBody(t *testing.T) {
	// 端到端: 真实 data-report body 含 SKILL_DIR/scripts/* 与 references/* 引用。
	src := filepath.Join(os.Getenv("HOME"), ".qwenworkcn", "skills", "data-report")
	if _, err := os.Stat(src); err != nil {
		t.Skip("data-report 未装")
	}
	raw, err := os.ReadFile(filepath.Join(src, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	issues := refs.CheckBodyRefs(bodyOf(t, raw), src)
	var missing []string
	for _, i := range issues {
		if i.Severity == "missing" {
			missing = append(missing, i.String())
		}
	}
	if len(missing) > 0 {
		t.Fatalf("data-report body 引用未在源目录全部存在: %v", missing)
	}
	refsSet := map[string]bool{}
	for _, i := range issues {
		refsSet[i.Ref] = true
	}
	if !anyKeyContains(refsSet, "xlsx_reader") || !anyKeyContains(refsSet, "references/") ||
		!anyKeyContains(refsSet, "html_report") {
		t.Fatalf("关键引用应识: %v", refsSet)
	}
}

func anyRef(issues []refs.BodyRefIssue, ref string) bool {
	for _, i := range issues {
		if i.Ref == ref {
			return true
		}
	}
	return false
}

func anyKeyContains(set map[string]bool, sub string) bool {
	for k := range set {
		if strings.Contains(k, sub) {
			return true
		}
	}
	return false
}

func bodyOf(t *testing.T, raw []byte) []byte {
	t.Helper()
	// frontmatter 边界后全部
	idx := strings.Index(string(raw), "---\n")
	rest := raw[idx+4:]
	idx2 := strings.Index(string(rest), "---\n")
	if idx < 0 || idx2 < 0 {
		t.Fatal("缺 frontmatter 边界")
	}
	return rest[idx2+4:]
}