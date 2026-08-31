// Package emit — SkillIR → 各 Agent 目录的 SKILL.md(+ 资源镜像)。
//
// 移植合同(对应 Python emitters/base.py, 字节语义逐条等价):
//   - 字段级透传 EditFrontmatterFields: 无语义变更 → 原样返回(完美字节稳定);
//     未变更字段保留原始行(引号/缩进/顺序); 变更/新增字段重写; 删除字段丢弃
//   - body 直接跟 frontmatter, 不 decode 不 normalize
//   - overrides 递归合并: dict 深并(emitter 已写值优先), 防 Hermes 嵌套元数据丢失
//   - 资源镜像: 整目录结构保真, 目标端已不在源端的条目删除
//
// 与 Python 的声明差异: 变更/新增字段的 dump 排版由 yaml.v3 生成
// (合法且稳定即可); 不变更字段的字节稳定性走原字节拼接路径, 不受影响。
package emit

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/BurntSushi/toml"
	"github.com/ite-rate/skillbank/internal/config"
	"github.com/ite-rate/skillbank/internal/ir"
	"gopkg.in/yaml.v3"
)

// EmitterResult — 一次 emit 的结果(给 manifest + CLI 展示用)。
type EmitterResult struct {
	DeployedPath string
	Method       string // cp | skipped
	Note         string
}

// Emitter — 各 Agent emitter 统一接口。
// TransformFrontmatter 返回 (fm, order): order 是字段产出序
// (Go map 无序, 新增字段追加顺序必须确定 — 对应 Python dict 声明序)。
type Emitter interface {
	// AgentName — agents.toml/machines.toml 里的键。
	AgentName() string
	TransformFrontmatter(ir *ir.SkillIR, cfg *config.AgentConfig) (map[string]any, []string)
	Deploy(ir *ir.SkillIR, deployRoot string, cfg *config.AgentConfig,
		canonicalSkillDir string) (EmitterResult, error)
}

// --- 值语义等值(跨 YAML/TOML 类型差异) ---

func normFloat(f float64) any {
	if f == float64(int64(f)) {
		return int64(f)
	}
	return f
}

func toAnyList(v any) ([]any, bool) {
	switch t := v.(type) {
	case []any:
		return t, true
	case []string:
		out := make([]any, len(t))
		for i, s := range t {
			out[i] = s
		}
		return out, true
	}
	return nil, false
}

// YAMLValueEqual — 语义等值: 处理 []any vs []string、int/int64/float64、
// map 递归。对应 Python `fm_orig.get(key) == new[key]`。
func YAMLValueEqual(a, b any) bool {
	switch at := a.(type) {
	case nil:
		return b == nil
	case bool:
		bt, ok := b.(bool)
		return ok && at == bt
	case string:
		bt, ok := b.(string)
		return ok && at == bt
	case int:
		return yamlNumberEqual(int64(at), b)
	case int64:
		return yamlNumberEqual(at, b)
	case uint64:
		return yamlNumberEqual(int64(at), b)
	case float64:
		return yamlNumberEqual(int64(at), b) || normFloat(at) == b
	case []any, []string:
		al, ok := toAnyList(a)
		if !ok {
			return false
		}
		bl, ok := toAnyList(b)
		if !ok || len(al) != len(bl) {
			return false
		}
		for i := range al {
			if !YAMLValueEqual(al[i], bl[i]) {
				return false
			}
		}
		return true
	case map[string]any:
		bt, ok := b.(map[string]any)
		if !ok || len(at) != len(bt) {
			return false
		}
		for k, v := range at {
			bv, ok := bt[k]
			if !ok || !YAMLValueEqual(v, bv) {
				return false
			}
		}
		return true
	}
	return false
}

func yamlNumberEqual(a int64, b any) bool {
	switch bt := b.(type) {
	case int:
		return a == int64(bt)
	case int64:
		return a == bt
	case uint64:
		return a == int64(bt)
	case float64:
		return float64(a) == bt
	}
	return false
}

// YAMLMapEqual — dict 级语义等值(键集合 + 逐值 YAMLValueEqual)。
func YAMLMapEqual(a, b map[string]any) bool {
	if len(a) != len(b) {
		return false
	}
	for k, v := range a {
		bv, ok := b[k]
		if !ok || !YAMLValueEqual(v, bv) {
			return false
		}
	}
	return true
}

// --- YAML 序化(yaml.Node 手构, 保字段序 + unicode 直出 + 防歧义引号) ---

var ambiguousStrRe = regexp.MustCompile(`\A(|true|false|yes|no|on|off|null|~|0|-?\d+(\.\d+)?([eE][-+]?\d+)?|0x[0-9a-fA-F]+)\z`)

// stringNeedsQuote — 字符串裸输出会被 YAML 解析成非 string 时必须加引号
// (对应 safe_dump 对 "true"/"1.0" 类值的自动引号)。
func stringNeedsQuote(s string) bool {
	if s == "" {
		return true
	}
	if ambiguousStrRe.MatchString(s) {
		return true
	}
	switch s[0] {
	case ' ', '-', '?', ':', ',', '[', ']', '{', '}', '#', '&', '*', '!',
		'|', '>', '\'', '"', '%', '@', '`':
		return true
	}
	if strings.ContainsAny(s, "\n\t") {
		return true
	}
	return strings.HasSuffix(s, " ") || strings.HasSuffix(s, ":")
}

// valueToNode — any → yaml.Node 递归转换。map 键按字典序(通用 map 无声明序,
// 确定性优先); 顶层字段序由调用方在 MappingNode 层控制。
func valueToNode(v any) *yaml.Node {
	switch t := v.(type) {
	case nil:
		return &yaml.Node{Kind: yaml.ScalarNode, Tag: "!!null", Value: ""}
	case bool:
		return &yaml.Node{Kind: yaml.ScalarNode, Tag: "!!bool", Value: fmt.Sprintf("%v", t)}
	case int:
		return &yaml.Node{Kind: yaml.ScalarNode, Tag: "!!int", Value: fmt.Sprintf("%d", t)}
	case int64:
		return &yaml.Node{Kind: yaml.ScalarNode, Tag: "!!int", Value: fmt.Sprintf("%d", t)}
	case float64:
		return &yaml.Node{Kind: yaml.ScalarNode, Tag: "!!float", Value: trimFloat(t)}
	case string:
		n := &yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: t}
		if stringNeedsQuote(t) {
			n.Style = yaml.DoubleQuotedStyle
		}
		return n
	case []any, []string:
		list, _ := toAnyList(t)
		seq := &yaml.Node{Kind: yaml.SequenceNode, Tag: "!!seq"}
		for _, e := range list {
			seq.Content = append(seq.Content, valueToNode(e))
		}
		return seq
	case map[string]any:
		m := &yaml.Node{Kind: yaml.MappingNode, Tag: "!!map"}
		keys := make([]string, 0, len(t))
		for k := range t {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			m.Content = append(m.Content,
				&yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: k},
				valueToNode(t[k]))
		}
		return m
	default:
		// 兜底: fmt 序化成字符串(不期望走到; 走到也可稳定复现)
		return valueToNode(fmt.Sprintf("%v", v))
	}
}

func trimFloat(f float64) string {
	s := fmt.Sprintf("%g", f)
	return s
}

// mappingNode — 按给定 order 构造 mapping node(order 之外的键按字典序补在后面)。
func mappingNode(fm map[string]any, order []string) *yaml.Node {
	m := &yaml.Node{Kind: yaml.MappingNode, Tag: "!!map"}
	done := map[string]bool{}
	for _, k := range order {
		if v, ok := fm[k]; ok {
			m.Content = append(m.Content,
				&yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: k},
				valueToNode(v))
			done[k] = true
		}
	}
	rest := make([]string, 0)
	for k := range fm {
		if !done[k] {
			rest = append(rest, k)
		}
	}
	sort.Strings(rest)
	for _, k := range rest {
		m.Content = append(m.Content,
			&yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: k},
			valueToNode(fm[k]))
	}
	return m
}

func marshalNode(node *yaml.Node) ([]byte, error) {
	doc := &yaml.Node{Kind: yaml.DocumentNode, Content: []*yaml.Node{node}}
	var buf strings.Builder
	enc := yaml.NewEncoder(&buf)
	enc.SetIndent(2)
	if err := enc.Encode(doc); err != nil {
		return nil, err
	}
	enc.Close()
	return []byte(buf.String()), nil
}

// DumpField — 序化单个字段(变更/新增字段用; 对应 Python _dump_field)。
func DumpField(key string, value any) (string, error) {
	m := &yaml.Node{Kind: yaml.MappingNode, Tag: "!!map"}
	m.Content = append(m.Content,
		&yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: key},
		valueToNode(value))
	out, err := marshalNode(m)
	if err != nil {
		return "", err
	}
	return strings.TrimRight(string(out), "\n"), nil
}

// DumpMap — 全量序化 frontmatter dict(无原始字节时的路径, 对应 safe_dump)。
// order 给字段产出序(canonical 声明序 / emitter 产出序)。
func DumpMap(fm map[string]any, order []string) ([]byte, error) {
	return marshalNode(mappingNode(fm, order))
}

// --- 字段级透传(零损耗核心) ---

// topLevelFieldRe — 顶层字段行: `key:` 开头且行首无缩进。block scalar/缩进续行
// 属于上一个字段。
var topLevelFieldRe = regexp.MustCompile(`^([A-Za-z_][A-Za-z0-9_]*):`)

// EditFrontmatterFields — 字段级透传: 未变更字段保原始字节, 仅重写变更/新增/删除字段。
//
//   - 无任何语义变更 → 原样返回(完美字节稳定)
//   - 未变更字段 → 保留原始行(含引号/缩进/顺序)
//   - 变更/新增字段 → 重写该字段
//   - 删除字段(在 orig 不在 new)→ 丢弃
//
// newOrder: new 中新增(不在 raw_text 里)字段的追加序(确定化 Python dict 序)。
func EditFrontmatterFields(rawText string, fmOrig, new map[string]any,
	newOrder []string) (string, error) {
	if YAMLMapEqual(new, fmOrig) {
		return rawText, nil
	}

	lines := strings.Split(rawText, "\n")
	// 定位每个顶层字段 `key:` 的行区间(含其块/续行/注释)。
	var keysOrdered []string
	keyStart := map[string]int{}
	for i, ln := range lines {
		if m := topLevelFieldRe.FindStringSubmatch(ln); m != nil && !startsWithSpace(ln) {
			keysOrdered = append(keysOrdered, m[1])
			keyStart[m[1]] = i
		}
	}
	spans := map[string][2]int{}
	for j, key := range keysOrdered {
		start := keyStart[key]
		end := len(lines)
		if j+1 < len(keysOrdered) {
			end = keyStart[keysOrdered[j+1]]
		}
		spans[key] = [2]int{start, end}
	}

	var blocks []string
	for _, key := range keysOrdered {
		if _, inNew := new[key]; !inNew {
			continue // 已删除字段 → 丢弃
		}
		span := spans[key]
		if YAMLValueEqual(fmOrig[key], new[key]) {
			blocks = append(blocks, strings.Join(lines[span[0]:span[1]], "\n")) // 未变 → 保原始字节
		} else {
			dumped, err := DumpField(key, new[key]) // 变更 → 重写该字段
			if err != nil {
				return "", err
			}
			blocks = append(blocks, dumped)
		}
	}
	// 新增字段(不在 raw_text 里的), 按 newOrder 序追加
	for _, key := range newOrder {
		if _, exists := keyStart[key]; exists {
			continue
		}
		if _, inNew := new[key]; !inNew {
			continue
		}
		dumped, err := DumpField(key, new[key])
		if err != nil {
			return "", err
		}
		blocks = append(blocks, dumped)
	}
	return strings.Join(blocks, "\n"), nil
}

func startsWithSpace(s string) bool {
	return len(s) > 0 && (s[0] == ' ' || s[0] == '\t')
}

// EmitFrontmatterBlock — frontmatter dict → `---\n<yaml>---\n` bytes。
//
// rawText + fmOrig 给定时走字段级透传(未变更字段保原始字节);
// 否则全量 dump(order 给字段产出序)。
func EmitFrontmatterBlock(fm map[string]any, order []string,
	rawText string, fmOrig map[string]any) ([]byte, error) {
	var yamlBytes []byte
	if rawText != "" && fmOrig != nil {
		edited, err := EditFrontmatterFields(rawText, fmOrig, fm, order)
		if err != nil {
			return nil, err
		}
		yamlBytes = []byte(strings.TrimRight(edited, "\n") + "\n")
	} else {
		var err error
		yamlBytes, err = DumpMap(fm, order)
		if err != nil {
			return nil, err
		}
		if len(yamlBytes) > 0 && yamlBytes[len(yamlBytes)-1] != '\n' {
			yamlBytes = append(yamlBytes, '\n')
		}
	}
	// yaml 输出末尾自带 \n; 拼 `---\n<yaml>---\n`(yaml 后 \n 即边界)
	return append([]byte("---\n"), append(yamlBytes, []byte("---\n")...)...), nil
}

// --- overrides(.agent_overrides/<agent>.toml) ---

// LoadAgentOverrides — 从 .agent_overrides/<agent>.toml 读该 Agent 专有字段
// (import 时抽的; 不存在返回空 map)。
func LoadAgentOverrides(canonicalSkillDir, agentName string) (map[string]any, error) {
	ovFile := filepath.Join(canonicalSkillDir, ".agent_overrides", agentName+".toml")
	raw, err := os.ReadFile(ovFile)
	if err != nil {
		if os.IsNotExist(err) {
			return map[string]any{}, nil
		}
		return nil, err
	}
	var out map[string]any
	if err := toml.Unmarshal(raw, &out); err != nil {
		return nil, fmt.Errorf("overrides 解析失败 %s: %w", ovFile, err)
	}
	if out == nil {
		out = map[string]any{}
	}
	return out, nil
}

// mergeOverrideValue — dict 递归并集(emitter 已写值优先), 非 dict 保 emitter 值。
//
// 场景: Hermes emitter 已写 metadata={hermes:{disable-model-invocation}}, overrides
// 里还有 metadata.hermes.{tags, related_skills} —— 整键跳过会丢市场/作者元数据。
func mergeOverrideValue(fmVal, ovVal any) any {
	fmMap, fmOK := fmVal.(map[string]any)
	ovMap, ovOK := ovVal.(map[string]any)
	if fmOK && ovOK {
		merged := map[string]any{}
		for k, v := range fmMap {
			merged[k] = v
		}
		for k, v := range ovMap {
			if _, exists := merged[k]; !exists {
				merged[k] = v
			} else {
				merged[k] = mergeOverrideValue(merged[k], v)
			}
		}
		return merged
	}
	return fmVal // emitter 已写字段优先, 不覆盖
}

// MergeAgentOverrides — overrides 合并进部署 frontmatter:
// 不存在的键直接加; 双 dict 递归合并; 已存在非 dict 保留 emitter 值。
// 返回合并后 fm 与新增键(追加序确定化: 按字典序)。
func MergeAgentOverrides(fm, overrides map[string]any) (map[string]any, []string) {
	merged := map[string]any{}
	for k, v := range fm {
		merged[k] = v
	}
	var added []string
	for k, v := range overrides {
		if _, exists := merged[k]; !exists {
			merged[k] = v
			added = append(added, k)
		} else {
			fmMap, fmOK := merged[k].(map[string]any)
			ovMap, ovOK := v.(map[string]any)
			if fmOK && ovOK {
				merged[k] = mergeOverrideValue(fmMap, ovMap)
			}
		}
	}
	sort.Strings(added)
	return merged, added
}

// --- 公共 helper(全部 emitter 复用) ---

// BuildSkillMDBytes — frontmatter block + body 拼最终字节流。
//
// canonicalSkillDir 给定时叠加该 Agent 的 overrides(dict 递归合并);
// ir.FMRaw 非 nil 时走字段级透传(未翻译字段保原始字节)。
func BuildSkillMDBytes(e Emitter, in *ir.SkillIR, cfg *config.AgentConfig,
	canonicalSkillDir string) ([]byte, error) {
	fm, order := e.TransformFrontmatter(in, cfg)
	if canonicalSkillDir != "" {
		overrides, err := LoadAgentOverrides(canonicalSkillDir, cfg.Name)
		if err != nil {
			return nil, err
		}
		if len(overrides) > 0 {
			merged, added := MergeAgentOverrides(fm, overrides)
			fm, order = merged, append(append([]string{}, order...), added...)
		}
	}
	var rawText string
	var fmOrig map[string]any
	if in.FMRaw != nil {
		rawText = string(in.FMRaw)
		fmOrig = in.FMOrig
	}
	block, err := EmitFrontmatterBlock(fm, order, rawText, fmOrig)
	if err != nil {
		return nil, err
	}
	return append(block, in.Body...), nil
}

// WriteSkillMD — 普通文件写入(自动建父目录)。
func WriteSkillMD(content []byte, path string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, content, 0o644)
}

// mkdirAll — 部署目标目录(emitter 层用, 独立 helper 便于测试桩)。
func mkdirAll(path string) error {
	return os.MkdirAll(path, 0o755)
}

// removeIfSymlinkOrNonDir — 目标是软链或非目录文件 → 删(全部 emitter 的部署前置)。
// 旧语义仅 ZCode(从 ln 改 cp 的迁移); v2.1 起通用化: sync 分类层保证无记录的软链/
// 非目录根本到不了部署, 能走到这里的只有「已收编(有 manifest 记录)」或「--force 放行的
// 非目录」, 摘链/删文件是安全的。真实目录 no-op(镜像写入, 不删)。
func removeIfSymlinkOrNonDir(path string) {
	info, err := os.Lstat(path)
	if err != nil {
		return
	}
	if info.Mode()&os.ModeSymlink != 0 || !info.IsDir() {
		_ = os.Remove(path)
	}
}

// TargetDir — emitter 实际落盘目录的唯一真源(Hermes 有 category 子目录; 其余 =
// deployRoot/<name>)。sync.Collect 的目标分类必须用同一份真源, 否则对 Hermes 查错目录。
func TargetDir(agentName string, in *ir.SkillIR, deployRoot string, cfg *config.AgentConfig) string {
	if agentName == "Hermes" {
		category := cfg.DefaultCategory
		if category == "" {
			category = "imported"
		}
		return filepath.Join(deployRoot, category, in.Name)
	}
	return filepath.Join(deployRoot, in.Name)
}

// WriteResources — canonical skill 目录完整结构保真同步到目标
// (除 SKILL.md / .agent_overrides)。body 里的相对路径引用必须继续有效,
// 所以原样镜像; 同时删除目标端已不在源端的条目(防残留旧文件)。
func WriteResources(targetSkillDir, canonicalSkillDir string) error {
	skip := map[string]bool{"SKILL.md": true, ".agent_overrides": true}

	srcEntries := map[string]bool{}
	srcItems, err := os.ReadDir(canonicalSkillDir)
	if err != nil {
		return err
	}
	for _, e := range srcItems {
		if !skip[e.Name()] {
			srcEntries[e.Name()] = true
		}
	}

	if err := os.MkdirAll(targetSkillDir, 0o755); err != nil {
		return err
	}
	// 删目标端已不在源端的条目(SKILL.md 由 emitter 写, 不动)
	dstItems, err := os.ReadDir(targetSkillDir)
	if err != nil {
		return err
	}
	for _, e := range dstItems {
		if e.Name() == "SKILL.md" {
			continue
		}
		if !srcEntries[e.Name()] {
			if err := removeEntry(filepath.Join(targetSkillDir, e.Name())); err != nil {
				return err
			}
		}
	}
	// 拷源端条目(先清目标同名再拷, 保证内容一致)
	names := make([]string, 0, len(srcEntries))
	for n := range srcEntries {
		names = append(names, n)
	}
	sort.Strings(names)
	for _, name := range names {
		s := filepath.Join(canonicalSkillDir, name)
		d := filepath.Join(targetSkillDir, name)
		if err := removeEntry(d); err != nil && !os.IsNotExist(err) {
			return err
		}
		if err := copyEntry(s, d); err != nil {
			return fmt.Errorf("拷 %s: %w", s, err)
		}
	}
	return nil
}

func removeEntry(path string) error {
	info, err := os.Lstat(path)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	if info.Mode()&os.ModeSymlink != 0 {
		return os.Remove(path)
	}
	if info.IsDir() {
		return os.RemoveAll(path)
	}
	return os.Remove(path)
}

func copyEntry(src, dst string) error {
	info, err := os.Lstat(src)
	if err != nil {
		return err
	}
	if info.Mode()&os.ModeSymlink != 0 {
		target, err := os.Readlink(src)
		if err != nil {
			return err
		}
		return os.Symlink(target, dst)
	}
	if info.IsDir() {
		return copyTree(src, dst)
	}
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	perm := fs.FileMode(info.Mode().Perm())
	return os.WriteFile(dst, data, perm)
}

func copyTree(src, dst string) error {
	if err := os.MkdirAll(dst, 0o755); err != nil {
		return err
	}
	items, err := os.ReadDir(src)
	if err != nil {
		return err
	}
	for _, e := range items {
		if err := copyEntry(filepath.Join(src, e.Name()), filepath.Join(dst, e.Name())); err != nil {
			return err
		}
	}
	return nil
}