// Package scan — 自动探测本机各 Agent 的 skills 目录, 供用户确认后写入 machines.toml。
//
// 探测信号三级(按可信度):
//   - strong : 目录存在且里面至少一个子目录有 SKILL.md("装了且在用, N 个 skill")
//   - medium : 目录存在但没有任何 SKILL.md("空 skills 目录")
//   - weak   : 目录不存在但父目录存在("agent 装了, skills 目录还没建" — kimi 惰性目录)
//
// 设计约定: scan 只应在目标机器本机上跑(它探测的就是本机文件系统)。
package scan

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// CandidatePaths — 每 Agent 的候选路径(按优先级); ~ 由传入的 home 展开。
var CandidatePaths = map[string][]string{
	"ClaudeCode": {"~/.claude/skills"},
	"ZCode":      {"~/.zcode/skills"},
	"QwenWorkCN": {
		"~/.qwenworkcn/skills",     // Mac 实测布局
		"~/.qwen/skills",           // 文档口径 / 旧版
		"~/.qwenwork/skills",
		"~/.config/QwenWorkCN/skills",
	},
	"TeleAgent": {
		"~/.config/TeleAgent/skills", // Mac 实测布局
		"~/.teleagent/skills",
	},
	"Hermes":   {"~/.hermes/skills"},
	"Codex":    {"~/.codex/skills"},
	"kimi-code": {
		"~/.kimi-code/skills", // strings 实测默认 root
		"~/.kimi/skills",      // legacy
	},
}

// GlobPatterns — glob 兜底: QwenWorkCN 路径历史杂, ~/.qwen*/skills 扫一遍。
var GlobPatterns = map[string][]string{
	"QwenWorkCN": {"~/.qwen*/skills"},
}

// Candidate — 一个探测结果。
type Candidate struct {
	Agent     string
	Path      string
	Confidence string // strong | medium | weak
	Evidence  string  // 人话证据, 给确认提示用
}

// Rank — strong(0) > medium(1) > weak(2)。
func (c *Candidate) Rank() int {
	switch c.Confidence {
	case "strong":
		return 0
	case "medium":
		return 1
	case "weak":
		return 2
	}
	return 3
}

// expandHome — "~" 前缀按传入 home 展开。
func expandHome(raw, home string) string {
	if strings.HasPrefix(raw, "~") {
		return home + raw[1:]
	}
	return raw
}

// CountSkills — 目录下含 SKILL.md 的子目录数。
func CountSkills(dirPath string) int {
	items, err := os.ReadDir(dirPath)
	if err != nil {
		return 0
	}
	n := 0
	for _, e := range items {
		if e.IsDir() {
			if _, err := os.Stat(filepath.Join(dirPath, e.Name(), "SKILL.md")); err == nil {
				n++
			}
		}
	}
	return n
}

func pathExists(p string) bool {
	_, err := os.Stat(p)
	return err == nil
}

func probe(agent, raw, home string) *Candidate {
	p := expandHome(raw, home)
	if pathExists(p) {
		n := CountSkills(p)
		if n > 0 {
			return &Candidate{agent, p, "strong", fmt.Sprintf("找到 %d 个 skill", n)}
		}
		return &Candidate{agent, p, "medium", "目录存在但没有任何 SKILL.md"}
	}
	if pathExists(filepath.Dir(p)) {
		return &Candidate{agent, p, "weak", fmt.Sprintf("agent 装在 %s, skills 目录尚未创建", filepath.Dir(p))}
	}
	return nil
}

// DetectAgent — 探测单个 Agent 的候选路径, 按可信度排序返回(可为空)。
func DetectAgent(agent, home string) []Candidate {
	if home == "" {
		home, _ = os.UserHomeDir()
	}
	var found []Candidate
	for _, raw := range CandidatePaths[agent] {
		if c := probe(agent, raw, home); c != nil {
			found = append(found, *c)
		}
	}
	for _, pat := range GlobPatterns[agent] {
		// 仅取 glob 命中且不在已知候选里的(去重)
		known := map[string]bool{}
		for _, r := range CandidatePaths[agent] {
			known[expandHome(r, home)] = true
		}
		full := expandHome(pat, home)
		hits, _ := filepath.Glob(full)
		sort.Strings(hits)
		for _, p := range hits {
			if known[p] {
				continue
			}
			if c := probe(agent, p, home); c != nil {
				found = append(found, *c)
			}
		}
	}
	// strong > medium > weak; 同级保候选顺序(稳定排序)
	out := append([]Candidate{}, found...)
	sort.SliceStable(out, func(i, j int) bool {
		return out[i].Rank() < out[j].Rank()
	})
	return out
}

// DetectAll — 全部 Agent 探测结果。
func DetectAll(agentNames []string, home string) map[string][]Candidate {
	out := map[string][]Candidate{}
	for _, a := range agentNames {
		out[a] = DetectAgent(a, home)
	}
	return out
}

// PickBest — 非交互模式取最优: strong > medium > weak, 同级取第一个。
func PickBest(cands []Candidate) *Candidate {
	if len(cands) == 0 {
		return nil
	}
	best := &cands[0]
	for i := 1; i < len(cands); i++ {
		if cands[i].Rank() < best.Rank() {
			best = &cands[i]
		}
	}
	return best
}