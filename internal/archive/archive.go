// Package archive — 长时间不用但未来可能用的 skill 归档/恢复。
//
// 归档 = mv skills/<name>/ → skills/.archive/<name>/ + 清已部署副本 + manifest 标记。
//   - sync 不扫 .archive/(不部署)
//   - list 默认不显示归档; --archived 看清单
//   - canonical 仍在 git 里(100% 可恢复)
//   - 恢复: skillbank unarchive <name> → 移回 skills/ + set-level manual
//
// 与 disable 的区别:
//   disable : skill 仍在 skills/ 里, list 显示, sync 不推但可见 — "出了问题被下架"
//   archive : skill 移到 .archive/, list 默认不显示 — "暂存将来可能用"
package archive

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/ite-rate/skillbank/internal/emit"
	"github.com/ite-rate/skillbank/internal/ir"
	"github.com/ite-rate/skillbank/internal/manifest"
	"github.com/ite-rate/skillbank/internal/parser"
)

// DirName — 归档区目录名(skills/ 下, sync 不扫)。
const DirName = ".archive"

func archiveRoot(repoRoot string) string {
	return filepath.Join(repoRoot, "skills", DirName)
}

func skillExists(repoRoot, name string) bool {
	_, err := os.Stat(filepath.Join(repoRoot, "skills", name, "SKILL.md"))
	return err == nil
}

func archivedExists(repoRoot, name string) bool {
	_, err := os.Stat(filepath.Join(archiveRoot(repoRoot), name, "SKILL.md"))
	return err == nil
}

// ArchiveSkill — 归档 skill: mv 到 .archive/ + 清已部署副本(走 manifest 删除链)。
// 返回人话结果描述。
func ArchiveSkill(repoRoot, name string, m *manifest.DeploymentsManifest,
	machine string) (string, error) {
	if !skillExists(repoRoot, name) {
		if archivedExists(repoRoot, name) {
			return fmt.Sprintf("already archived: %s", name), nil
		}
		return fmt.Sprintf("canonical 不存在: skills/%s/", name), nil
	}

	src := filepath.Join(repoRoot, "skills", name)
	dstDir := archiveRoot(repoRoot)
	if err := os.MkdirAll(dstDir, 0o755); err != nil {
		return "", err
	}
	dst := filepath.Join(dstDir, name)

	if _, err := os.Lstat(dst); err == nil {
		// 归档区已有同名(可能旧归档残留), 覆盖
		if err := os.RemoveAll(dst); err != nil {
			return "", err
		}
	}
	if err := os.Rename(src, dst); err != nil {
		return "", err
	}

	// 清已部署副本(走 manifest 删除链)
	var notes []string
	if m != nil {
		actions := m.DeleteLocal(name, machine, "", false)
		if len(actions) > 0 {
			notes = append(notes, fmt.Sprintf("清本机副本 %d 个", len(actions)))
		}
		if n := m.MarkPendingDeletion(name, machine); n > 0 {
			notes = append(notes, fmt.Sprintf("其它机器 %d 个标 pending", n))
		}
		if err := m.Save(""); err != nil {
			return "", err
		}
	}

	out := fmt.Sprintf("已归档 %s → skills/.archive/%s", name, name)
	if len(notes) > 0 {
		out += "(" + strings.Join(notes, ", ") + ")"
	}
	return out, nil
}

// UnarchiveSkill — 恢复归档 skill: mv 回 skills/ + set-level manual(默认不自动触发)。
// 返回人话结果描述。
func UnarchiveSkill(repoRoot, name string) (string, error) {
	if !archivedExists(repoRoot, name) {
		return fmt.Sprintf("归档区不存在: skills/.archive/%s/", name), nil
	}

	src := filepath.Join(archiveRoot(repoRoot), name)
	dst := filepath.Join(repoRoot, "skills", name)

	if _, err := os.Stat(dst); err == nil {
		return fmt.Sprintf("skills/%s/ 已存在(同名冲突, 先 rm 或 rename 再 unarchive)", name), nil
	}

	if err := os.Rename(src, dst); err != nil {
		return "", err
	}

	// set-level manual(恢复后默认不自动触发, 你审过再改 auto)
	skillMD := filepath.Join(dst, "SKILL.md")
	in, err := parser.ParseCanonical(skillMD)
	if err != nil {
		return "", err
	}
	if in.Level != ir.Manual {
		old := string(in.Level)
		in.Level = ir.Manual
		if err := emit.EmitCanonical(in, skillMD); err != nil {
			return "", err
		}
		return fmt.Sprintf("已恢复 %s ← .archive, level: %s → manual(审过再 set-level auto)", name, old), nil
	}
	return fmt.Sprintf("已恢复 %s ← .archive(level 已是 manual)", name), nil
}

// ListArchived — 归档区 skill 名列表(字典序)。
func ListArchived(repoRoot string) []string {
	root := archiveRoot(repoRoot)
	items, err := os.ReadDir(root)
	if err != nil {
		return nil
	}
	var out []string
	for _, e := range items {
		if !e.IsDir() {
			continue
		}
		if _, err := os.Stat(filepath.Join(root, e.Name(), "SKILL.md")); err == nil {
			out = append(out, e.Name())
		}
	}
	sort.Strings(out)
	return out
}
// SkillExists — canonical skills/<name>/SKILL.md 是否存在。
func SkillExists(repoRoot, name string) bool { return skillExists(repoRoot, name) }

// ArchivedExists — 归档区 skills/.archive/<name>/SKILL.md 是否存在。
func ArchivedExists(repoRoot, name string) bool { return archivedExists(repoRoot, name) }
