// Package ir — canonical SKILL.md 的语义化中间表示。
//
// 移植合同(对应 Python ir.py, 语义逐条等价):
//   - Body 是 []byte 零损耗硬约束: parser/emitter 全程字节流转, 不 decode 不 normalize
//   - FMRaw/FMOrig 保 frontmatter 原始字节与原始 dict, emitter 据此做字段级透传
//     (未变更字段原字节保留, 引号/顺序不漂)
//
// Roundtrip 零损耗含义: parse → IR0 → emit → parse → IR1, IR1.Body == IR0.Body 字节等值;
// frontmatter 往返允许 dict 等值(序化格式可漂, body 不漂)。
package ir

import (
	"crypto/sha256"
	"encoding/hex"
)

// Level — skill 分级(决策 4.4)。
type Level string

const (
	// Auto 稳定高频, 同步 + 允许模型自动触发
	Auto Level = "auto"
	// Manual 稳定低频, 同步 + 禁止自动触发
	Manual Level = "manual"
	// Experimental 实验中, 同步 + 禁止自动触发(同 manual)
	Experimental Level = "experimental"
	// Disable 暂停, 不同步 + 清理已部署副本(canonical 保留以便恢复)
	Disable Level = "disable"
)

// ValidLevel — canonical frontmatter level 合法值。
var ValidLevels = []Level{Auto, Manual, Experimental, Disable}

func (l Level) Valid() bool {
	switch l {
	case Auto, Manual, Experimental, Disable:
		return true
	}
	return false
}

// AllowsSync — disable 不参与同步, 只保留 canonical。
func (l Level) AllowsSync() bool { return l != Disable }

// AllowsAutoTrigger — manual/experimental/disable 都禁止模型自动触发。
func (l Level) AllowsAutoTrigger() bool { return l == Auto }

// SkillIR — canonical SKILL.md 的 IR。
//
// 可选字段用 *string(非 string): Python 原版用 None 区分「缺省」与「空串」
// (`description_zh: ''` 是存在且值为空, 透传时必须保留), Go string 合并两者
// 会把显式空串误判为删除 → 字节漂移。
type SkillIR struct {
	Name        string
	Description string
	Body        []byte   // 零损耗核心: 原字节, 不 decode
	Level       Level    // 缺省 auto(FromFrontmatterDict 填)
	NativeAgent *string  // nil = 无
	Requires    []string // 能力标签, 仅文档标注; 空(含显式 requires: [])不输出, 对应 Python `if self.requires:`
	DescZH      *string  // 双语 desc(_zh; TeleAgent 镜像成 _cn)
	NameZH      *string  // 双语 name
	Version     *string
	License     *string
	Source      *string // 来源 provenance(git URL); nil = 本地导入/未知
	SourcePath  string    // parser 溯源
	// 字段级透传: parser 保留 frontmatter 原始字节 + 原始 dict。
	// FMRaw 为 nil(如 import 新建)时 emitter 走全量 dump。
	FMRaw  []byte         // frontmatter 原始文本(不含 --- 边界); nil = 无
	FMOrig map[string]any // 原始解析出的 frontmatter dict; FMRaw 非 nil 时必有
}

// BodyHash — body sha256(manifest ir_hash 用, 跨机零损耗验证)。
func (ir *SkillIR) BodyHash() string {
	sum := sha256.Sum256(ir.Body)
	return "sha256:" + hex.EncodeToString(sum[:])
}

// ToFrontmatterDict — canonical frontmatter 字段 dict(emit 回 SKILL.md 用)。
// 字段顺序即声明序(新增字段 dump 时保持此序)。
func (ir *SkillIR) ToFrontmatterDict() map[string]any {
	fm := map[string]any{
		"name":        ir.Name,
		"description": ir.Description,
		"level":       string(ir.Level),
	}
	if ir.NativeAgent != nil {
		fm["native_agent"] = *ir.NativeAgent
	}
	if len(ir.Requires) > 0 {
		fm["requires"] = append([]string{}, ir.Requires...)
	}
	if ir.DescZH != nil {
		fm["description_zh"] = *ir.DescZH
	}
	if ir.NameZH != nil {
		fm["name_zh"] = *ir.NameZH
	}
	if ir.Version != nil {
		fm["version"] = *ir.Version
	}
	if ir.License != nil {
		fm["license"] = *ir.License
	}
	if ir.Source != nil {
		fm["source"] = *ir.Source
	}
	return fm
}

// CanonicalFieldOrder — canonical 字段产出序(新增字段 dump 追加序, 对应 Python dict 声明序)。
var CanonicalFieldOrder = []string{
	"name", "description", "level", "native_agent", "requires",
	"description_zh", "name_zh", "version", "license", "source",
}

// FromFrontmatterDict — 从 frontmatter dict + body bytes 构建 IR。
// 允许未识别字段(留作 leftover, 不报错)。fmRaw 非 nil 时存入供字段级透传。
// 缺 name/description 返回错误(canonical 必填)。
func FromFrontmatterDict(fm map[string]any, body []byte, sourcePath string,
	fmRaw []byte) (*SkillIR, error) {
	name, _ := fm["name"].(string)
	desc, _ := fm["description"].(string)
	if name == "" {
		return nil, &RequiredFieldError{Field: "name"}
	}
	if desc == "" {
		return nil, &RequiredFieldError{Field: "description"}
	}

	level := Auto
	if lv, ok := fm["level"]; ok {
		if s, ok := lv.(string); ok {
			level = Level(s)
		}
	}

	ir := &SkillIR{
		Name:        name,
		Description: desc,
		Body:        body,
		Level:       level,
		SourcePath:  sourcePath,
	}
	if v, ok := fm["native_agent"]; ok {
		ir.NativeAgent = strPtr(v)
	}
	if req, ok := fm["requires"]; ok {
		if list, ok := req.([]any); ok {
			for _, e := range list {
				if s, ok := e.(string); ok {
					ir.Requires = append(ir.Requires, s)
				}
			}
		}
	}
	if v, ok := fm["description_zh"]; ok {
		ir.DescZH = strPtr(v)
	}
	if v, ok := fm["name_zh"]; ok {
		ir.NameZH = strPtr(v)
	}
	if v, ok := fm["version"]; ok {
		ir.Version = strPtr(v)
	}
	if v, ok := fm["license"]; ok {
		ir.License = strPtr(v)
	}
	if v, ok := fm["source"]; ok {
		ir.Source = strPtr(v)
	}
	if fmRaw != nil {
		ir.FMRaw = fmRaw
		fmOrig := make(map[string]any, len(fm))
		for k, v := range fm {
			fmOrig[k] = v
		}
		ir.FMOrig = fmOrig
	}
	return ir, nil
}

// RequiredFieldError — frontmatter 缺必填字段。
type RequiredFieldError struct{ Field string }

func (e *RequiredFieldError) Error() string {
	return "frontmatter 缺必填字段: " + e.Field
}

// strPtr — frontmatter 值 → *string(非 string 值视为缺省; 实际数据都是字符串)。
func strPtr(v any) *string {
	if s, ok := v.(string); ok {
		return &s
	}
	return nil
}