// Package parser — canonical SKILL.md → SkillIR。
//
// 零损耗实现关键(移植合同, 对应 Python parsers/canonical.py):
//   - raw 文件按 []byte 读
//   - 字节级匹配 frontmatter 边界 `---\n ... \n---\n`(允许 \r\n)
//   - frontmatter bytes 解 YAML 拿 dict; body bytes 取边界后的全部原字节
//   - body 直接进 IR, 不 decode 不修改
package parser

import (
	"fmt"
	"os"
	"regexp"

	"github.com/ite-rate/skillbank/internal/ir"
	"gopkg.in/yaml.v3"
)

// FrontmatterRe — byte-level frontmatter 边界匹配(允许 \n 或 \r\n 行结束)。
// 子组: fm = frontmatter YAML 正文, body = 边界后全部原字节。
// (?s) 必须: 否则 `.` 不匹配 \n, 多行 body 整个匹配失败(对应 Python re.DOTALL)。
var FrontmatterRe = regexp.MustCompile(`(?s)\A---\r?\n(?P<fm>.*?)\r?\n---\r?\n(?P<body>.*)\z`)

// InvalidCanonicalError — canonical SKILL.md 必须有 `---\n...\n---\n` 边界。
type InvalidCanonicalError struct{ Path string }

func (e *InvalidCanonicalError) Error() string {
	return fmt.Sprintf("canonical SKILL.md 必须有 frontmatter 边界 `---\\n...\\n---\\n`: %s", e.Path)
}

// ParseCanonical — 读 canonical SKILL.md(整文件 bytes)解析成 SkillIR。
//
// body 为 frontmatter 边界之后的全部原字节(零损耗核心)。
// 无 frontmatter 边界 → InvalidCanonicalError;缺 name/description → RequiredFieldError。
func ParseCanonical(path string) (*ir.SkillIR, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	m := FrontmatterRe.FindSubmatchIndex(raw)
	if m == nil {
		return nil, &InvalidCanonicalError{Path: path}
	}
	fmBytes := raw[m[2]:m[3]]
	bodyBytes := raw[m[4]:m[5]]

	var fm map[string]any
	if err := yaml.Unmarshal(fmBytes, &fm); err != nil {
		return nil, fmt.Errorf("frontmatter YAML 解析失败 %s: %w", path, err)
	}
	if fm == nil {
		return nil, &InvalidCanonicalError{Path: path}
	}
	return ir.FromFrontmatterDict(fm, bodyBytes, path, fmBytes)
}

// ParseBytes — 从内存 bytes 解析(测试/golden 用; path 仅作溯源信息)。
func ParseBytes(raw []byte, path string) (*ir.SkillIR, error) {
	m := FrontmatterRe.FindSubmatchIndex(raw)
	if m == nil {
		return nil, &InvalidCanonicalError{Path: path}
	}
	fmBytes := raw[m[2]:m[3]]
	bodyBytes := raw[m[4]:m[5]]
	var fm map[string]any
	if err := yaml.Unmarshal(fmBytes, &fm); err != nil {
		return nil, fmt.Errorf("frontmatter YAML 解析失败 %s: %w", path, err)
	}
	if fm == nil {
		return nil, &InvalidCanonicalError{Path: path}
	}
	return ir.FromFrontmatterDict(fm, bodyBytes, path, fmBytes)
}