// importer 反向导入测试(移植 tests/test_importer.py 16 条, 语义等价)。
//
// 覆盖: TeleAgent _cn→_zh 映射、QwenWorkCN 市场元数据→overrides、body 零损耗、
// 资源镜像、native 路径探测、重名三策略(去重/自动改名/callback)、路径扫描警告。
package importer_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/BurntSushi/toml"
	"github.com/ite-rate/skillbank/internal/config"
	"github.com/ite-rate/skillbank/internal/importer"
	"github.com/ite-rate/skillbank/internal/parser"
)

func mkAgentSkill(t *testing.T, base, agentDir, name string, fmLines []string,
	body string, files map[string]string) string {
	t.Helper()
	d := filepath.Join(base, agentDir, name)
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	content := "---\n" + strings.Join(fmLines, "\n") + "\n---\n"
	if err := os.WriteFile(filepath.Join(d, "SKILL.md"),
		[]byte(content+body), 0o644); err != nil {
		t.Fatal(err)
	}
	for rel, c := range files {
		p := filepath.Join(d, rel)
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte(c), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	return d
}

func mkMachines(t *testing.T, tmp string) *config.MachinesConfig {
	t.Helper()
	m := config.NewMachinesConfig()
	m.SetSkillsDir("m1", "TeleAgent", filepath.Join(tmp, "teleagent-skills"))
	m.SetSkillsDir("m1", "QwenWorkCN", filepath.Join(tmp, "qwen-skills"))
	return m
}

// --- TeleAgent 源 ---

func TestImportTeleagentCnToZh(t *testing.T) {
	home := t.TempDir()
	src := mkAgentSkill(t, home, "teleagent-skills", "canvas-design", []string{
		"name: canvas-design",
		"description: Create visual art",
		`name_cn: "创意海报"`,
		`description_cn: "创意海报设计工具"`,
		"license: MIT",
	}, "## body\n\ncontent\r\n", map[string]string{
		"prompts/p1.md": "# p1\n",
		"_meta.json":    `{"x":1}`,
	})

	repo := filepath.Join(home, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	res, err := importer.ImportSkill(src, repo, importer.Options{
		Machines: mkMachines(t, home), Machine: "m1",
	})
	if err != nil {
		t.Fatal(err)
	}

	irOut, err := parser.ParseCanonical(filepath.Join(res.CanonicalDir, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	if irOut.Name != "canvas-design" || irOut.Description != "Create visual art" {
		t.Fatalf("ir: %+v", irOut)
	}
	if irOut.DescZH == nil || *irOut.DescZH != "创意海报设计工具" {
		t.Fatalf("_cn 应映射为 canonical _zh: %v", irOut.DescZH)
	}
	if irOut.NameZH == nil || *irOut.NameZH != "创意海报" {
		t.Fatalf("name_cn 应映射为 name_zh: %v", irOut.NameZH)
	}
	if irOut.NativeAgent == nil || *irOut.NativeAgent != "TeleAgent" {
		t.Fatalf("应按路径探测 native: %v", irOut.NativeAgent)
	}
	if irOut.License == nil || *irOut.License != "MIT" {
		t.Fatalf("license: %v", irOut.License)
	}
	if string(irOut.Level) != "manual" {
		t.Fatalf("level 应默认 manual(未审不自动触发): %s", irOut.Level)
	}
	if string(irOut.Body) != "## body\n\ncontent\r\n" {
		t.Fatalf("body 零损耗(CRLF 保留): %q", irOut.Body)
	}

	// 资源镜像
	b, err := os.ReadFile(filepath.Join(res.CanonicalDir, "prompts", "p1.md"))
	if err != nil || string(b) != "# p1\n" {
		t.Fatalf("prompts 镜像: %v %q", err, b)
	}
	if _, err := os.Stat(filepath.Join(res.CanonicalDir, "_meta.json")); err != nil {
		t.Fatal("_meta.json 应镜像")
	}
	// license 是 canonical 字段 → 无 leftovers → 无 overrides
	entries, _ := os.ReadDir(filepath.Join(res.CanonicalDir, ".agent_overrides"))
	if len(entries) != 0 {
		t.Fatalf("不应有 overrides: %v", entries)
	}
}

func TestImportQwenMarketMetadataToOverrides(t *testing.T) {
	home := t.TempDir()
	src := mkAgentSkill(t, home, "qwen-skills", "bilibili-summary", []string{
		"name: bilibili-summary",
		"description: Summarize bilibili videos",
		"install_source: market",
		"skill_id: abc-123",
		"enabled_at: 2026-08-14T00:00:00Z",
		"version: 1.2.0",
	}, "## body\n", nil)

	repo := filepath.Join(home, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	res, err := importer.ImportSkill(src, repo, importer.Options{
		Machines: mkMachines(t, home), Machine: "m1",
	})
	if err != nil {
		t.Fatal(err)
	}

	irOut, err := parser.ParseCanonical(filepath.Join(res.CanonicalDir, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	if irOut.NativeAgent == nil || *irOut.NativeAgent != "QwenWorkCN" {
		t.Fatalf("native: %v", irOut.NativeAgent)
	}
	if irOut.Version == nil || *irOut.Version != "1.2.0" {
		t.Fatalf("canonical 认识 version: %v", irOut.Version)
	}
	// 市场元数据进 overrides, 不污染 canonical frontmatter
	ovPath := filepath.Join(res.CanonicalDir, ".agent_overrides", "QwenWorkCN.toml")
	raw, err := os.ReadFile(ovPath)
	if err != nil {
		t.Fatalf("应有 QwenWorkCN overrides: %v", err)
	}
	var d map[string]any
	if err := toml.Unmarshal(raw, &d); err != nil {
		t.Fatal(err)
	}
	if d["install_source"] != "market" || d["skill_id"] != "abc-123" {
		t.Fatalf("overrides 内容: %v", d)
	}
	skMD, _ := os.ReadFile(filepath.Join(res.CanonicalDir, "SKILL.md"))
	fmPart := strings.SplitN(string(skMD), "---\n", 3)[1]
	if strings.Contains(fmPart, "install_source") || strings.Contains(fmPart, "skill_id") {
		t.Fatalf("市场元数据不应进 canonical frontmatter:\n%s", fmPart)
	}
}

// --- 边界 ---

func TestImportMissingDescriptionRaises(t *testing.T) {
	home := t.TempDir()
	src := mkAgentSkill(t, home, "some-skills", "bad", []string{"name: bad"}, "## b\n", nil)
	repo := filepath.Join(home, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	_, err := importer.ImportSkill(src, repo, importer.Options{})
	if err == nil || !strings.Contains(err.Error(), "description") {
		t.Fatalf("got %v", err)
	}
}

func TestImportExistingCanonicalSameBodySilentDedup(t *testing.T) {
	// 同 body 同名(重复 import 同源) → 静默去重返回, 不报错(用户拍板)。
	home := t.TempDir()
	src := mkAgentSkill(t, home, "some-skills", "dup",
		[]string{"name: dup", "description: x"}, "## body\n", nil)
	repo := filepath.Join(home, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	r1, err := importer.ImportSkill(src, repo, importer.Options{})
	if err != nil {
		t.Fatal(err)
	}
	// 第二次同 body: 不抛, 返回已存在的, 带 dedup 警告
	r2, err := importer.ImportSkill(src, repo, importer.Options{})
	if err != nil {
		t.Fatalf("同 body 重复 import 应静默返回: %v", err)
	}
	if r1.CanonicalDir != r2.CanonicalDir {
		t.Fatalf("应返回已存在目录: %s vs %s", r1.CanonicalDir, r2.CanonicalDir)
	}
	if !anyWarn(r2.Warnings, "去重") {
		t.Fatalf("warnings: %v", r2.Warnings)
	}
	// force 仍允许重入(用户想重覆盖时)
	r3, err := importer.ImportSkill(src, repo, importer.Options{Force: true})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(r3.CanonicalDir); err != nil {
		t.Fatal("force 重入应存在")
	}
}

func TestImportExistingCanonicalDiffBodyNoAutoRenameRaises(t *testing.T) {
	// 不同 body 同名 + 关自动改名 + 无 callback → 报错(防自动覆盖)。
	home := t.TempDir()
	s1 := mkAgentSkill(t, home, "sk1", "dup",
		[]string{"name: dup", "description: x"}, "## A\n", nil)
	s2 := mkAgentSkill(t, home, "sk2", "dup",
		[]string{"name: dup", "description: x"}, "## B body\n", nil)
	repo := filepath.Join(home, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	if _, err := importer.ImportSkill(s1, repo, importer.Options{DisableAutoRename: true}); err != nil {
		t.Fatal(err)
	}
	_, err := importer.ImportSkill(s2, repo, importer.Options{DisableAutoRename: true})
	if err == nil || !strings.Contains(err.Error(), "已存在且 body 不同") {
		t.Fatalf("got %v", err)
	}
}

func TestImportDiffBodyAutoRename(t *testing.T) {
	// 不同 body 同名 + 自动改名 → 用建议名(原名-native 短码)。
	home := t.TempDir()
	s1 := mkAgentSkill(t, home, "sk1", "dup",
		[]string{"name: dup", "description: x"}, "## A\n", nil)
	s2 := mkAgentSkill(t, home, "sk2", "dup",
		[]string{"name: dup", "description: x"}, "## B\n", nil)
	repo := filepath.Join(home, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	r1, err := importer.ImportSkill(s1, repo, importer.Options{Agent: "ClaudeCode"})
	if err != nil {
		t.Fatal(err)
	}
	if filepath.Base(r1.CanonicalDir) != "dup" {
		t.Fatalf("首个应原名导入: %s", r1.CanonicalDir)
	}
	// 第二次不同 body 来自 TeleAgent → 自动建议名 dup-tele
	r2, err := importer.ImportSkill(s2, repo, importer.Options{Agent: "TeleAgent"})
	if err != nil {
		t.Fatal(err)
	}
	if filepath.Base(r2.CanonicalDir) != "dup-tele" {
		t.Fatalf("建议名应为 dup-tele, got %s", r2.CanonicalDir)
	}
	for _, n := range []string{"dup", "dup-tele"} {
		if _, err := os.Stat(filepath.Join(repo, "skills", n)); err != nil {
			t.Fatalf("skills/%s 应存在: %v", n, err)
		}
	}
}

func TestImportDiffBodyRenameCallback(t *testing.T) {
	// 不同 body 同名 + rename_callback → 用 callback 返回的名(用户自决)。
	home := t.TempDir()
	s1 := mkAgentSkill(t, home, "sk1", "dup",
		[]string{"name: dup", "description: x"}, "## A\n", nil)
	s2 := mkAgentSkill(t, home, "sk2", "dup",
		[]string{"name: dup", "description: x"}, "## B\n", nil)
	repo := filepath.Join(home, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	if _, err := importer.ImportSkill(s1, repo, importer.Options{DisableAutoRename: true}); err != nil {
		t.Fatal(err)
	}
	cb := func(orig, suggested, native string) (string, error) { return "office-dup", nil }
	r2, err := importer.ImportSkill(s2, repo, importer.Options{
		DisableAutoRename: true, RenameCallback: cb, Agent: "Hermes",
	})
	if err != nil {
		t.Fatal(err)
	}
	if filepath.Base(r2.CanonicalDir) != "office-dup" {
		t.Fatalf("callback 应决定改名 office-dup: %s", r2.CanonicalDir)
	}
	// 建议名应是 dup-hermes
	if got := importer.SuggestVariantName("dup", "Hermes"); got != "dup-hermes" {
		t.Fatalf("suggest: %s", got)
	}
}

func TestShortAgentCodeAndSuggest(t *testing.T) {
	for agent, want := range map[string]string{
		"QwenWorkCN": "qwen", "TeleAgent": "tele", "ClaudeCode": "claude",
		"": "src",
	} {
		if got := importer.ShortAgentCode(agent); got != want {
			t.Fatalf("short_agent_code(%q) = %q, want %q", agent, got, want)
		}
	}
	if got := importer.SuggestVariantName("docx", "QwenWorkCN"); got != "docx-qwen" {
		t.Fatalf("suggest: %s", got)
	}
	if got := importer.SuggestVariantName("humanizer", "Hermes"); got != "humanizer-hermes" {
		t.Fatalf("suggest: %s", got)
	}
}

func TestImportNoFrontmatterRaises(t *testing.T) {
	home := t.TempDir()
	d := filepath.Join(home, "raw")
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(d, "SKILL.md"), []byte("just body\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	repo := filepath.Join(home, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	_, err := importer.ImportSkill(d, repo, importer.Options{})
	if err == nil || !strings.Contains(err.Error(), "frontmatter") {
		t.Fatalf("got %v", err)
	}
}

func TestDetectSourceAgentUnknown(t *testing.T) {
	home := t.TempDir()
	m := mkMachines(t, home)
	if got := importer.DetectSourceAgent(filepath.Join(home, "elsewhere", "skill"), m, "m1"); got != "" {
		t.Fatalf("未知路径应为空, got %q", got)
	}
	if got := importer.DetectSourceAgent(filepath.Join(home, "teleagent-skills", "s"), m, "m1"); got != "TeleAgent" {
		t.Fatalf("got %q", got)
	}
}

func TestImportExplicitAgentFlagBeatsDetection(t *testing.T) {
	home := t.TempDir()
	src := mkAgentSkill(t, home, "teleagent-skills", "x1",
		[]string{"name: x1", "description: x"}, "## b\n", nil)
	repo := filepath.Join(home, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	res, err := importer.ImportSkill(src, repo, importer.Options{
		Agent: "ClaudeCode", Machines: mkMachines(t, home), Machine: "m1",
	})
	if err != nil {
		t.Fatal(err)
	}
	irOut, err := parser.ParseCanonical(filepath.Join(res.CanonicalDir, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	if irOut.NativeAgent == nil || *irOut.NativeAgent != "ClaudeCode" {
		t.Fatalf("显式 agent 应优先: %v", irOut.NativeAgent)
	}
}

// --- P0 #1: scan_body_paths 路径警告 ---

func TestScanBodyPathsAbsoluteWarns(t *testing.T) {
	body := []byte("## Step\n\nRun /Users/ss/.claude/skills/foo/run.py\n")
	if !anyWarn(importer.ScanBodyPaths(body), "绝对路径") {
		t.Fatal("应警告绝对路径")
	}
}

func TestScanBodyPathsWindowsDriveWarns(t *testing.T) {
	body := []byte("python E:\\anaconda\\python.exe C:\\Users\\x\\r.py\n")
	if !anyWarn(importer.ScanBodyPaths(body), "绝对路径") {
		t.Fatal("应警告 Windows 盘符绝对路径")
	}
}

func TestScanBodyPathsCrossDirWarns(t *testing.T) {
	body := []byte("## Step\n\n参考 ../shared/templates.md 的模板\n")
	if !anyWarn(importer.ScanBodyPaths(body), "跨 skill 目录") {
		t.Fatal("应警告跨目录相对路径")
	}
}

func TestScanBodyPathsCleanReturnsEmpty(t *testing.T) {
	body := []byte("## Step\n\nRun scripts/run.py\n用 ./resources/x.png\n")
	if ws := importer.ScanBodyPaths(body); len(ws) != 0 {
		t.Fatalf("干净 body 应零警告: %v", ws)
	}
}

func TestImportReturnsPathWarnings(t *testing.T) {
	home := t.TempDir()
	src := mkAgentSkill(t, home, "sk", "x",
		[]string{"name: x", "description: x"}, "## step\nrun /Users/nope.py\n", nil)
	repo := filepath.Join(home, "repo")
	if err := os.MkdirAll(repo, 0o755); err != nil {
		t.Fatal(err)
	}
	res, err := importer.ImportSkill(src, repo, importer.Options{})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(res.CanonicalDir); err != nil {
		t.Fatal("导入应成功")
	}
	if !anyWarn(res.Warnings, "绝对路径") {
		t.Fatalf("warnings: %v", res.Warnings)
	}
}

func anyWarn(ws []string, sub string) bool {
	for _, w := range ws {
		if strings.Contains(w, sub) {
			return true
		}
	}
	return false
}