// canonical emitter — SkillIR → canonical SKILL.md(写回中央仓)。
//
// 零损耗实现关键(对应 Python emitters/canonical.py):
//   - body bytes 直接拼到 frontmatter 之后, 不 decode/encode/normalize
//   - 有原始 frontmatter → 字段级透传(未变更字段原字节保留)
//   - 无原始 frontmatter(如 import 新建)→ 全量 dump
//
// roundtrip zero-loss: parse→IR0 → EmitCanonical → parse → IR1,
// IR1.Body == IR0.Body 字节等值。
package emit

import (
	"os"
	"strings"

	"github.com/ite-rate/skillbank/internal/ir"
)

// EmitCanonical — 把 IR 写成 canonical SKILL.md。
// 父目录需存在, 不自动建目录(与 Python 一致, add/importer 层负责建)。
func EmitCanonical(in *ir.SkillIR, targetPath string) error {
	fmBytes, err := canonicalFrontmatterBytes(in)
	if err != nil {
		return err
	}
	out := append([]byte("---\n"), fmBytes...)
	out = append(out, []byte("---\n")...)
	out = append(out, in.Body...)
	return os.WriteFile(targetPath, out, 0o644)
}

// CanonicalSkillMDBytes — 不落盘版本(add/import 内存预览、测试用)。
func CanonicalSkillMDBytes(in *ir.SkillIR) ([]byte, error) {
	fmBytes, err := canonicalFrontmatterBytes(in)
	if err != nil {
		return nil, err
	}
	out := append([]byte("---\n"), fmBytes...)
	out = append(out, []byte("---\n")...)
	return append(out, in.Body...), nil
}

func canonicalFrontmatterBytes(in *ir.SkillIR) ([]byte, error) {
	fm := in.ToFrontmatterDict()
	if in.FMRaw != nil && in.FMOrig != nil {
		edited, err := EditFrontmatterFields(string(in.FMRaw), in.FMOrig, fm,
			ir.CanonicalFieldOrder)
		if err != nil {
			return nil, err
		}
		return []byte(strings.TrimRight(edited, "\n") + "\n"), nil
	}
	return DumpMap(fm, ir.CanonicalFieldOrder)
}