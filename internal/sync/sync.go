// Sync 引擎 — canonical skills → 该机器配置的 Agents, 计划/展示/执行三段式。
// (移植 src/skillbank/sync.py, 语义等价)
//
// 流程:
//  1. Collect(): 解析 canonical skills/<name>/SKILL.md → IR;
//     先处理 pending_deletion(删除链跨机段);
//     再处理 disable 级 skill 与孤儿记录(canonical 已删)的清理;
//     最后对每个 skill × 机器上的 Agent 生成 deploy 计划。
//  2. ShowPlan(): 人话展示(dry-run 到此为止)。
//  3. Execute(): 真 deploy(emitter) + manifest upsert/清理。
//
// 计划项 kind:
//
//	deploy    将部署(cp/ln)
//	deferred  目标是真实目录, 不动, 需 zcode-cleanup(保留兼容, 现不再产出)
//	skip      不部署(原因见 detail: 未装 / Hermes 超限 / 被过滤)
//	delete    本机清理(该 skill 的旧部署)
//	pending   其它机器标 pending_deletion
//	keep      hash 相同, 跳过不重写(真幂等;资源自愈交给 --force/doctor)
//	warn      解析/一致性问题, 不中断
package sync

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/ite-rate/skillbank/internal/config"
	"github.com/ite-rate/skillbank/internal/emit"
	"github.com/ite-rate/skillbank/internal/ir"
	"github.com/ite-rate/skillbank/internal/manifest"
	"github.com/ite-rate/skillbank/internal/parser"
	"github.com/ite-rate/skillbank/internal/refs"
)

// PlanItem — 计划里的一条。
type PlanItem struct {
	Kind   string // deploy | deferred | skip | delete | pending | keep | warn
	Skill  string
	Agent  string // 可空
	Detail string
}

// SyncContext — collect 的产物, execute 的输入。
type SyncContext struct {
	Plan  []PlanItem
	IRs   map[string]*ir.SkillIR // skill -> IR
	Order []string               // canonical 解析序(Go map 无序, 序单独保)
	// DeployPairs — execute 阶段要 deploy 的 (skill, agent) 对
	// (collect 时敲定, avoid 重算过滤逻辑)
	DeployPairs [][2]string
}

// --- 阶段 1: collect ---

// IterCanonicalSkills — skills/ 下所有含 SKILL.md 的目录(排序, 确定性)。
func IterCanonicalSkills(repoRoot string) []string {
	skillsDir := filepath.Join(repoRoot, "skills")
	entries, err := os.ReadDir(skillsDir)
	if err != nil {
		return nil
	}
	var dirs []string
	for _, e := range entries {
		if _, err := os.Stat(filepath.Join(skillsDir, e.Name(), "SKILL.md")); err == nil {
			dirs = append(dirs, filepath.Join(skillsDir, e.Name()))
		}
	}
	sort.Strings(dirs)
	return dirs
}

// cleanupPlanForSkill — disable/orphan:本机记录 → delete 项, 其它机器记录 → pending 项。
func cleanupPlanForSkill(skill, machine string, m *manifest.DeploymentsManifest,
	ctx *SyncContext, reason string) {
	for _, r := range m.Find(skill, "", "") {
		if r.Machine == machine {
			ctx.Plan = append(ctx.Plan, PlanItem{"delete", skill, r.Agent,
				fmt.Sprintf("%s; %s", reason, r.DeployPath)})
		} else {
			ctx.Plan = append(ctx.Plan, PlanItem{"pending", skill, r.Agent,
				fmt.Sprintf("%s; %s 下次 sync 时删", reason, r.Machine)})
		}
	}
}

// Collect — 生成 sync 计划。skillsFilter/agentsFilter 为 nil = 不过滤。
func Collect(repoRoot, machine string, skillsFilter, agentsFilter []string,
	machines *config.MachinesConfig, agentsCfg *config.AgentsConfig,
	m *manifest.DeploymentsManifest, force bool) (*SyncContext, error) {
	ctx := &SyncContext{IRs: map[string]*ir.SkillIR{}}
	mcfg, err := machines.GetMachine(machine)
	if err != nil {
		return nil, err
	}

	// a) pending_deletion(其它机器 rm 标来的, 本机 sync 先执行)
	for _, r := range m.Records {
		if r.PendingDeletion && r.Machine == machine {
			ctx.Plan = append(ctx.Plan, PlanItem{"delete", r.Skill, r.Agent,
				fmt.Sprintf("pending; %s", r.DeployPath)})
		}
	}

	// b) 孤儿记录:manifest 有但 canonical 已无此 skill
	canonicalNames := map[string]bool{}
	canonicalDirs := IterCanonicalSkills(repoRoot)
	for _, d := range canonicalDirs {
		canonicalNames[filepath.Base(d)] = true
	}
	for _, orphan := range m.Skills() {
		if !canonicalNames[orphan] {
			cleanupPlanForSkill(orphan, machine, m, ctx, "canonical 已删除")
		}
	}

	// c) 解析 canonical skills
	for _, skillDir := range canonicalDirs {
		name := filepath.Base(skillDir)
		in, err := parser.ParseCanonical(filepath.Join(skillDir, "SKILL.md"))
		if err != nil { // 单 skill 坏不中断全局
			ctx.Plan = append(ctx.Plan, PlanItem{"warn", name, "",
				fmt.Sprintf("解析失败: %v", err)})
			continue
		}
		if in.Name != name {
			ctx.Plan = append(ctx.Plan, PlanItem{"warn", name, "",
				fmt.Sprintf("frontmatter name=%q != 目录名(以目录名为准)", in.Name)})
		}
		ctx.IRs[name] = in
		ctx.Order = append(ctx.Order, name)

		// disable 级:不同步, 且清理既有部署
		if in.Level == ir.Disable {
			if len(m.Find(name, "", "")) > 0 {
				cleanupPlanForSkill(name, machine, m, ctx, "level=disable")
			} else {
				ctx.Plan = append(ctx.Plan, PlanItem{"skip", name, "", "disable 且无部署记录"})
			}
		}
	}

	// d) skill × agent 部署计划
	// 先按 agent 粒度判一次"装没装":skills 根的父目录(agent home)不存在 = 没装,
	// 该 agent 全部 skip(防 MkdirAll 凭空造孤儿目录;与 doctor error 语义一致)。
	installed := map[string]bool{}
	for _, agent := range agentsCfg.Names() {
		if !mcfg.HasAgent(agent) {
			continue
		}
		root := machines.GetSkillsDir(machine, agent)
		if root == "" {
			installed[agent] = false
			continue
		}
		if _, err := os.Stat(filepath.Dir(root)); err == nil {
			installed[agent] = true
		}
	}

	for _, name := range ctx.Order {
		in := ctx.IRs[name]
		if in.Level == ir.Disable {
			continue
		}
		if len(skillsFilter) > 0 && !contains(skillsFilter, name) {
			continue
		}
		for _, agent := range agentsCfg.Names() { // agents.toml 顺序
			if !mcfg.HasAgent(agent) {
				continue // 该机器没配此 Agent = 没装
			}
			deployRoot := machines.GetSkillsDir(machine, agent)
			if !installed[agent] {
				ctx.Plan = append(ctx.Plan, PlanItem{"skip", name, agent,
					fmt.Sprintf("agent 未安装?(%s 不存在)", filepath.Dir(deployRoot))})
				continue
			}
			if len(agentsFilter) > 0 && !contains(agentsFilter, agent) {
				ctx.Plan = append(ctx.Plan, PlanItem{"skip", name, agent, "未选(过滤)"})
				continue
			}
			detail := filepath.Join(deployRoot, name)

			kind := "deploy"
			recs := m.Find(name, machine, agent)
			if len(recs) > 0 && recs[0].IrHash == in.BodyHash() && !force {
				kind = "keep"
			}
			ctx.Plan = append(ctx.Plan, PlanItem{kind, name, agent, detail})
			// keep 项不进 DeployPairs:已对账(hash 相同), execute 跳过不重写、不刷 manifest。
			// 资源自愈不是 keep 的职责(用户手动改部署端资源不会被纠正),需自愈用 --force/doctor。
			// force 时强制走 deploy(让 frontmatter 字段级透传/overrides 合并等非 body 变更落地)。
			if kind == "deploy" {
				ctx.DeployPairs = append(ctx.DeployPairs, [2]string{name, agent})
			}
		}
	}
	return ctx, nil
}

func contains(list []string, s string) bool {
	for _, x := range list {
		if x == s {
			return true
		}
	}
	return false
}

// --- 阶段 2: show ---

var kindMark = map[string]string{
	"deploy": "+", "keep": "=", "deferred": "~", "skip": "-",
	"delete": "x", "pending": "p", "warn": "!",
}

var kindOrder = []string{"deploy", "keep", "deferred", "skip", "delete", "pending", "warn"}

// ShowPlan — 人话展示计划(dry-run 到此为止)。
func ShowPlan(ctx *SyncContext) {
	if len(ctx.Plan) == 0 {
		fmt.Println("[sync] 无计划(无 canonical skill / 无该机器 Agent)")
		return
	}
	for _, it := range ctx.Plan {
		mark, ok := kindMark[it.Kind]
		if !ok {
			mark = "?"
		}
		agent := ""
		if it.Agent != "" {
			agent = " → " + it.Agent
		}
		fmt.Printf("  [%s] %-8s %s%s  %s\n", mark, it.Kind, it.Skill, agent, it.Detail)
	}
	var parts []string
	for _, k := range kindOrder {
		n := 0
		for _, it := range ctx.Plan {
			if it.Kind == k {
				n++
			}
		}
		if n > 0 {
			parts = append(parts, fmt.Sprintf("%d %s", n, k))
		}
	}
	fmt.Printf("  合计: %s\n", strings.Join(parts, ", "))
}

// --- 阶段 3: execute ---

// Execute — 执行计划;返回非 0 表示有失败数。manifest 有变更时 save。
func Execute(repoRoot, machine string, ctx *SyncContext,
	machines *config.MachinesConfig, agentsCfg *config.AgentsConfig,
	m *manifest.DeploymentsManifest) int {
	if len(ctx.Plan) == 0 {
		return 0
	}
	failures := 0
	manifestDirty := false

	// 删除段:本机 delete 项(pending 项 + disable/orphan 清理)
	deleteSkills := map[string]bool{}
	pendingSkills := map[string]bool{}
	for _, it := range ctx.Plan {
		if it.Kind == "delete" {
			deleteSkills[it.Skill] = true
		}
		if it.Kind == "pending" {
			pendingSkills[it.Skill] = true
		}
	}
	var delSorted []string
	for s := range deleteSkills {
		delSorted = append(delSorted, s)
	}
	sort.Strings(delSorted)
	for _, skill := range delSorted {
		for _, a := range m.DeleteLocal(skill, machine, "", false) {
			fmt.Printf("  %s\n", a)
			manifestDirty = true
		}
	}
	// 其它机器 pending 标记(disable/orphan 的)
	var pendSorted []string
	for s := range pendingSkills {
		pendSorted = append(pendSorted, s)
	}
	sort.Strings(pendSorted)
	for _, skill := range pendSorted {
		if n := m.MarkPendingDeletion(skill, machine); n > 0 {
			fmt.Printf("  pending_deletion x%d: %s(其它机器下次 sync 删)\n", n, skill)
			manifestDirty = true
		}
	}

	// keep 段:已对账的项不重写, 仅打印告知(避免与 skip/未部署混淆)。
	for _, it := range ctx.Plan {
		if it.Kind == "keep" {
			fmt.Printf("  = %s → %s: keep(hash 相同, 跳过重写)\n", it.Skill, it.Agent)
		}
	}

	// 部署段
	for _, pair := range ctx.DeployPairs {
		name, agent := pair[0], pair[1]
		in := ctx.IRs[name]
		cfg := agentsCfg.Get(agent)
		deployRoot := machines.GetSkillsDir(machine, agent)
		e, err := emit.GetEmitter(agent)
		var result emit.EmitterResult
		if err == nil {
			result, err = e.Deploy(in, deployRoot, cfg, filepath.Join(repoRoot, "skills", name))
		}
		if err != nil { // 单个失败不中断其余
			fmt.Printf("  ✗ %s → %s: %v\n", name, agent, err)
			failures++
			continue
		}

		if result.Method == "skipped" {
			// Hermes 超限等:该 Agent 本轮不部署。若之前有部署记录 → 清掉旧副本+记录
			fmt.Printf("  - %s → %s: SKIP(%s)\n", name, agent, result.Note)
			if recs := m.Find(name, machine, agent); len(recs) > 0 {
				for _, a := range m.DeleteLocal(name, machine, agent, false) {
					fmt.Printf("    清理旧部署: %s\n", a)
				}
				manifestDirty = true
			}
			continue
		}
		if result.Method == "deferred" {
			fmt.Printf("  ~ %s → %s: DEFERRED(%s)\n", name, agent, result.Note)
			continue
		}

		// P0#3: kimi 不支持 frontmatter 禁止触发字段, manual/experimental disable 在 kimi 失效
		if agent == "kimi-code" && (in.Level == ir.Manual || in.Level == ir.Experimental) {
			fmt.Printf("  ⚠ %s → kimi-code: level=%s 但 kimi 无禁自动触发字段, "+
				"该 Agent 端可能仍自动触发(请靠 description 话术或下级工具显式控制)\n", name, in.Level)
		}

		m.Upsert(manifest.DeployRecord{
			Skill: name, Machine: machine, Agent: agent,
			DeployPath: result.DeployedPath, Method: result.Method,
			IrHash: in.BodyHash(), Note: result.Note,
		})
		manifestDirty = true
		// 资源镜像统计(让 silent failure 可感知:P0 #15)
		resStat := refs.ResourceStats(filepath.Dir(result.DeployedPath))
		extra := ""
		if result.Note != "" {
			extra = fmt.Sprintf("(%s)", result.Note)
		}
		resStr := " [无资源]"
		if resStat != "" {
			resStr = fmt.Sprintf(" [资源: %s]", resStat)
		}
		fmt.Printf("  %s %s → %s%s%s\n", result.Method, name, agent, extra, resStr)
	}

	if manifestDirty {
		if err := m.Save(""); err != nil {
			fmt.Printf("  ✗ manifest 保存失败: %v\n", err)
			return failures + 1
		}
		fmt.Printf("  manifest 已更新: %s\n", m.Path)
	}
	return failures
}