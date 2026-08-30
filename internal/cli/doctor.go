// doctor 子命令 — 环境体检(配置/路径/manifest/canonical/git)。
// (移植 cli.py _cmd_doctor/_doctor_skill_check)
package cli

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/ite-rate/skillbank/internal/identity"
	"github.com/ite-rate/skillbank/internal/manifest"
	"github.com/ite-rate/skillbank/internal/parser"
	"github.com/ite-rate/skillbank/internal/refs"
	"github.com/ite-rate/skillbank/internal/sync"
)

// doctorSkillCheck — --skill <name>: 深 check body 引用 vs skill_dir 资源一致性(P0 #15)。
//
// 防 "skill 调 py 因资源没 sync 过去 → 静默失败 → 你只觉得 LLM 质量差" 的盲区。
// SkillBank 责任到此为止:LLM 真跑通 py 不是它管,但引用文件缺失可识别。
func (a *App) doctorSkillCheck(skillName string) int {
	skillDir := filepath.Join(a.RepoRoot, "skills", skillName)
	skillMD := filepath.Join(skillDir, "SKILL.md")
	if _, err := os.Stat(skillMD); err != nil {
		fmt.Printf("[doctor --skill] canonical 不存在: skills/%s/\n", skillName)
		return 2
	}
	fmt.Printf("[doctor --skill] %s\n", skillName)
	fmt.Printf("  canonical: %s\n", skillDir)

	// 1. 资源镜像统计
	res := refs.ResourceStats(skillDir)
	if res == "" {
		res = "(无资源)"
	}
	fmt.Printf("  资源镜像: %s\n", res)

	// 2. body 引用与资源对应 check
	in, err := parser.ParseCanonical(skillMD)
	if err != nil {
		fmt.Printf("  ✗ canonical SKILL.md 解析失败: %v\n", err)
		return 1
	}
	issues := refs.CheckBodyRefs(in.Body, skillDir)
	if len(issues) == 0 {
		fmt.Println("  body 引用检查: body 里无相对路径引用(scripts/refs/templates/...), 无可查项")
		return 0
	}
	nMissing, nOK := 0, 0
	for _, it := range issues {
		if it.Severity == "missing" {
			nMissing++
		} else if it.Severity == "ok" {
			nOK++
		}
		fmt.Printf("    %s\n", it)
	}
	fmt.Printf("  合计: ✓%d 引用文件存在 / ✗%d 缺失\n", nOK, nMissing)

	// 3. 缺失明细 + 建议
	if nMissing > 0 {
		fmt.Println("\n  ⚠ SkillBank 端无法帮你修(资源本应有未镜像 = 你 import 时漏了资源):")
		for _, it := range issues {
			if it.Severity == "missing" {
				fmt.Printf("    %s\n", it.Detail)
			}
		}
		fmt.Println("    建议:检查源 skill 目录是否完整;或 `skillbank import --force <源> 重导一次`")
		return 1
	}
	fmt.Println("  body 引用与镜像资源一致 ✓")
	return 0
}

func (a *App) cmdDoctor(args []string) int {
	fs := newFlagSet("machine", "skill")
	machineFlag := fs.strP("machine", "")
	skillFlag := fs.strP("skill", "")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[doctor] %s\n", msg)
		return 2
	}

	// --skill <name> 细查基准:body 引用 vs 资源镜像一致性
	if *skillFlag != "" {
		return a.doctorSkillCheck(*skillFlag)
	}

	var errsOut, warns []string
	fmt.Printf("[doctor] repo: %s\n", a.RepoRoot)

	// 1. 配置互验
	agentsCfg, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("  ✗ 配置加载失败: %v\n", err)
		return 1
	}
	fmt.Printf("  ✓ 配置加载: %d agents, %d machines\n", len(agentsCfg.Names()), len(machines.Machines))

	machine, rc := a.resolveMachine("doctor", machines, *machineFlag, false)
	if rc != 0 {
		return rc
	}
	// 本机绑定状态(未绑定的命令默认值解析会拒绝执行, 提前在此提醒)
	bound := identity.ReadBinding(a.RepoRoot)
	switch {
	case bound == "":
		warns = append(warns, "本机身份未绑定: 不带 --machine 的命令会拒绝执行"+
			"(`skillbank use <别名>` 或 `skillbank scan --machine <别名>`)")
	case bound != machine:
		warns = append(warns, fmt.Sprintf("本机绑定 %q ≠ 本次查询机器 %q(显式指定)", bound, machine))
	default:
		fmt.Printf("  ✓ 本机绑定: %s\n", bound)
	}

	// 2. 该机器路径存在性
	e_, w_ := machines.CheckPathsExist(machine)
	for _, x := range e_ {
		errsOut = append(errsOut, "路径: "+x)
	}
	for _, x := range w_ {
		warns = append(warns, "路径: "+x)
	}
	fmt.Printf("  ✓/✗ 路径检查: %d errors, %d warnings\n", len(e_), len(w_))

	// 3. manifest 一致性
	m, err := manifest.Load(a.ManifestPath())
	if err != nil {
		fmt.Printf("  ✗ manifest 加载失败: %v\n", err)
		return 1
	}
	issues := m.CheckConsistency()
	for _, i := range issues {
		warns = append(warns, "manifest: "+i)
	}
	fmt.Printf("  ✓ manifest: %d 条记录, %d 项差异\n", len(m.Records), len(issues))

	// 4. canonical skills 可解析 + name 一致
	skillDirs := sync.IterCanonicalSkills(a.RepoRoot)
	for _, d := range skillDirs {
		name := filepath.Base(d)
		in, err := parser.ParseCanonical(filepath.Join(d, "SKILL.md"))
		if err != nil {
			errsOut = append(errsOut, fmt.Sprintf("canonical: %s 解析失败: %v", name, err))
		} else if in.Name != name {
			warns = append(warns, fmt.Sprintf("canonical: %s 的 frontmatter name=%q 不一致", name, in.Name))
		}
	}
	fmt.Printf("  ✓/✗ canonical: %d 个 skill\n", len(skillDirs))

	// 5. git 状态
	gitOut := ""
	if r, err := exec.Command("git", "-C", a.RepoRoot, "status", "--porcelain").Output(); err == nil {
		gitOut = strings.TrimSpace(string(r))
	}
	if gitOut != "" {
		warns = append(warns, fmt.Sprintf("git 工作区有未提交变更(%d 文件)",
			len(strings.Split(gitOut, "\n"))))
	}
	gitState := "干净"
	if gitOut != "" {
		gitState = "有未提交变更"
	}
	fmt.Printf("  ✓ git: %s\n", gitState)

	for _, w := range warns {
		fmt.Printf("  ⚠ %s\n", w)
	}
	for _, e := range errsOut {
		fmt.Printf("  ✗ %s\n", e)
	}
	state := "OK"
	if len(errsOut) > 0 {
		state = "FAIL"
	}
	fmt.Printf("[doctor] %s(%d errors, %d warnings)\n", state, len(errsOut), len(warns))
	if len(errsOut) > 0 {
		return 1
	}
	return 0
}