// 7 个 Agent emitter + 注册表(对应 Python emitters/{claudecode,zcode,qwenworkcn,
// teleagent,hermes,codex,kimi}.py + __init__.py EMITTERS)。
//
// 字段集逐 Agent 方言(决策不变):
//   - ClaudeCode/ZCode: name + description (+ disable-model-invocation)
//   - QwenWorkCN:       name + description + _zh 直传 (+ enabled_at: false)
//   - TeleAgent:        name + description + _cn 镜像 (+ enabled_at: false)
//   - Codex:            name + description(≤1024 触发短语保留截断) (+ disable-model-invocation)
//   - Hermes:           name + description(≤1024) + metadata.hermes 命名空间 + imported/ 类目 + 100k 跳过
//   - kimi-code:        name + description(无禁触发字段)
//
// canonical 元字段(native_agent/requires/version/license)不写入 Agent 文件
// (它们是 emitter 决策依据, 不是给 Agent LLM 看的)。
package emit

import (
	"fmt"
	"path/filepath"
	"sort"
	"strings"
	"unicode/utf8"

	"github.com/ite-rate/skillbank/internal/config"
	"github.com/ite-rate/skillbank/internal/ir"
)

const (
	codexDescMax  = 1024
	hermesDescMax = 1024
	hermesFileMax = 100_000
	ellipsis      = "..."
)

// --- 通用 cp 部署(除 Hermes 外全部同形) ---

// deployCP — cp SKILL.md + resources/ 到 <deployRoot>/<name>/。
func deployCP(e Emitter, in *ir.SkillIR, deployRoot string, cfg *config.AgentConfig,
	canonicalSkillDir string) (EmitterResult, error) {
	skillTargetDir := TargetDir(e.AgentName(), in, deployRoot, cfg)
	// 目标是旧软链/非目录文件 → 先删(分类层保证无记录目标到不了这里)
	removeIfSymlinkOrNonDir(skillTargetDir)
	if err := mkdirAll(skillTargetDir); err != nil {
		return EmitterResult{}, err
	}
	content, err := BuildSkillMDBytes(e, in, cfg, canonicalSkillDir)
	if err != nil {
		return EmitterResult{}, err
	}
	skillMDPath := filepath.Join(skillTargetDir, "SKILL.md")
	if err := WriteSkillMD(content, skillMDPath); err != nil {
		return EmitterResult{}, err
	}
	if err := WriteResources(skillTargetDir, canonicalSkillDir); err != nil {
		return EmitterResult{}, err
	}
	return EmitterResult{DeployedPath: skillMDPath, Method: "cp"}, nil
}

// --- 截断策略(rune 计数, 对应 Python len(str) 非 len(bytes)) ---

// truncateTail — Hermes 式简单截断: 尾部截 + "..."。
func truncateTail(desc string, maxChars int) string {
	r := []rune(desc)
	if len(r) <= maxChars {
		return desc
	}
	clip := maxChars - len(ellipsis)
	if clip <= 0 {
		return ellipsis
	}
	return string(r[:clip]) + ellipsis
}

// truncateKeepTrigger — Codex 式截断: 优先保留触发短语所在末句(P0 #4)。
//
// 长 description 尾段常是触发短语("Use when the user asks for ...");
// 末句装得下 → 前段抠头 + " ... " + 末句; 装不下 → 普通尾截 + "..."。
func truncateKeepTrigger(desc string, maxChars int) string {
	r := []rune(desc)
	if len(r) <= maxChars {
		return desc
	}
	budget := maxChars - len(ellipsis)
	if budget <= 0 {
		return ellipsis
	}

	triggers := []string{
		"use when", "when the user", "use this",
		"invoke when", "load when", "trigger when",
	}
	lower := strings.ToLower(desc)
	triggerPos := -1
	for _, t := range triggers {
		if p := strings.LastIndex(lower, t); p > triggerPos {
			triggerPos = p
		}
	}
	if triggerPos == -1 {
		return string(r[:budget]) + ellipsis
	}

	// 留触发短语所在整句末段(从句首/触发短语起, 到 description 结束)
	prefixR := r[:triggerPos]
	cut := -1
	for _, sep := range []string{". ", "\n", "! ", "? "} {
		if p := lastIndexRunes(prefixR, sep); p > cut {
			cut = p
		}
	}
	tailStart := triggerPos
	if cut != -1 {
		tailStart = cut + 1
	}
	tail := strings.Trim(string(r[tailStart:]), " \t")
	tailR := []rune(tail)
	if len(tailR) <= budget {
		const sep = " ... " // 5 chars 头尾分界(计入总长)
		headBudget := budget - len(tailR) - len([]rune(sep))
		if headBudget > 12 && tailStart > 0 {
			head := strings.TrimRight(string(r[:headBudget]), " .,;!?")
			return head + sep + tail
		}
		// 头装不下就只留尾巴
		if len(tailR) < len(r) {
			return tail + ellipsis
		}
		return tail
	}
	return string(r[:budget]) + ellipsis
}

// lastIndexRunes — []rune 内找子串最后出现位置(找不到 -1; rune 索引)。
func lastIndexRunes(r []rune, sub string) int {
	subR := []rune(sub)
	if len(subR) == 0 || len(subR) > len(r) {
		return -1
	}
	for i := len(r) - len(subR); i >= 0; i-- {
		match := true
		for j := range subR {
			if r[i+j] != subR[j] {
				match = false
				break
			}
		}
		if match {
			return i
		}
	}
	return -1
}

// --- 7 个 emitter ---

// ClaudeCodeEmitter — Anthropic Skill 标准本尊(最简 emitter)。
type ClaudeCodeEmitter struct{}

func (ClaudeCodeEmitter) AgentName() string { return "ClaudeCode" }

func (ClaudeCodeEmitter) TransformFrontmatter(in *ir.SkillIR,
	cfg *config.AgentConfig) (map[string]any, []string) {
	fm := map[string]any{"name": in.Name, "description": in.Description}
	order := []string{"name", "description"}
	if cfg.NeedsDisableInvoke(string(in.Level)) {
		fm[cfg.DisableInvokeField] = cfg.DisableInvokeValue
		order = append(order, cfg.DisableInvokeField)
	}
	return fm, order
}

func (e ClaudeCodeEmitter) Deploy(in *ir.SkillIR, deployRoot string,
	cfg *config.AgentConfig, canonicalSkillDir string) (EmitterResult, error) {
	return deployCP(e, in, deployRoot, cfg, canonicalSkillDir)
}

// ZCodeEmitter — 与 ClaudeCode 同形(cp; 2026-08-16 从 ln 软链改 cp 统一)。
type ZCodeEmitter struct{}

func (ZCodeEmitter) AgentName() string { return "ZCode" }

func (ZCodeEmitter) TransformFrontmatter(in *ir.SkillIR,
	cfg *config.AgentConfig) (map[string]any, []string) {
	fm := map[string]any{"name": in.Name, "description": in.Description}
	order := []string{"name", "description"}
	if cfg.NeedsDisableInvoke(string(in.Level)) {
		fm[cfg.DisableInvokeField] = cfg.DisableInvokeValue
		order = append(order, cfg.DisableInvokeField)
	}
	return fm, order
}

func (e ZCodeEmitter) Deploy(in *ir.SkillIR, deployRoot string,
	cfg *config.AgentConfig, canonicalSkillDir string) (EmitterResult, error) {
	return deployCP(e, in, deployRoot, cfg, canonicalSkillDir)
}

// QwenWorkCNEmitter — name + description + _zh 直传 + enabled_at: false。
type QwenWorkCNEmitter struct{}

func (QwenWorkCNEmitter) AgentName() string { return "QwenWorkCN" }

func (QwenWorkCNEmitter) TransformFrontmatter(in *ir.SkillIR,
	cfg *config.AgentConfig) (map[string]any, []string) {
	fm := map[string]any{"name": in.Name, "description": in.Description}
	order := []string{"name", "description"}
	// canonical 中文双字段名就是 _zh, 与 QwenWorkCN 同名 -> 直接传
	if in.DescZH != nil {
		fm["description_zh"] = *in.DescZH
		order = append(order, "description_zh")
	}
	if in.NameZH != nil {
		fm["name_zh"] = *in.NameZH
		order = append(order, "name_zh")
	}
	if cfg.NeedsDisableInvoke(string(in.Level)) {
		fm[cfg.DisableInvokeField] = cfg.DisableInvokeValue
		order = append(order, cfg.DisableInvokeField)
	}
	return fm, order
}

func (e QwenWorkCNEmitter) Deploy(in *ir.SkillIR, deployRoot string,
	cfg *config.AgentConfig, canonicalSkillDir string) (EmitterResult, error) {
	return deployCP(e, in, deployRoot, cfg, canonicalSkillDir)
}

// TeleAgentEmitter — name + description + _cn 镜像(canonical _zh → _cn) + enabled_at: false。
type TeleAgentEmitter struct{}

func (TeleAgentEmitter) AgentName() string { return "TeleAgent" }

func (TeleAgentEmitter) TransformFrontmatter(in *ir.SkillIR,
	cfg *config.AgentConfig) (map[string]any, []string) {
	fm := map[string]any{"name": in.Name, "description": in.Description}
	order := []string{"name", "description"}
	// 双语字段镜像: canonical description_zh -> TeleAgent description_cn
	if in.DescZH != nil {
		fm["description_cn"] = *in.DescZH
		order = append(order, "description_cn")
	}
	if in.NameZH != nil {
		fm["name_cn"] = *in.NameZH
		order = append(order, "name_cn")
	}
	if cfg.NeedsDisableInvoke(string(in.Level)) {
		fm[cfg.DisableInvokeField] = cfg.DisableInvokeValue
		order = append(order, cfg.DisableInvokeField)
	}
	return fm, order
}

func (e TeleAgentEmitter) Deploy(in *ir.SkillIR, deployRoot string,
	cfg *config.AgentConfig, canonicalSkillDir string) (EmitterResult, error) {
	return deployCP(e, in, deployRoot, cfg, canonicalSkillDir)
}

// CodexEmitter — name + description(≤1024 触发短语保留截断) + disable-model-invocation。
type CodexEmitter struct{}

func (CodexEmitter) AgentName() string { return "Codex" }

func (CodexEmitter) TransformFrontmatter(in *ir.SkillIR,
	cfg *config.AgentConfig) (map[string]any, []string) {
	max := cfg.DescriptionMax
	if max == 0 {
		max = codexDescMax
	}
	fm := map[string]any{
		"name":        in.Name,
		"description": truncateKeepTrigger(in.Description, max),
	}
	order := []string{"name", "description"}
	if cfg.NeedsDisableInvoke(string(in.Level)) {
		fm[cfg.DisableInvokeField] = cfg.DisableInvokeValue
		order = append(order, cfg.DisableInvokeField)
	}
	return fm, order
}

func (e CodexEmitter) Deploy(in *ir.SkillIR, deployRoot string,
	cfg *config.AgentConfig, canonicalSkillDir string) (EmitterResult, error) {
	res, err := deployCP(e, in, deployRoot, cfg, canonicalSkillDir)
	if err != nil {
		return res, err
	}
	// 告知 manifest 与 caller: description 被截过
	max := cfg.DescriptionMax
	if max == 0 {
		max = codexDescMax
	}
	if utf8.RuneCountInString(in.Description) > max {
		res.Note = fmt.Sprintf("description truncated to %d chars (Codex load limit)", max)
	}
	return res, nil
}

// HermesEmitter — metadata.hermes 命名空间 + imported/ 类目 + 100k 超限跳过。
type HermesEmitter struct{}

func (HermesEmitter) AgentName() string { return "Hermes" }

func (HermesEmitter) TransformFrontmatter(in *ir.SkillIR,
	cfg *config.AgentConfig) (map[string]any, []string) {
	max := cfg.DescriptionMax
	if max == 0 {
		max = hermesDescMax
	}
	fm := map[string]any{
		"name":        in.Name,
		"description": truncateTail(in.Description, max),
	}
	order := []string{"name", "description"}
	if cfg.NeedsDisableInvoke(string(in.Level)) {
		// Hermes 的禁止自动触发字段在 metadata.hermes 命名空间下
		fm["metadata"] = map[string]any{
			"hermes": map[string]any{
				"disable-model-invocation": cfg.DisableInvokeValue,
			},
		}
		order = append(order, "metadata")
	}
	return fm, order
}

func (e HermesEmitter) Deploy(in *ir.SkillIR, deployRoot string,
	cfg *config.AgentConfig, canonicalSkillDir string) (EmitterResult, error) {
	// 先拼字节流算总字符数(决定是否超限)
	content, err := BuildSkillMDBytes(e, in, cfg, canonicalSkillDir)
	if err != nil {
		return EmitterResult{}, err
	}
	totalChars := utf8.RuneCount(content)
	fileMax := cfg.FileSizeMax
	if fileMax == 0 {
		fileMax = hermesFileMax
	}
	if totalChars > fileMax {
		return EmitterResult{
			DeployedPath: "/dev/null",
			Method:       "skipped",
			Note: fmt.Sprintf("file_size_max exceeded: deployed SKILL.md would be "+
				"%d chars > Hermes limit %d; skipped (body zero-loss intact)",
				totalChars, fileMax),
		}, nil
	}

	category := cfg.DefaultCategory
	if category == "" {
		category = "imported"
	}
	skillTargetDir := TargetDir(e.AgentName(), in, deployRoot, cfg)
	if err := mkdirAll(skillTargetDir); err != nil {
		return EmitterResult{}, err
	}
	skillMDPath := filepath.Join(skillTargetDir, "SKILL.md")
	if err := WriteSkillMD(content, skillMDPath); err != nil {
		return EmitterResult{}, err
	}
	if err := WriteResources(skillTargetDir, canonicalSkillDir); err != nil {
		return EmitterResult{}, err
	}

	var noteParts []string
	max := cfg.DescriptionMax
	if max == 0 {
		max = hermesDescMax
	}
	if utf8.RuneCountInString(in.Description) > max {
		noteParts = append(noteParts, "description truncated to 1024")
	}
	if category != "imported" {
		noteParts = append(noteParts, "category="+category)
	}
	return EmitterResult{
		DeployedPath: skillMDPath,
		Method:       "cp",
		Note:         strings.Join(noteParts, "; "),
	}, nil
}

// KimiEmitter — name + description(kimi 无 frontmatter 禁止触发字段)。
type KimiEmitter struct{}

func (KimiEmitter) AgentName() string { return "kimi-code" }

func (KimiEmitter) TransformFrontmatter(in *ir.SkillIR,
	cfg *config.AgentConfig) (map[string]any, []string) {
	fm := map[string]any{"name": in.Name, "description": in.Description}
	order := []string{"name", "description"}
	// 仅当 cfg 配了 disable_invoke_field 才写(目前 kimi 没配, 留作扩展位)
	if cfg.DisableInvokeField != "" && cfg.NeedsDisableInvoke(string(in.Level)) {
		fm[cfg.DisableInvokeField] = cfg.DisableInvokeValue
		order = append(order, cfg.DisableInvokeField)
	}
	return fm, order
}

func (e KimiEmitter) Deploy(in *ir.SkillIR, deployRoot string,
	cfg *config.AgentConfig, canonicalSkillDir string) (EmitterResult, error) {
	return deployCP(e, in, deployRoot, cfg, canonicalSkillDir)
}

// --- 注册表(对应 Python EMITTERS dict) ---

var emitterNames = []string{
	"ClaudeCode", "ZCode", "QwenWorkCN", "TeleAgent", "Hermes", "Codex", "kimi-code",
}

func newEmitter(name string) (Emitter, bool) {
	switch name {
	case "ClaudeCode":
		return ClaudeCodeEmitter{}, true
	case "ZCode":
		return ZCodeEmitter{}, true
	case "QwenWorkCN":
		return QwenWorkCNEmitter{}, true
	case "TeleAgent":
		return TeleAgentEmitter{}, true
	case "Hermes":
		return HermesEmitter{}, true
	case "Codex":
		return CodexEmitter{}, true
	case "kimi-code":
		return KimiEmitter{}, true
	}
	return nil, false
}

// GetEmitter — agent 名 → emitter(不存在报错, 可用名单按字典序, 对应 Python KeyError 文案)。
func GetEmitter(agentName string) (Emitter, error) {
	if e, ok := newEmitter(agentName); ok {
		return e, nil
	}
	avail := append([]string{}, emitterNames...)
	sort.Strings(avail)
	return nil, fmt.Errorf("no emitter for agent %q(可用: %v)", agentName, avail)
}