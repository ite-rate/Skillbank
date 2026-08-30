// Package manifest — manifests/deployments.json 读写 + 删除链。
//
// 移植合同(对应 Python manifest.py):
//   - schema v1: {version, records:[DeployRecord...]}
//   - JSON 字节兼容: 字段顺序 = DeployRecord 声明序, indent=2, 非ASCII不转义
//     (ensure_ascii=False), 尾 "\n" — 否则跨机 git diff 全是噪音
//   - 原子写(tmp + rename)防写坏
//
// 删除链(决策 5/6):
//  1. rm <name> / 改 level=disable:
//     - 本机记录的 deploy_path 直接删(只删 manifest 记录的; 用户手放/内置不碰)
//     - 其它机器记录标 pending_deletion=true, 那台机器下次 sync 执行删除
//  2. skill 从 manifest 消失后 canonical 仍保留(disable 时), git 里可恢复
package manifest

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// ManifestVersion — schema 版本。
const ManifestVersion = 1

func nowISO() string {
	return time.Now().UTC().Format("2006-01-02T15:04:05Z")
}

// DeployRecord — 单条部署记录。
// 字段顺序即 JSON 输出序(与 Python dataclass 声明序逐字段对齐 — 字节兼容)。
type DeployRecord struct {
	Skill          string `json:"skill"`
	Machine        string `json:"machine"`
	Agent          string `json:"agent"`
	DeployPath     string `json:"deploy_path"`     // 绝对路径(emitter 落盘时展开)
	DeployedAt     string `json:"deployed_at"`     // ISO8601 UTC
	Method         string `json:"method"`           // cp | ln(skipped 不入 manifest)
	IrHash         string `json:"ir_hash"`          // body sha256(跨机零损耗验证)
	Note           string `json:"note"`
	PendingDeletion bool   `json:"pending_deletion"` // 跨机删除标记
}

// Key — (skill, machine, agent) 唯一键。
type Key struct {
	Skill, Machine, Agent string
}

func (r *DeployRecord) Key() Key {
	return Key{r.Skill, r.Machine, r.Agent}
}

// DeploymentsManifest — manifest 全表。
type DeploymentsManifest struct {
	Records []DeployRecord
	Path    string // 落盘位置; 空 = 内存态(测试用)
}

// Load — 读 manifest; 不存在返回空表。
func Load(path string) (*DeploymentsManifest, error) {
	m := &DeploymentsManifest{Records: nil, Path: path}
	raw, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return m, nil
	}
	if err != nil {
		return nil, err
	}
	var doc struct {
		Version int            `json:"version"`
		Records []DeployRecord `json:"records"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		return nil, fmt.Errorf("manifest 解析失败 %s: %w", path, err)
	}
	if doc.Version != ManifestVersion {
		return nil, fmt.Errorf("manifest version %d != supported %d: %s", doc.Version, ManifestVersion, path)
	}
	m.Records = doc.Records
	return m, nil
}

// Save — 原子写(tmp + rename)。
// 字节合同: 与 Python json.dumps(ensure_ascii=False, indent=2) + "\n" 全等。
func (m *DeploymentsManifest) Save(path string) error {
	p := path
	if p == "" {
		p = m.Path
	}
	if p == "" {
		return fmt.Errorf("no manifest path given")
	}
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		return err
	}
	doc := struct {
		Version int            `json:"version"`
		Records []DeployRecord `json:"records"`
	}{ManifestVersion, m.Records}
	if doc.Records == nil {
		doc.Records = []DeployRecord{}
	}
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false) // ensure_ascii=False 等价(非ASCII直出 + URL 不转义)
	enc.SetIndent("", "  ")  // indent=2
	if err := enc.Encode(doc); err != nil {
		return err
	}
	// Encoder 自带尾 "\n", 与 Python json.dumps(...) + "\n" 单尾换行等值, 不再补
	out := buf.Bytes()
	tmp := strings.TrimSuffix(p, ".json") + ".json.tmp"
	if err := os.WriteFile(tmp, out, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, p)
}

// Find — 按 skill(可选 machine/agent 过滤)查记录。
func (m *DeploymentsManifest) Find(skill string, machine, agent string) []DeployRecord {
	var out []DeployRecord
	for _, r := range m.Records {
		if r.Skill != skill {
			continue
		}
		if machine != "" && r.Machine != machine {
			continue
		}
		if agent != "" && r.Agent != agent {
			continue
		}
		out = append(out, r)
	}
	return out
}

// Skills — manifest 里的 skill 名(首次出现序)。
func (m *DeploymentsManifest) Skills() []string {
	seen := map[string]bool{}
	var out []string
	for _, r := range m.Records {
		if !seen[r.Skill] {
			seen[r.Skill] = true
			out = append(out, r.Skill)
		}
	}
	return out
}

// Upsert — 按 (skill, machine, agent) 替换或追加; 新记录补 deployed_at。
func (m *DeploymentsManifest) Upsert(rec DeployRecord) {
	for i, r := range m.Records {
		if r.Key() == rec.Key() {
			m.Records[i] = rec
			return
		}
	}
	if rec.DeployedAt == "" {
		rec.DeployedAt = nowISO()
	}
	m.Records = append(m.Records, rec)
}

// RemoveRecord — 删记录(不删盘上文件); 返回是否删到。
func (m *DeploymentsManifest) RemoveRecord(skill, machine, agent string) bool {
	for i, r := range m.Records {
		if r.Key() == (Key{skill, machine, agent}) {
			m.Records = append(m.Records[:i], m.Records[i+1:]...)
			return true
		}
	}
	return false
}

// MarkPendingDeletion — rm/disable 时: 其它机器的记录标 pending_deletion=true。
// 本机(exceptMachine)记录由 DeleteLocal 直接处理, 不标 pending。返回标记条数。
func (m *DeploymentsManifest) MarkPendingDeletion(skill, exceptMachine string) int {
	n := 0
	for i, r := range m.Records {
		if r.Skill == skill && exceptMachine != "" && r.Machine != exceptMachine {
			if !r.PendingDeletion {
				m.Records[i].PendingDeletion = true
				n++
			}
		}
	}
	return n
}

// DeleteLocal — 删除链·本机段: 删盘上 deploy_path + 清 manifest 记录。
//
// 只删 manifest 记录的路径(用户手放/内置 skill 从不入库, 天然不碰)。
// cp 记录 deploy_path 指 <dir>/SKILL.md → 删 skill 目录; ln 记录指软链目录本身。
// dryRun 只报告不动盘不清记录。返回删除的动作描述列表。
func (m *DeploymentsManifest) DeleteLocal(skill, machine, agent string, dryRun bool) []string {
	var actions []string
	recs := append([]DeployRecord{}, m.Find(skill, machine, agent)...)
	for _, r := range recs {
		targetDir := r.DeployPath
		if filepath.Base(targetDir) == "SKILL.md" {
			targetDir = filepath.Dir(targetDir)
		}
		if dryRun {
			actions = append(actions, fmt.Sprintf("WOULD DELETE %s (%s, %s)", targetDir, r.Agent, r.Method))
			continue
		}
		switch removeSkillDir(targetDir) {
		case removedSymlink:
			actions = append(actions, fmt.Sprintf("unlinked %s (%s, %s)", targetDir, r.Agent, r.Method))
		case removedDir:
			actions = append(actions, fmt.Sprintf("deleted %s (%s, %s)", targetDir, r.Agent, r.Method))
		case alreadyGone:
			actions = append(actions, fmt.Sprintf("already gone %s (%s, %s)", targetDir, r.Agent, r.Method))
		}
		m.RemoveRecord(skill, machine, r.Agent)
	}
	return actions
}

// ProcessPendingDeletions — 删除链·跨机段: 本机 sync 时执行别的机器标来的
// pending_deletion(删本机 deploy_path + 清记录)。返回动作描述列表。
func (m *DeploymentsManifest) ProcessPendingDeletions(machine string, dryRun bool) []string {
	var actions []string
	recs := append([]DeployRecord{}, m.Records...)
	for _, r := range recs {
		if !r.PendingDeletion || r.Machine != machine {
			continue
		}
		targetDir := r.DeployPath
		if filepath.Base(targetDir) == "SKILL.md" {
			targetDir = filepath.Dir(targetDir)
		}
		if dryRun {
			actions = append(actions, fmt.Sprintf("WOULD DELETE(pending) %s (%s)", targetDir, r.Agent))
			continue
		}
		switch removeSkillDir(targetDir) {
		case removedSymlink:
			actions = append(actions, fmt.Sprintf("unlinked(pending) %s (%s)", targetDir, r.Agent))
		case removedDir:
			actions = append(actions, fmt.Sprintf("deleted(pending) %s (%s)", targetDir, r.Agent))
		case alreadyGone:
			actions = append(actions, fmt.Sprintf("already gone(pending) %s (%s)", targetDir, r.Agent))
		}
		m.RemoveRecord(r.Skill, r.Machine, r.Agent)
	}
	return actions
}

type removeOutcome int

const (
	alreadyGone removeOutcome = iota
	removedSymlink
	removedDir
)

// removeSkillDir — 删软链或 skill 目录(与 Python is_symlink→unlink / rmtree 对齐)。
func removeSkillDir(path string) removeOutcome {
	info, err := os.Lstat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return alreadyGone
		}
		return alreadyGone
	}
	if info.Mode()&os.ModeSymlink != 0 {
		if os.Remove(path) == nil {
			return removedSymlink
		}
		return alreadyGone
	}
	if info.IsDir() {
		if os.RemoveAll(path) == nil {
			return removedDir
		}
		return alreadyGone
	}
	// deploy_path 指向普通文件(异常形态): 删文件当目录已删
	if os.Remove(path) == nil {
		return removedDir
	}
	return alreadyGone
}

// CheckConsistency — 盘上文件 vs manifest 记录对账(doctor 用); 返回差异描述。
func (m *DeploymentsManifest) CheckConsistency() []string {
	var issues []string
	seenKeys := map[Key]bool{}
	for _, r := range m.Records {
		k := r.Key()
		if seenKeys[k] {
			issues = append(issues, fmt.Sprintf("duplicate record %s/%s/%s", k.Skill, k.Machine, k.Agent))
		}
		seenKeys[k] = true
		if !r.PendingDeletion {
			if _, err := os.Stat(r.DeployPath); err != nil {
				issues = append(issues, fmt.Sprintf("recorded but missing on disk: %s (%s@%s/%s)",
					r.DeployPath, r.Skill, r.Machine, r.Agent))
			}
		}
	}
	return issues
}