// Package refs — 统一资源统计 + body 引用一致性校验(P0 #15)。
//
// 让 "skill 调 py 失败" 这种 silent failure 在 SkillBank 层面可见:
//   - sync execute(): 部署后打印资源镜像统计
//   - doctor --skill <name>: 深 check body 里引用的相对路径在镜像目录是否有对应文件
//
// 非 SkillBank 责任: LLM 真把 py 跑通(skill 作者测试范畴);
// SkillBank 责任: 文件搬齐 + 告诉你引用与文件的对应一致性。
package refs

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

// ResourceStats — deployed 后目录里的资源构成人话统计。空返 ""。
func ResourceStats(deployedSkillDir string) string {
	items, err := os.ReadDir(deployedSkillDir)
	if err != nil {
		return ""
	}
	byDir := map[string]int{}
	miscFiles := 0
	var dirNames []string
	for _, e := range items {
		name := e.Name()
		if name == "SKILL.md" || name == ".agent_overrides" || strings.HasPrefix(name, ".") {
			continue
		}
		full := filepath.Join(deployedSkillDir, name)
		if isDir(full) {
			n := countFilesRecursive(full)
			if n > 0 {
				byDir[name] = n
				dirNames = append(dirNames, name)
			}
		} else {
			miscFiles++
		}
	}
	sort.Strings(dirNames)
	var parts []string
	for _, k := range dirNames {
		parts = append(parts, fmt.Sprintf("%s/%d", k, byDir[k]))
	}
	if miscFiles > 0 {
		parts = append(parts, fmt.Sprintf("files/%d", miscFiles))
	}
	return strings.Join(parts, ", ")
}

func isDir(path string) bool {
	info, err := os.Stat(path)
	return err == nil && info.IsDir()
}

// countFilesRecursive — 递归数文件(含软链; 对应 Python _iter_files)。
func countFilesRecursive(p string) int {
	items, err := os.ReadDir(p)
	if err != nil {
		return 0
	}
	n := 0
	for _, e := range items {
		full := filepath.Join(p, e.Name())
		info, err := os.Lstat(full)
		if err != nil {
			continue
		}
		if info.Mode()&os.ModeSymlink != 0 {
			n++
		} else if info.IsDir() {
			n += countFilesRecursive(full)
		} else {
			n++
		}
	}
	return n
}

// BodyRefIssue — doctor --skill 细查时一条引用问题。
type BodyRefIssue struct {
	Severity string // "missing" | "ok"
	Ref      string // body 里找到的引用路径串
	Detail   string // 人话
}

func (i BodyRefIssue) String() string {
	mark := "·"
	switch i.Severity {
	case "missing":
		mark = "✗"
	case "ok":
		mark = "✓"
	}
	return fmt.Sprintf("%s %s: %s", mark, i.Ref, i.Detail)
}

const _subdirs = `(?:scripts|references|resources|templates|prompts|fonts|rooms|agents|protocol)`
const _exts = `(?:json|jpeg|yml|yaml|toml|html|css|csv|ottf|jpeg|jpg|png|tsv|tsx|geojson|js|ts|md|txt|py|sh|ttf|ttf)`

// relRefRe — body 里相对路径引用: 反引号/引号/( 后跟 <subdir>/<file>.<ext>。
// (Python 版的 (?!https?://|\.\./) 负向预查在 RE2 没有; 但 capture 组必须紧跟
// 前缀字符且以白名单子目录开头, https:// 与 ../ 天然不匹配, 语义等价。)
var relRefRe = regexp.MustCompile("[`\"'(](" + _subdirs + "/[A-Za-z0-9_./\\-]+\\." + _exts + ")")

// skillDirRefRe — SKILL_DIR 变量引用 "${SKILL_DIR}/scripts/foo.py"。
var skillDirRefRe = regexp.MustCompile(`\$(?:\{SKILL_DIR\}|SKILL_DIR)[/\\]+(` + _subdirs + `/[A-Za-z0-9_./\-]+\.(?:json|jpeg|yml|yaml|toml|html|css|csv|ottf|jpg|png|tsv|tsx|js|ts|md|txt|py|sh|ttf))`)

// CheckBodyRefs — check body 里相对路径引用的文件在 skillDir 内是否存在
// (防 silent failure)。不报 ../ 和 https://(scan_body_paths 管 / URL 本就外部)。
func CheckBodyRefs(body []byte, skillDir string) []BodyRefIssue {
	text := string(body)
	var issues []BodyRefIssue
	seenRefs := map[string]bool{}
	for _, rx := range []*regexp.Regexp{relRefRe, skillDirRefRe} {
		for _, m := range rx.FindAllStringSubmatch(text, -1) {
			ref := m[1]
			if seenRefs[ref] {
				continue
			}
			seenRefs[ref] = true
			target := filepath.Join(skillDir, ref)
			if _, err := os.Stat(target); err == nil {
				issues = append(issues, BodyRefIssue{"ok", ref, "在镜像目录中存在"})
			} else {
				issues = append(issues, BodyRefIssue{"missing", ref,
					fmt.Sprintf("在 skill 目录内找不到 %s", target)})
			}
		}
	}
	return issues
}