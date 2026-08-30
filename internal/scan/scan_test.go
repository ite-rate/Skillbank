// scan 探测测试(移植 tests/test_scan.py 9 条, 语义等价)。
//
// 用假 home 模拟各安装状态: strong/medium/weak、QwenWorkCN 候选序、glob 怪路径兜底。
package scan_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/ite-rate/skillbank/internal/scan"
)

func fakeHome(t *testing.T) string {
	t.Helper()
	home := filepath.Join(t.TempDir(), "home")
	if err := os.MkdirAll(home, 0o755); err != nil {
		t.Fatal(err)
	}
	return home
}

func mkSkill(t *testing.T, base, name string) {
	t.Helper()
	d := filepath.Join(base, name)
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(d, "SKILL.md"),
		[]byte("---\nname: x\ndescription: x\n---\nbody\n"), 0o644); err != nil {
		t.Fatal(err)
	}
}

// --- 探测分级 ---

func TestDetectStrongWithSkills(t *testing.T) {
	home := fakeHome(t)
	skills := filepath.Join(home, ".claude", "skills")
	mkSkill(t, skills, "agora")
	cands := scan.DetectAgent("ClaudeCode", home)
	if len(cands) != 1 {
		t.Fatalf("cands: %v", cands)
	}
	c := cands[0]
	if c.Confidence != "strong" || c.Path != skills {
		t.Fatalf("candidate: %+v", c)
	}
	if !strings.Contains(c.Evidence, "1 个 skill") {
		t.Fatalf("evidence: %q", c.Evidence)
	}
}

func TestDetectMediumEmptyDir(t *testing.T) {
	home := fakeHome(t)
	if err := os.MkdirAll(filepath.Join(home, ".claude", "skills"), 0o755); err != nil {
		t.Fatal(err)
	}
	cands := scan.DetectAgent("ClaudeCode", home)
	if len(cands) == 0 || cands[0].Confidence != "medium" {
		t.Fatalf("cands: %v", cands)
	}
}

func TestDetectWeakLazyDir(t *testing.T) {
	// agent 装了(父目录在)但 skills 目录没建 — kimi 场景。
	home := fakeHome(t)
	if err := os.MkdirAll(filepath.Join(home, ".kimi-code"), 0o755); err != nil {
		t.Fatal(err)
	}
	cands := scan.DetectAgent("kimi-code", home)
	if len(cands) != 1 {
		t.Fatalf("cands: %v", cands)
	}
	c := cands[0]
	if c.Confidence != "weak" || c.Path != filepath.Join(home, ".kimi-code", "skills") {
		t.Fatalf("candidate: %+v", c)
	}
	if !strings.Contains(c.Evidence, "尚未创建") {
		t.Fatalf("evidence: %q", c.Evidence)
	}
}

func TestDetectNotInstalledReturnsEmpty(t *testing.T) {
	home := fakeHome(t)
	if cands := scan.DetectAgent("Hermes", home); len(cands) != 0 {
		t.Fatalf("未装应空: %v", cands)
	}
}

func TestQwenworkcnPrefersQwenworkcn(t *testing.T) {
	// 同时有 .qwenworkcn(在用) 和 .qwen(旧), 排序优先 .qwenworkcn。
	home := fakeHome(t)
	mkSkill(t, filepath.Join(home, ".qwenworkcn", "skills"), "dws")
	mkSkill(t, filepath.Join(home, ".qwen", "skills"), "old")
	cands := scan.DetectAgent("QwenWorkCN", home)
	if len(cands) == 0 || cands[0].Path != filepath.Join(home, ".qwenworkcn", "skills") {
		t.Fatalf("cands: %v", cands)
	}
}

func TestQwenworkcnWeirdPathGotByGlob(t *testing.T) {
	// 怪路径(~/.qwenworkcn-skills)也能被 glob 兜住。
	home := fakeHome(t)
	weird := filepath.Join(home, ".qwenworkcn-skills", "skills")
	mkSkill(t, weird, "dws")
	cands := scan.DetectAgent("QwenWorkCN", home)
	found := false
	for _, c := range cands {
		if c.Path == weird {
			found = true
		}
	}
	if !found {
		t.Fatalf("glob 应兜住怪路径: %v", cands)
	}
}

func TestPickBestPrefersStrong(t *testing.T) {
	home := fakeHome(t)
	mkSkill(t, filepath.Join(home, ".qwenworkcn", "skills"), "dws") // strong
	if err := os.MkdirAll(filepath.Join(home, ".qwen"), 0o755); err != nil {
		t.Fatal(err)
	} // weak(.qwen/skills 未建)
	best := scan.PickBest(scan.DetectAgent("QwenWorkCN", home))
	if best == nil || best.Confidence != "strong" ||
		best.Path != filepath.Join(home, ".qwenworkcn", "skills") {
		t.Fatalf("best: %+v", best)
	}
}