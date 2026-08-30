// 零损耗硬约束 — CI 门(移植 tests/test_roundtrip.py, 14 条语义等价)。
//
// roundtrip: parse(canonical) → IR0 → EmitCanonical → parse → IR1
// 断言 IR1.Body == IR0.Body(字节完全等值)。
package parser_test

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"testing"

	"github.com/ite-rate/skillbank/internal/emit"
	"github.com/ite-rate/skillbank/internal/ir"
	"github.com/ite-rate/skillbank/internal/parser"
)

// roundtrip — canonical → parse → emit → parse, 返回 (IR0, IR1)。
func roundtrip(t *testing.T, content []byte) (*ir.SkillIR, *ir.SkillIR) {
	t.Helper()
	dir := t.TempDir()
	srcSkill := filepath.Join(dir, "SKILL.md")
	if err := os.WriteFile(srcSkill, content, 0o644); err != nil {
		t.Fatal(err)
	}
	ir0, err := parser.ParseCanonical(srcSkill)
	if err != nil {
		t.Fatalf("parse IR0: %v", err)
	}
	dstSkill := filepath.Join(dir, "dst", "SKILL.md")
	if err := os.MkdirAll(filepath.Dir(dstSkill), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := emit.EmitCanonical(ir0, dstSkill); err != nil {
		t.Fatalf("emit: %v", err)
	}
	ir1, err := parser.ParseCanonical(dstSkill)
	if err != nil {
		t.Fatalf("parse IR1: %v", err)
	}
	return ir0, ir1
}

func assertBodyIdentical(t *testing.T, ir0, ir1 *ir.SkillIR) {
	t.Helper()
	if !bytes.Equal(ir1.Body, ir0.Body) {
		t.Fatalf("零损耗被破\n原 body: %q\n往返 body: %q", ir0.Body, ir1.Body)
	}
}

func TestAsciiBodyRoundtripIdentical(t *testing.T) {
	original := []byte("---\nname: demo\ndescription: a demo skill\nlevel: auto\n---\n\nbody line 1\nbody line 2\n    indented line\n")
	ir0, ir1 := roundtrip(t, original)
	assertBodyIdentical(t, ir0, ir1)
}

func TestUnicodeChineseBodyRoundtripIdentical(t *testing.T) {
	original := []byte("---\n" +
		"name: canvas\n" +
		"description: 创意海报\n" +
		"level: auto\n" +
		"description_zh: 海报\n" +
		"---\n" +
		"正文开始\n" +
		"# 中文标题\n")
	ir0, ir1 := roundtrip(t, original)
	assertBodyIdentical(t, ir0, ir1)
}

func TestCrlfBodyNotNormalizedToLf(t *testing.T) {
	// 关键场景: canonical 用 \n; Agent 既有 skill 反向导入时可能含 \r\n。
	// parser/emitter 不得把 \r\n 改成 \n。
	original := []byte("---\r\nname: crlf\ndescription: x\r\nlevel: auto\r\n---\r\nfirst\r\nsecond\r\n")
	ir0, ir1 := roundtrip(t, original)
	assertBodyIdentical(t, ir0, ir1)
	// 特别校验: 原 CRLF 必须存在, 不被改成 LF
	if !bytes.Contains(ir1.Body, []byte("\r\n")) {
		t.Fatal("CRLF body 被规整成 LF — 零损耗破")
	}
}

func TestBodyWithTabsAndNullByte(t *testing.T) {
	original := []byte("---\nname: tabs\ndescription: x\nlevel: auto\n---\n\ta\tb\x00c\nend\n")
	ir0, ir1 := roundtrip(t, original)
	assertBodyIdentical(t, ir0, ir1)
}

func TestBodyStartsWithBlankLines(t *testing.T) {
	original := []byte("---\nname: blanks\ndescription: x\nlevel: auto\n---\n\n\n\nbody after blanks\n")
	ir0, ir1 := roundtrip(t, original)
	assertBodyIdentical(t, ir0, ir1)
	// 校验空行还在
	if !bytes.HasPrefix(ir1.Body, []byte("\n\n\n")) {
		t.Fatal("leading blank lines 被吞")
	}
}

func TestBodyStartsImmediatelyAfterFrontmatter(t *testing.T) {
	// body 紧贴 frontmatter —— 确认 body 前的第 1 字节没被吞。
	original := []byte("---\nname: adj\ndescription: x\nlevel: auto\n---\nno-blank-here\n")
	ir0, ir1 := roundtrip(t, original)
	assertBodyIdentical(t, ir0, ir1)
	if string(ir1.Body) != "no-blank-here\n" {
		t.Fatalf("body 首字节被吞: %q", ir1.Body)
	}
}

func TestEmptyBodyAfterFrontmatterNewlineOnly(t *testing.T) {
	original := []byte("---\nname: empty\ndescription: x\nlevel: auto\n---\n")
	ir0, ir1 := roundtrip(t, original)
	assertBodyIdentical(t, ir0, ir1)
	if len(ir0.Body) > 1 {
		t.Fatalf("空 body 应只剩分隔符换行: got %q", ir0.Body)
	}
}

func TestFullFieldSetRoundtripIdentical(t *testing.T) {
	// 完整 canonical frontmatter 字段 + 复杂 body 往返全等。
	original := []byte("---\n" +
		"name: full-fields\n" +
		"description: A skill with every canonical frontmatter field exercised.\n" +
		"level: manual\n" +
		"native_agent: TeleAgent\n" +
		"requires: [image_generation, file_write]\n" +
		"description_zh: 创意\n" +
		"name_zh: 创意\n" +
		"version: 1.0.0\n" +
		"license: MIT\n" +
		"---\n" +
		"\n## Step 1\n\nDo thing.\n\n```python\nprint('hi')\n```\n")
	ir0, ir1 := roundtrip(t, original)

	// field-level assertions
	if ir0.Name != "full-fields" {
		t.Fatalf("name: %q", ir0.Name)
	}
	if ir0.Level != ir.Manual {
		t.Fatalf("level: %q", ir0.Level)
	}
	if ir0.NativeAgent == nil || *ir0.NativeAgent != "TeleAgent" {
		t.Fatalf("native_agent: %v", ir0.NativeAgent)
	}
	if len(ir0.Requires) != 2 || ir0.Requires[0] != "image_generation" || ir0.Requires[1] != "file_write" {
		t.Fatalf("requires: %v", ir0.Requires)
	}
	if ir0.DescZH == nil || *ir0.DescZH != "创意" {
		t.Fatalf("description_zh: %v", ir0.DescZH)
	}
	if ir0.NameZH == nil || *ir0.NameZH != "创意" {
		t.Fatalf("name_zh: %v", ir0.NameZH)
	}
	if ir0.Version == nil || *ir0.Version != "1.0.0" {
		t.Fatalf("version: %v", ir0.Version)
	}
	if ir0.License == nil || *ir0.License != "MIT" {
		t.Fatalf("license: %v", ir0.License)
	}

	assertBodyIdentical(t, ir0, ir1)

	// field-level survive
	if ir1.Name != ir0.Name || ir1.Description != ir0.Description || ir1.Level != ir0.Level {
		t.Fatal("基本字段往返丢失")
	}
	if ir1.Requires == nil || len(ir1.Requires) != 2 {
		t.Fatalf("requires 往返丢失: %v", ir1.Requires)
	}
	if ir1.DescZH == nil || ir1.NameZH == nil || ir1.Version == nil || ir1.License == nil {
		t.Fatal("可选字段往返丢失")
	}
}

func TestDisableLevelRoundtrip(t *testing.T) {
	original := []byte("---\nname: dis\ndescription: x\nlevel: disable\n---\nbody\n")
	ir0, ir1 := roundtrip(t, original)
	if ir0.Level != ir.Disable {
		t.Fatalf("level: %q", ir0.Level)
	}
	if ir0.Level.AllowsSync() || ir0.Level.AllowsAutoTrigger() {
		t.Fatal("disable 不应允许 sync/auto trigger")
	}
	assertBodyIdentical(t, ir0, ir1)
}

func TestMissingFrontmatterRaises(t *testing.T) {
	// canonical 必须有 frontmatter; 无的非法文件应报错。
	dir := t.TempDir()
	p := filepath.Join(dir, "SKILL.md")
	if err := os.WriteFile(p, []byte("# just a body, no frontmatter\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := parser.ParseCanonical(p); err == nil {
		t.Fatal("无 frontmatter 应报错")
	}
}

func TestMissingRequiredNameRaises(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, "SKILL.md")
	if err := os.WriteFile(p, []byte("---\ndescription: x\nlevel: auto\n---\nbody\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	_, err := parser.ParseCanonical(p)
	if err == nil {
		t.Fatal("缺 name 应报错")
	}
	var re *ir.RequiredFieldError
	if !errors.As(err, &re) || re.Field != "name" {
		t.Fatalf("应为 RequiredFieldError(name), got %v", err)
	}
}

func TestBodyHashStable(t *testing.T) {
	// body_hash 稳定(同字节流两次 hash 一致), 用于 manifest 跨机零损耗验证。
	original := []byte("---\nname: hash\ndescription: x\nlevel: auto\n---\nbody\n")
	ir0, ir1 := roundtrip(t, original)
	if ir0.BodyHash() != ir1.BodyHash() {
		t.Fatal("往返后 body_hash 不一致 — body 已漂移")
	}
}

func TestFrontmatterBytesStableNoChange(t *testing.T) {
	// 无变更时 frontmatter 字节完全一致(引号/顺序/缩进都不漂)。
	// 回归: 此前 safe_dump 全量重建会去掉 description 引号(git diff 无意义噪音)。
	original := "---\n" +
		"name: atelier\n" +
		"description: \"Atelier (工作坊) — Creative breakthrough deliberation room.\"\n" +
		"level: manual\n" +
		"version: 1.2.0\n" +
		"---\n" +
		"# /atelier\n" +
		"body here\n"
	dir := t.TempDir()
	srcSkill := filepath.Join(dir, "SKILL.md")
	if err := os.WriteFile(srcSkill, []byte(original), 0o644); err != nil {
		t.Fatal(err)
	}
	parsed, err := parser.ParseCanonical(srcSkill)
	if err != nil {
		t.Fatal(err)
	}
	dstSkill := filepath.Join(dir, "dst", "SKILL.md")
	if err := os.MkdirAll(filepath.Dir(dstSkill), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := emit.EmitCanonical(parsed, dstSkill); err != nil {
		t.Fatal(err)
	}
	out, err := os.ReadFile(dstSkill)
	if err != nil {
		t.Fatal(err)
	}
	if string(out) != original {
		t.Fatalf("无变更时 frontmatter 字节应完全一致\n原: %q\n出: %q", original, out)
	}
}

func TestFrontmatterUnchangedFieldsPreservedWhenFieldEdited(t *testing.T) {
	// 只改一个字段时, 其余字段原字节保留(引号不丢)。
	original := "---\n" +
		"name: atelier\n" +
		"description: \"Atelier (工作坊) — quoted description.\"\n" +
		"level: manual\n" +
		"version: 1.2.0\n" +
		"---\n" +
		"# body\n"
	dir := t.TempDir()
	srcSkill := filepath.Join(dir, "SKILL.md")
	if err := os.WriteFile(srcSkill, []byte(original), 0o644); err != nil {
		t.Fatal(err)
	}
	parsed, err := parser.ParseCanonical(srcSkill)
	if err != nil {
		t.Fatal(err)
	}
	parsed.Level = ir.Auto // 只改 level

	dstSkill := filepath.Join(dir, "dst", "SKILL.md")
	if err := os.MkdirAll(filepath.Dir(dstSkill), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := emit.EmitCanonical(parsed, dstSkill); err != nil {
		t.Fatal(err)
	}
	out, err := os.ReadFile(dstSkill)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Contains(out, []byte(`"Atelier (工作坊) — quoted description."`)) {
		t.Fatal("description 引号被丢掉")
	}
	if !bytes.Contains(out, []byte("version: 1.2.0")) {
		t.Fatal("未变更字段 version 被改")
	}
	if !bytes.Contains(out, []byte("level: auto")) || bytes.Contains(out, []byte("level: manual")) {
		t.Fatal("level 未生效")
	}
}