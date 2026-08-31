// Package importer — 把既有 skill(各 Agent 目录/本地路径/git URL)反向导入中央仓。
//
// 移植合同(对应 Python importer.py):
// 只读源目录, 全部产物写进 repo 的 skills/<name>/:
//   skills/<name>/SKILL.md                       canonical frontmatter + body 原字节
//   skills/<name>/<原目录其它文件/子目录>          保真镜像
//   skills/<name>/.agent_overrides/<agent>.toml   Agent 专有字段(不污染 canonical)
//
// 字段映射:
//   name/description 直传(缺 name 用目录名; 缺 description 报错)
//   level 默认 manual(新导入未审, 不自动触发)
//   native_agent: --agent 指定, 或按源路径前缀匹配 machines.toml 探测
//   _zh 直传(QwenWorkCN) / _cn 映射到 canonical _zh(TeleAgent)
//   其余字段 → .agent_overrides/<agent>.toml(或 _unknown.toml)
package importer

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/ite-rate/skillbank/internal/config"
	"github.com/ite-rate/skillbank/internal/emit"
	"github.com/ite-rate/skillbank/internal/ir"
	"github.com/ite-rate/skillbank/internal/parser"
	"gopkg.in/yaml.v3"
)

// Agent 名 → 短码(重名变体建议名用, 3-5 字符用户可识别)。
var agentShort = map[string]string{
	"ClaudeCode": "claude",
	"ZCode":      "zcode",
	"QwenWorkCN": "qwen",
	"TeleAgent":  "tele",
	"Hermes":     "hermes",
	"Codex":      "codex",
	"kimi-code":  "kimi",
}

// ShortAgentCode — Agent 短码(空 agent → "src")。
func ShortAgentCode(agent string) string {
	if agent == "" {
		return "src"
	}
	if s, ok := agentShort[agent]; ok {
		return s
	}
	return strings.ReplaceAll(strings.ToLower(agent[:min(5, len(agent))]), "-", "")
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// SuggestVariantName — 不同 body 同名时: 原名-native短码(e.g. docx-qwen)。
func SuggestVariantName(baseName, agent string) string {
	return baseName + "-" + ShortAgentCode(agent)
}

// crossDirRe — 跨 skill 目录的相对引用(HERMES 跨 skill 插值这种)。
var crossDirRe = regexp.MustCompile(`\.\./[A-Za-z0-9_\-]+/`)

// absolutePathRe — Unix 绝对路径或 Windows 盘符前缀。
var absolutePathHitRe = regexp.MustCompile(`(?:^|[\s"'(])(/Users/|/home/|[A-Z]:\\)`)
var absoluteSampleRe = regexp.MustCompile(`(?:/Users/|/home/|/usr/|/opt/|/tmp/|/[a-zA-Z0-9_./-]+|[A-Z]:\\[^\s\n]+)`)

// ScanBodyPaths — 扫 body 找:
//   - 绝对路径(/Users/ /home/ C:\ ...) — 跨机迁移必断
//   - ../ 跨 skill 目录的相对引用 — 部署到不同子目录布局后断裂
//
// 返回人话警告描述列表(空表示没问题)。
func ScanBodyPaths(body []byte) []string {
	text := string(body)
	var warns []string
	if absolutePathHitRe.MatchString(text) {
		sample := "..."
		if m := absoluteSampleRe.FindString(text); m != "" {
			if len(m) > 80 {
				m = m[:80]
			}
			sample = m
		}
		warns = append(warns, fmt.Sprintf("body 含写死的绝对路径(%s,跨机迁移必断)", sample))
	}
	if cross := crossDirRe.FindAllString(text, -1); len(cross) > 0 {
		set := map[string]bool{}
		for _, c := range cross {
			set[c] = true
		}
		var uniq []string
		for c := range set {
			uniq = append(uniq, c)
		}
		sort.Strings(uniq)
		warns = append(warns, fmt.Sprintf("body 含跨 skill 目录的相对引用(%s,部署到 imported/ 或软链后可能失效)",
			strings.Join(uniq, "../")[:min(60, len(strings.Join(uniq, "../")))]))
	}
	return warns
}

// stripFMBody — SKILL.md 切出 body(重名比较用); 失败回退整文件。
func stripFMBody(skillMDPath string) []byte {
	raw, err := os.ReadFile(skillMDPath)
	if err != nil {
		return raw
	}
	m := parser.FrontmatterRe.FindSubmatchIndex(raw)
	if m == nil {
		return raw
	}
	return raw[m[4]:m[5]]
}

// canonicalKnownFields — canonical 认识的字段(不进 overrides)。
var canonicalKnownFields = map[string]bool{
	"name": true, "description": true, "level": true, "native_agent": true,
	"requires": true, "description_zh": true, "name_zh": true,
	"version": true, "license": true, "source": true,
}

// DetectSourceAgent — 源目录在哪个 Agent 的 skills_dir 下 → 那个 Agent 名。
func DetectSourceAgent(srcDir string, machines *config.MachinesConfig, machine string) string {
	src, err := filepath.Abs(srcDir)
	if err != nil {
		return ""
	}
	m, ok := machines.Machines[machine]
	if !ok {
		return ""
	}
	for _, aName := range m.AgentOrder {
		root, err := filepath.Abs(m.Agents[aName].SkillsDir)
		if err != nil {
			continue
		}
		if src == root || strings.HasPrefix(src, root+string(filepath.Separator)) {
			return aName
		}
	}
	return ""
}

// ImportResult — 一次导入的产物。
type ImportResult struct {
	CanonicalDir string
	Warnings     []string
	Source       string // 写进 canonical source 的来源(git URL; 本地导入为空)
	Commit       string // git 导入时的源 commit(仅展示用, 不持久化)
}

// Options — import_skill 参数(Python 关键字参数的具名化)。
type Options struct {
	Level          string // 默认 manual
	Agent          string // 显式 native_agent
	Machines       *config.MachinesConfig
	Machine        string
	Force          bool
	RenameCallback func(baseName, suggested, native string) (string, error)
	// DisableAutoRename 关掉自动改名(默认自动改名, 对齐 Python auto_rename=True);
	// 关掉后不同 body 重名且无 callback → 报错(防自动覆盖)。
	DisableAutoRename bool
	// Source — git URL 来源, 写进 canonical frontmatter source。
	// 空 = 本地路径导入, 不写(绝对路径跨机必断)。
	Source string
}

// ImportSkill — 导入一个 skill 目录(须含 SKILL.md)→ skills/<name>/。
//
// 重名策略(用户拍板 2026-08-15):
//   - 同 body 同名(软链共享同一份真身) → 静默去重; 已存在的就是它, 不交互
//   - 不同 body 同名 → 交互改名; 建议名 = 原名-native短码(e.g. docx-qwen)
//   - Force=true → 同 body 也允许重入(覆盖同 body 同名)
func ImportSkill(srcDir, repoRoot string, opts Options) (ImportResult, error) {
	level := opts.Level
	if level == "" {
		level = "manual"
	}
	srcDir, err := filepath.Abs(srcDir)
	if err != nil {
		return ImportResult{}, err
	}
	skillMD := filepath.Join(srcDir, "SKILL.md")
	raw, err := os.ReadFile(skillMD)
	if err != nil {
		return ImportResult{}, fmt.Errorf("源目录无 SKILL.md: %s", srcDir)
	}
	m := parser.FrontmatterRe.FindSubmatchIndex(raw)
	if m == nil {
		return ImportResult{}, fmt.Errorf("SKILL.md 无 frontmatter 边界: %s", skillMD)
	}
	fmBytes := raw[m[2]:m[3]]
	body := raw[m[4]:m[5]]
	var fm map[string]any
	if err := yaml.Unmarshal(fmBytes, &fm); err != nil || fm == nil {
		return ImportResult{}, fmt.Errorf("frontmatter 不是 YAML mapping: %s", skillMD)
	}

	name := srcDirName(srcDir)
	if v, ok := fm["name"].(string); ok && v != "" {
		name = v
	}
	description, _ := fm["description"].(string)
	if description == "" {
		return ImportResult{}, fmt.Errorf("frontmatter 缺 description(必填): %s", skillMD)
	}

	// 双语: _zh 直传(QwenWorkCN), _cn 映射到 canonical _zh(TeleAgent)
	descZH := firstStr(fm, "description_zh", "description_cn")
	nameZH := firstStr(fm, "name_zh", "name_cn")

	// native_agent: 显式 > 路径探测
	native := opts.Agent
	if native == "" && opts.Machines != nil && opts.Machine != "" {
		native = DetectSourceAgent(srcDir, opts.Machines, opts.Machine)
	}

	// === 重名处理 ===
	dst := filepath.Join(repoRoot, "skills", name)
	irName := name
	if _, err := os.Stat(dst); err == nil {
		existingBody := stripFMBody(filepath.Join(dst, "SKILL.md"))
		if bytesEqual(existingBody, body) && !opts.Force {
			// 同 body 同名: 静默去重, 返回已存在的(重复 import 不报错也不覆盖)
			return ImportResult{CanonicalDir: dst,
				Warnings: []string{fmt.Sprintf("已存在同内容同名的 %s, 跳过(软链共享去重)", filepath.Base(dst))}}, nil
		}
		if !bytesEqual(existingBody, body) {
			// 不同 body 同名 → 交互/自动改名
			suggested := SuggestVariantName(name, native)
			switch {
			case opts.RenameCallback != nil:
				newName, cbErr := opts.RenameCallback(name, suggested, native)
				if cbErr != nil { // 用户跳过等 → 整个 import 中止
					return ImportResult{}, cbErr
				}
				name = newName
			case !opts.DisableAutoRename:
				name = suggested
			default:
				return ImportResult{}, fmt.Errorf("canonical 已存在且 body 不同: %s。建议名 %s(本 import 仅在 CLI 交互/auto_rename 时生效)", dst, suggested)
			}
			irName = name // canonical 用新名
			dst = filepath.Join(repoRoot, "skills", name)
			if _, err := os.Stat(dst); err == nil && !opts.Force {
				return ImportResult{}, fmt.Errorf("改名后仍冲突 %s(--force 覆盖, 或用别的名)", dst)
			}
		}
	}

	// provenance source: 源 frontmatter 已声明的优先(不覆盖); 否则用 opts.Source(git URL)
	src := opts.Source
	var sourceWarn string
	if existing, ok := fm["source"].(string); ok && existing != "" {
		if src != "" && existing != src {
			sourceWarn = fmt.Sprintf("源 SKILL.md 已有 source=%q, 保留原值", existing)
		}
		src = existing
	}

	in := &ir.SkillIR{
		Name:        irName,
		Description: description,
		Body:        body,
		Level:       ir.Level(level),
		NativeAgent: strPtrOrNil(native),
		DescZH:      strPtrOrNil(descZH),
		NameZH:      strPtrOrNil(nameZH),
		Version:     versionPtr(fm, "version"),
		License:     versionPtr(fm, "license"),
		Source:      strPtrOrNil(src),
	}

	if _, err := os.Stat(dst); err == nil && opts.Force {
		if err := os.RemoveAll(dst); err != nil {
			return ImportResult{}, err
		}
	}
	if err := os.MkdirAll(dst, 0o755); err != nil {
		return ImportResult{}, err
	}

	// canonical SKILL.md(body bytes 原样)
	if err := emit.EmitCanonical(in, filepath.Join(dst, "SKILL.md")); err != nil {
		return ImportResult{}, err
	}

	// 其余文件/子目录保真镜像
	if err := mirrorOtherFiles(srcDir, dst); err != nil {
		return ImportResult{}, err
	}

	// Agent 专有字段 → overrides
	leftovers := map[string]any{}
	for k, v := range fm {
		if canonicalKnownFields[k] || k == "description_cn" || k == "name_cn" || v == nil {
			continue
		}
		leftovers[k] = v
	}
	if len(leftovers) > 0 {
		ovAgent := opts.Agent
		if ovAgent == "" {
			ovAgent = native
		}
		if ovAgent == "" {
			ovAgent = "_unknown"
		}
		ovDir := filepath.Join(dst, ".agent_overrides")
		if err := os.MkdirAll(ovDir, 0o755); err != nil {
			return ImportResult{}, err
		}
		ovFile := filepath.Join(ovDir, ovAgent+".toml")
		if err := os.WriteFile(ovFile, []byte(marshalTOML(leftovers)), 0o644); err != nil {
			return ImportResult{}, err
		}
	}

	warnings := ScanBodyPaths(body)
	if sourceWarn != "" {
		warnings = append(warnings, sourceWarn)
	}
	return ImportResult{CanonicalDir: dst, Warnings: warnings, Source: opts.Source}, nil
}

func srcDirName(srcDir string) string {
	return filepath.Base(srcDir)
}

func bytesEqual(a, b []byte) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func firstStr(fm map[string]any, keys ...string) string {
	for _, k := range keys {
		if s, ok := fm[k].(string); ok && s != "" {
			return s
		}
	}
	return ""
}

func strPtrOrNil(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}

// versionPtr — 字段存在且非 nil → 字符串化(Python `str(fm[k]) if fm.get(k) is not None`)。
func versionPtr(fm map[string]any, key string) *string {
	v, ok := fm[key]
	if !ok || v == nil {
		return nil
	}
	if s, ok := v.(string); ok {
		return &s
	}
	s := fmt.Sprintf("%v", v)
	return &s
}

// mirrorOtherFiles — src 下除 SKILL.md 外的条目保真镜像到 dst(排序遍历, 确定性)。
func mirrorOtherFiles(srcDir, dst string) error {
	names, err := listDirNames(srcDir)
	if err != nil {
		return err
	}
	for _, name := range names {
		if name == "SKILL.md" {
			continue
		}
		if err := mirrorEntry(filepath.Join(srcDir, name), filepath.Join(dst, name)); err != nil {
			return err
		}
	}
	return nil
}

func listDirNames(dir string) ([]string, error) {
	items, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	names := make([]string, 0, len(items))
	for _, e := range items {
		names = append(names, e.Name())
	}
	sort.Strings(names)
	return names, nil
}

// mirrorEntry — 单个条目(文件/目录/软链)镜像; 目录递归。
func mirrorEntry(s, d string) error {
	info, err := os.Lstat(s)
	if err != nil {
		return err
	}
	switch {
	case info.Mode()&os.ModeSymlink != 0:
		target, err := os.Readlink(s)
		if err != nil {
			return err
		}
		abs, err := filepath.Abs(s)
		if err != nil {
			return err
		}
		resolved := target
		if !filepath.IsAbs(resolved) {
			resolved = filepath.Join(filepath.Dir(abs), target)
		}
		return os.Symlink(resolved, d)
	case info.IsDir():
		if err := os.MkdirAll(d, 0o755); err != nil {
			return err
		}
		names, err := listDirNames(s)
		if err != nil {
			return err
		}
		for _, name := range names {
			if err := mirrorEntry(filepath.Join(s, name), filepath.Join(d, name)); err != nil {
				return err
			}
		}
		return nil
	default:
		data, err := os.ReadFile(s)
		if err != nil {
			return err
		}
		return os.WriteFile(d, data, info.Mode().Perm())
	}
}

// marshalTOML — map[string]any → TOML(BurntSushi 无 encoder, 手写最小序化器)。
// 格式合同: 合法 + 确定(键字典序; 标量先出, 嵌套 table 后出) — 与 tomli_w 排版
// 不逐字节对齐(内部工件, 无跨实现字节合同)。
func marshalTOML(m map[string]any) string {
	var b strings.Builder
	writeTOMLTable(&b, m, nil)
	return b.String()
}

func writeTOMLTable(b *strings.Builder, m map[string]any, path []string) {
	// 标量/数组先出
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var tables []string
	for _, k := range keys {
		if _, ok := m[k].(map[string]any); ok {
			tables = append(tables, k)
			continue
		}
		fmt.Fprintf(b, "%s = %s\n", k, tomlValue(m[k]))
	}
	// 嵌套 table 后出([a.b] 段)
	sort.Strings(tables)
	for _, k := range tables {
		sub := m[k].(map[string]any)
		fmt.Fprintf(b, "[%s]\n", strings.Join(append(append([]string{}, path...), k), "."))
		writeTOMLTable(b, sub, append(append([]string{}, path...), k))
	}
}

func tomlValue(v any) string {
	switch t := v.(type) {
	case string:
		return tomlQuote(t)
	case bool:
		if t {
			return "true"
		}
		return "false"
	case int:
		return fmt.Sprintf("%d", t)
	case int64:
		return fmt.Sprintf("%d", t)
	case uint64:
		return fmt.Sprintf("%d", t)
	case float64:
		return fmt.Sprintf("%g", t)
	case []any:
		parts := make([]string, 0, len(t))
		for _, e := range t {
			parts = append(parts, tomlValue(e))
		}
		return "[" + strings.Join(parts, ", ") + "]"
	case []string:
		parts := make([]string, 0, len(t))
		for _, e := range t {
			parts = append(parts, tomlQuote(e))
		}
		return "[" + strings.Join(parts, ", ") + "]"
	case map[string]any:
		// 内联表(浅层); 深层由 writeTOMLTable 段落处理
		keys := make([]string, 0, len(t))
		for k := range t {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		parts := make([]string, 0, len(keys))
		for _, k := range keys {
			if _, isMap := t[k].(map[string]any); isMap {
				continue // 不内联嵌套表(由段落路径保证唯一处理)
			}
			parts = append(parts, k+" = "+tomlValue(t[k]))
		}
		return "{" + strings.Join(parts, ", ") + "}"
	default:
		return tomlQuote(fmt.Sprintf("%v", v))
	}
}

func tomlQuote(s string) string {
	escaped := strings.ReplaceAll(s, "\\", "\\\\")
	escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
	escaped = strings.ReplaceAll(escaped, "\n", "\\n")
	return "\"" + escaped + "\""
}
// ImportGitURL — git clone --depth 1 到临时目录, 导入其中所有含 SKILL.md 的 skill 目录。
// 返回每个候选目录的导入结果。(移植 importer.import_git_url)
func ImportGitURL(url, repoRoot string, opts Options) ([]ImportResult, error) {
	tmpRoot, err := os.MkdirTemp("", "skillbank-add-")
	if err != nil {
		return nil, err
	}
	defer os.RemoveAll(tmpRoot)
	tmp := filepath.Join(tmpRoot, "src")
	cmd := exec.Command("git", "clone", "--depth", "1", url, tmp)
	if out, err := cmd.CombinedOutput(); err != nil {
		msg := string(out)
		if len(msg) > 300 {
			msg = msg[:300]
		}
		return nil, fmt.Errorf("git clone 失败: %s", strings.TrimSpace(msg))
	}
	// provenance: 抓源 commit(失败容忍, 仅展示用); opts.Source 供 ImportSkill 写 canonical
	commit := ""
	if out, err := exec.Command("git", "-C", tmp, "rev-parse", "HEAD").Output(); err == nil {
		commit = strings.TrimSpace(string(out))
	}
	opts.Source = url

	var cands []string
	if _, err := os.Stat(filepath.Join(tmp, "SKILL.md")); err == nil {
		cands = []string{tmp}
	} else {
		entries, err := os.ReadDir(tmp)
		if err != nil {
			return nil, err
		}
		for _, e := range entries {
			if _, err := os.Stat(filepath.Join(tmp, e.Name(), "SKILL.md")); err == nil {
				cands = append(cands, filepath.Join(tmp, e.Name()))
			}
		}
		sort.Strings(cands)
	}
	if len(cands) == 0 {
		return nil, fmt.Errorf("%s 里没找到任何 SKILL.md", url)
	}
	var results []ImportResult
	for _, c := range cands {
		res, err := ImportSkill(c, repoRoot, opts)
		if err != nil {
			return results, err
		}
		res.Commit = commit
		results = append(results, res)
	}
	return results, nil
}
