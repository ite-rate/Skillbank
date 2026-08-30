// Golden fixture 消费测试 — testdata/golden 字节合同。
//
// 合同来源(历史): 移植期由 Python 参考实现生成 expected.md, 语义已锁定进
// fixture;Go 是唯一实现后 fixture 即权威。本测试证 Go 实现满足同一合同:
//   - byte_exact case: Go 产物与 expected.md 字节全等
//     (字段级透传路径 — 跨机 git diff 零噪音的硬保证)
//   - semantic case: body 字节等值 + frontmatter 语义等值 + keep/drop 行合同
//     (全量 dump 路径 — dump 排版是已声明的自由度)
package emit_test

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
	"testing"

	"github.com/ite-rate/skillbank/internal/emit"
	"github.com/ite-rate/skillbank/internal/ir"
	"github.com/ite-rate/skillbank/internal/parser"
	"gopkg.in/yaml.v3"
)

var goldenBodyRe = regexp.MustCompile(`(?s)\A---\r?\n.*?\r?\n---\r?\n(.*)\z`)

func goldenDir(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for {
		candidate := filepath.Join(dir, "testdata", "golden")
		if info, err := os.Stat(candidate); err == nil && info.IsDir() {
			return candidate
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatal("找不到 testdata/golden")
		}
		dir = parent
	}
}

type goldenMeta struct {
	Check     string            `json:"check"`
	Edit      map[string]string `json:"edit"`
	KeepLines []string          `json:"keep_lines"`
	DropLines []string          `json:"drop_lines"`
	FreshIR   bool              `json:"fresh_ir"`
}

type goldenCase struct {
	name     string
	dir      string
	meta     goldenMeta
	input    []byte // nil = fresh_ir
	expected []byte
}

func loadGoldenCases(t *testing.T) []goldenCase {
	t.Helper()
	root := goldenDir(t)
	entries, err := os.ReadDir(root)
	if err != nil {
		t.Fatal(err)
	}
	var cases []goldenCase
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		dir := filepath.Join(root, e.Name())
		rawMeta, err := os.ReadFile(filepath.Join(dir, "meta.json"))
		if err != nil {
			t.Fatalf("case %s: %v", e.Name(), err)
		}
		var meta goldenMeta
		if err := json.Unmarshal(rawMeta, &meta); err != nil {
			t.Fatalf("case %s meta.json: %v", e.Name(), err)
		}
		c := goldenCase{name: e.Name(), dir: dir, meta: meta}
		if !meta.FreshIR {
			c.input, err = os.ReadFile(filepath.Join(dir, "input.md"))
			if err != nil {
				t.Fatalf("case %s input.md: %v", e.Name(), err)
			}
		}
		c.expected, err = os.ReadFile(filepath.Join(dir, "expected.md"))
		if err != nil {
			t.Fatalf("case %s expected.md: %v", e.Name(), err)
		}
		cases = append(cases, c)
	}
	if len(cases) < 7 {
		t.Fatalf("golden case 应 ≥7 个, got %d", len(cases))
	}
	return cases
}

// goldenGoEmit — 按 case 用 Go 实现重走 parse→(edit)→EmitCanonical。
func goldenGoEmit(t *testing.T, c goldenCase) []byte {
	t.Helper()
	scratch := t.TempDir()
	var in *ir.SkillIR
	if c.meta.FreshIR {
		in = &ir.SkillIR{
			Name:        "imported-demo",
			Description: "An imported skill with 中文 desc.",
			Body:        []byte("## imported body\r\nCRLF kept\n"),
			Level:       ir.Auto,
			Requires:    []string{"image_generation"},
		}
	} else {
		src := filepath.Join(scratch, "SKILL.md")
		if err := os.WriteFile(src, c.input, 0o644); err != nil {
			t.Fatal(err)
		}
		parsed, err := parser.ParseCanonical(src)
		if err != nil {
			t.Fatalf("case %s parse: %v", c.name, err)
		}
		in = parsed
	}
	if lvl, ok := c.meta.Edit["set_level"]; ok {
		in.Level = ir.Level(lvl)
	}
	dst := filepath.Join(scratch, "out", "SKILL.md")
	if err := os.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := emit.EmitCanonical(in, dst); err != nil {
		t.Fatalf("case %s emit: %v", c.name, err)
	}
	out, err := os.ReadFile(dst)
	if err != nil {
		t.Fatal(err)
	}
	return out
}

func goldenBody(t *testing.T, raw []byte) []byte {
	t.Helper()
	m := goldenBodyRe.FindSubmatch(raw)
	if m == nil {
		t.Fatalf("golden 产物缺 frontmatter 边界: %q", raw)
	}
	return m[1]
}

func goldenFM(t *testing.T, raw []byte) map[string]any {
	t.Helper()
	m := regexp.MustCompile(`(?s)\A---\r?\n(.*?)\r?\n---\r?\n`).FindSubmatch(raw)
	if m == nil {
		t.Fatalf("golden 产物缺 frontmatter 边界: %q", raw)
	}
	var fm map[string]any
	if err := yaml.Unmarshal(m[1], &fm); err != nil {
		t.Fatalf("golden frontmatter YAML 解析失败: %v\n%s", err, m[1])
	}
	return fm
}

func TestGoldenByteExact(t *testing.T) {
	// byte_exact: Go 产物与 Python 基准字节全等(字段级透传路径的硬合同)。
	n := 0
	for _, c := range loadGoldenCases(t) {
		if c.meta.Check != "byte_exact" {
			continue
		}
		out := goldenGoEmit(t, c)
		if !bytes.Equal(out, c.expected) {
			t.Errorf("case %s: Go 产物与 golden 期望字节不等\nGo 期望等值于 Python:\n--- go ---\n%q\n--- expected ---\n%q",
				c.name, out, c.expected)
		}
		n++
	}
	if n < 5 {
		t.Fatalf("byte_exact case 应 ≥5 个, got %d", n)
	}
}

func TestGoldenSemantic(t *testing.T) {
	// semantic: body 字节等值 + frontmatter 语义等值 + keep/drop 行合同。
	for _, c := range loadGoldenCases(t) {
		if c.meta.Check != "semantic" {
			continue
		}
		out := goldenGoEmit(t, c)

		// body 字节等值(零损耗)
		if !bytes.HasSuffix(out, goldenBody(t, c.expected)) {
			t.Errorf("case %s: body 零损耗破", c.name)
		}
		// frontmatter 语义等值
		fmOut := goldenFM(t, out)
		fmExp := goldenFM(t, c.expected)
		if !emit.YAMLMapEqual(fmOut, fmExp) {
			t.Errorf("case %s: frontmatter 语义不等\nGo: %v\n期望: %v", c.name, fmOut, fmExp)
		}
		// keep/drop lines 合同
		for _, keep := range c.meta.KeepLines {
			if !bytes.Contains(out, []byte(keep)) {
				t.Errorf("case %s: 未保留行 %q", c.name, keep)
			}
		}
		for _, drop := range c.meta.DropLines {
			if bytes.Contains(out, []byte(drop)) {
				t.Errorf("case %s: 未删行 %q", c.name, drop)
			}
		}
	}
}

func TestGoldenExpectedParses(t *testing.T) {
	// 所有 expected.md 本身可被 Go parser 接受(不是坏 fixture)。
	for _, c := range loadGoldenCases(t) {
		parsed, err := parser.ParseBytes(c.expected, filepath.Join(c.dir, "expected.md"))
		if err != nil {
			t.Errorf("case %s: expected.md 解析失败: %v", c.name, err)
			continue
		}
		if parsed.Name == "" {
			t.Errorf("case %s: expected.md 缺 name", c.name)
		}
	}
}