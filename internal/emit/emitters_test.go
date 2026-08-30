// 7 个 Agent emitter 测试(移植 test_emitter_claudecode.py 8 条 +
// test_emitter_m3.py 18 条 + test_emitter_m4.py 7 条, 语义等价)。
//
// 每个 emitter 的关键行为:
//   - body 字节与 IR.Body 等值(零损耗硬约束)
//   - TeleAgent: _zh → _cn 镜像 + enabled_at: false
//   - QwenWorkCN: _zh 直传 + enabled_at: false + 作废字段不写
//   - Codex: >1024 截断(触发短语保留) + disable-model-invocation
//   - Hermes: imported/ 类目 + metadata.hermes 命名空间 + 100k 超限 skipped
//   - ZCode: cp 三态(干净/旧软链/真实目录)
//   - kimi: 最小子集, 无禁触发字段
package emit_test

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/ite-rate/skillbank/internal/config"
	"github.com/ite-rate/skillbank/internal/emit"
	"github.com/ite-rate/skillbank/internal/ir"
	"github.com/ite-rate/skillbank/internal/parser"
	"gopkg.in/yaml.v3"
)

// parseCanonical — parser 包入口的简短别名。
func parseCanonical(path string) (*ir.SkillIR, error) {
	return parser.ParseCanonical(path)
}

// repoRoot — 从 cwd 向上找 agents.toml(测试跑在 internal/emit/ 下)。
func repoRoot(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, "agents.toml")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatal("找不到 repo 根(agents.toml)")
		}
		dir = parent
	}
}

func loadAgentsCfg(t *testing.T) *config.AgentsConfig {
	t.Helper()
	cfg, err := config.LoadAgents(filepath.Join(repoRoot(t), "agents.toml"))
	if err != nil {
		t.Fatal(err)
	}
	return cfg
}

// makeCanon — 真实存在的 canonical skill 目录(write_resources 全结构镜像需要)。
func makeCanon(t *testing.T) string {
	t.Helper()
	d := filepath.Join(t.TempDir(), "canonical", "demo")
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(d, "SKILL.md"),
		[]byte("---\nname: demo\ndescription: a skill\nlevel: auto\n---\n## body\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	return d
}

func sp(s string) *string { return &s }

type irOpts struct {
	body        []byte
	level       ir.Level
	description string
	native      *string
	requires    []string
	descZH      *string
	nameZH      *string
}

// makeIR — 测试默认值与 Python _make_ir 对齐。
func makeIR(o irOpts) *ir.SkillIR {
	in := &ir.SkillIR{
		Name:        "demo",
		Description: "a demo skill",
		Body:        []byte("## Step 1\n\ndo something\n"),
		Level:       ir.Auto,
	}
	if o.body != nil {
		in.Body = o.body
	}
	if o.level != "" {
		in.Level = o.level
	}
	if o.description != "" {
		in.Description = o.description
	}
	in.NativeAgent = o.native
	in.Requires = o.requires
	in.DescZH = o.descZH
	in.NameZH = o.nameZH
	return in
}

// splitFMBody — deployed SKILL.md → (frontmatter dict, body bytes)。
func splitFMBody(t *testing.T, raw []byte) (map[string]any, []byte) {
	t.Helper()
	parts := bytes.SplitN(raw, []byte("---\n"), 3)
	if len(parts) != 3 {
		t.Fatalf("deployed SKILL.md 应有 frontmatter 边界: %q", raw)
	}
	var fm map[string]any
	if err := yaml.Unmarshal(parts[1], &fm); err != nil {
		t.Fatalf("frontmatter 解析失败: %v\n%s", err, parts[1])
	}
	return fm, parts[2]
}

func deployTo(t *testing.T, e emit.Emitter, in *ir.SkillIR, cfg *config.AgentConfig,
	canon string) emit.EmitterResult {
	t.Helper()
	res, err := e.Deploy(in, t.TempDir(), cfg, canon)
	if err != nil {
		t.Fatalf("deploy: %v", err)
	}
	return res
}

func readDeployed(t *testing.T, res emit.EmitterResult) []byte {
	t.Helper()
	raw, err := os.ReadFile(res.DeployedPath)
	if err != nil {
		t.Fatalf("读部署产物: %v", err)
	}
	return raw
}

func fmGet(t *testing.T, fm map[string]any, key string) any {
	t.Helper()
	v, ok := fm[key]
	if !ok {
		t.Fatalf("frontmatter 缺字段 %q: %v", key, fm)
	}
	return v
}

func fmStr(t *testing.T, fm map[string]any, key string) string {
	t.Helper()
	s, _ := fmGet(t, fm, key).(string)
	return s
}

// --- ClaudeCode ---

func TestClaudeBodyIdenticalAfterEmit(t *testing.T) {
	// body 字节经过 emitter deploy 后仍与原 IR body 字节等值(前言在外)。
	body := []byte("## Step 1\n\nLine A\nLine B\r\nCRLF preserved\r\n")
	in := makeIR(irOpts{body: body, level: ir.Auto})
	cfg := loadAgentsCfg(t).Get("ClaudeCode")
	res := deployTo(t, emit.ClaudeCodeEmitter{}, in, cfg, makeCanon(t))
	raw := readDeployed(t, res)
	if !bytes.HasSuffix(raw, body) {
		t.Fatalf("body 应完整保留在 deployed SKILL.md 末尾, got tail: %q", raw[len(raw)-len(body):])
	}
	pos := bytes.Index(raw, body)
	if pos == -1 || !bytes.Equal(raw[pos:], body) {
		t.Fatalf("body 字节必须出现在 deployed 文件末尾且与原 IR 等值")
	}
}

func TestClaudeCrlfPreservedInDeployed(t *testing.T) {
	body := []byte("CRLF\r\nmust not be LF\n")
	in := makeIR(irOpts{body: body})
	cfg := loadAgentsCfg(t).Get("ClaudeCode")
	res := deployTo(t, emit.ClaudeCodeEmitter{}, in, cfg, makeCanon(t))
	raw := readDeployed(t, res)
	if !bytes.Contains(raw, []byte("CRLF\r\nmust not be LF\n")) {
		t.Fatal("CRLF body 被 emitter 改成 LF — 零损耗破")
	}
}

func TestClaudeAutoLevelNoDisableInvoke(t *testing.T) {
	// level=auto → frontmatter 不写 disable-model-invocation。
	in := makeIR(irOpts{level: ir.Auto})
	cfg := loadAgentsCfg(t).Get("ClaudeCode")
	res := deployTo(t, emit.ClaudeCodeEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if len(fm) != 2 || fmStr(t, fm, "name") != "demo" || fmStr(t, fm, "description") != "a demo skill" {
		t.Fatalf("auto 级 frontmatter 应只剩 name+description, got: %v", fm)
	}
	if _, ok := fm["disable-model-invocation"]; ok {
		t.Fatal("auto 级不应有 disable-model-invocation")
	}
}

func TestClaudeManualLevelEmitsDisableInvokeTrue(t *testing.T) {
	in := makeIR(irOpts{level: ir.Manual})
	cfg := loadAgentsCfg(t).Get("ClaudeCode")
	res := deployTo(t, emit.ClaudeCodeEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if v := fmGet(t, fm, "disable-model-invocation"); v != true {
		t.Fatalf("manual 级应映射 disable-model-invocation: true, got %v", v)
	}
}

func TestClaudeExperimentalLevelAlsoEmitsDisableInvoke(t *testing.T) {
	in := makeIR(irOpts{level: ir.Experimental})
	cfg := loadAgentsCfg(t).Get("ClaudeCode")
	res := deployTo(t, emit.ClaudeCodeEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if fmGet(t, fm, "disable-model-invocation") != true {
		t.Fatal("experimental 级应映射 disable-model-invocation: true")
	}
}

func TestClaudeCanonicalMetaFieldsNotPolluting(t *testing.T) {
	// canonical 元字段不写进 Claude frontmatter。
	in := makeIR(irOpts{
		native:   sp("TeleAgent"),
		requires: []string{"image_generation", "file_write"},
		descZH:   sp("中文描述"),
	})
	in.NameZH = sp("中文名")
	in.Version = sp("1.0.0")
	in.License = sp("MIT")
	cfg := loadAgentsCfg(t).Get("ClaudeCode")
	res := deployTo(t, emit.ClaudeCodeEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	for _, forbidden := range []string{"native_agent", "requires", "description_zh",
		"name_zh", "version", "license", "level"} {
		if _, ok := fm[forbidden]; ok {
			t.Fatalf("canonical 元字段 %q 污染 Claude frontmatter", forbidden)
		}
	}
}

func TestClaudeLongDescriptionNotTruncated(t *testing.T) {
	// Claude Code 无 description 字符限制。
	longDesc := strings.Repeat("A very long description. ", 100) // > 2000 chars
	in := makeIR(irOpts{description: longDesc})
	cfg := loadAgentsCfg(t).Get("ClaudeCode")
	res := deployTo(t, emit.ClaudeCodeEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if fmStr(t, fm, "description") != longDesc {
		t.Fatal("Claude description 被截断 — 不应有长度限制")
	}
}

func TestClaudeFrontmatterQuotePreservedWhenParsed(t *testing.T) {
	// 从带引号真实 canonical 解析(字段级透传): 未截断 description 引号保留。
	// 回归: 部署侧 safe_dump 全量重建曾去掉引号, 导致部署产物与 canonical 字节不一致。
	dir := t.TempDir()
	canon := filepath.Join(dir, "canonical", "demo")
	if err := os.MkdirAll(canon, 0o755); err != nil {
		t.Fatal(err)
	}
	content := "---\n" +
		"name: demo\n" +
		"description: 'Quoted description with (1) parens (2) and (3) list.'\n" +
		"level: manual\n" +
		"---\n" +
		"# body\n"
	if err := os.WriteFile(filepath.Join(canon, "SKILL.md"), []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	parsed, err := parseCanonical(filepath.Join(canon, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	if parsed.FMRaw == nil {
		t.Fatal("parse 应保留 frontmatter 原始字节")
	}
	cfg := loadAgentsCfg(t).Get("ClaudeCode")
	res, err := emit.ClaudeCodeEmitter{}.Deploy(parsed, filepath.Join(dir, "x"), cfg, canon)
	if err != nil {
		t.Fatal(err)
	}
	raw := readDeployed(t, res)
	if !bytes.Contains(raw, []byte("description: 'Quoted description with (1) parens (2) and (3) list.'")) {
		t.Fatal("部署产物 description 原始引号被丢掉(字段级透传应保留)")
	}
	if !bytes.Contains(raw, []byte("disable-model-invocation: true")) {
		t.Fatal("manual 级应翻译成 disable-model-invocation")
	}
	fm, _ := splitFMBody(t, raw)
	if _, ok := fm["level"]; ok {
		t.Fatal("canonical level 字段不应污染部署产物")
	}
}

// --- TeleAgent ---

func TestTeleagentZhDescMirroredToCn(t *testing.T) {
	// canonical description_zh → TeleAgent description_cn 镜像生成。
	in := makeIR(irOpts{descZH: sp("创意海报设计"), nameZH: sp("创意海报设计")})
	cfg := loadAgentsCfg(t).Get("TeleAgent")
	res := deployTo(t, emit.TeleAgentEmitter{}, in, cfg, makeCanon(t))
	fm, body := splitFMBody(t, readDeployed(t, res))
	if fmStr(t, fm, "description_cn") != "创意海报设计" {
		t.Fatalf("description_cn: %v", fm["description_cn"])
	}
	if fmStr(t, fm, "name_cn") != "创意海报设计" {
		t.Fatalf("name_cn: %v", fm["name_cn"])
	}
	if !bytes.Equal(body, in.Body) {
		t.Fatal("body 零损耗破")
	}
}

func TestTeleagentManualLevelEnabledAtFalse(t *testing.T) {
	// manual/experimental → enabled_at: false(借用 QwenWork 同字段语义)。
	in := makeIR(irOpts{level: ir.Manual})
	cfg := loadAgentsCfg(t).Get("TeleAgent")
	res := deployTo(t, emit.TeleAgentEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if v, ok := fm["enabled_at"]; !ok || v != false {
		t.Fatalf("enabled_at 应为 false, got %v", fm["enabled_at"])
	}
}

func TestTeleagentCanonicalMetaNotPolluting(t *testing.T) {
	in := makeIR(irOpts{native: sp("Hermes"), requires: []string{"web_search"}})
	in.Version = sp("1.0")
	in.License = sp("MIT")
	cfg := loadAgentsCfg(t).Get("TeleAgent")
	res := deployTo(t, emit.TeleAgentEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	for _, forbidden := range []string{"native_agent", "requires", "version", "license", "level"} {
		if _, ok := fm[forbidden]; ok {
			t.Fatalf("元字段 %q 污染 TeleAgent frontmatter", forbidden)
		}
	}
}

// --- QwenWorkCN ---

func TestQwenworkcnZhDescDirectPass(t *testing.T) {
	// canonical description_zh 与 QwenWorkCN 同名, 直传(不镜像)。
	in := makeIR(irOpts{descZH: sp("中文"), nameZH: sp("名")})
	cfg := loadAgentsCfg(t).Get("QwenWorkCN")
	res := deployTo(t, emit.QwenWorkCNEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if fmStr(t, fm, "description_zh") != "中文" {
		t.Fatalf("description_zh: %v", fm["description_zh"])
	}
	if fmStr(t, fm, "name_zh") != "名" {
		t.Fatalf("name_zh: %v", fm["name_zh"])
	}
	// 不存在 description_cn / name_cn(那是 TeleAgent 的镜像后缀)
	if _, ok := fm["description_cn"]; ok {
		t.Fatal("不应有 description_cn")
	}
	if _, ok := fm["name_cn"]; ok {
		t.Fatal("不应有 name_cn")
	}
}

func TestQwenworkcnNoObsoleteFields(t *testing.T) {
	// canonical 元字段与 Qwen Code CLI 作废字段都不主动写(防污染)。
	in := makeIR(irOpts{native: sp("ClaudeCode")})
	cfg := loadAgentsCfg(t).Get("QwenWorkCN")
	res := deployTo(t, emit.QwenWorkCNEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	for _, forbidden := range []string{"priority", "paths", "user-invocable", "source",
		"native_agent", "level"} {
		if _, ok := fm[forbidden]; ok {
			t.Fatalf("字段 %q 不应写入 QwenWorkCN", forbidden)
		}
	}
}

// --- Codex ---

func TestCodexDescriptionTruncatedAt1024(t *testing.T) {
	// description > 1024 → 截断加 "..." 尾。
	longDesc := strings.Repeat("x", 1024+500)
	in := makeIR(irOpts{description: longDesc})
	cfg := loadAgentsCfg(t).Get("Codex")
	res := deployTo(t, emit.CodexEmitter{}, in, cfg, makeCanon(t))
	fm, body := splitFMBody(t, readDeployed(t, res))
	desc := fmStr(t, fm, "description")
	if !strings.HasSuffix(desc, "...") {
		t.Fatal("截断应后缀省略号")
	}
	if len([]rune(desc)) > 1024 {
		t.Fatal("截断后长度不得超过 1024")
	}
	if len(desc) >= len(longDesc) {
		t.Fatal("应截了 500 多字")
	}
	if !bytes.Equal(body, in.Body) {
		t.Fatal("body 不动破")
	}
	if !strings.Contains(res.Note, "truncated") {
		t.Fatalf("note 应含 truncated: %q", res.Note)
	}
}

func TestCodexDescriptionAtBoundaryNotTruncated(t *testing.T) {
	// description 恰好等于 1024 → 不截(保留全长, 无 ...)。
	boundaryDesc := strings.Repeat("y", 1024)
	in := makeIR(irOpts{description: boundaryDesc})
	cfg := loadAgentsCfg(t).Get("Codex")
	res := deployTo(t, emit.CodexEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if fmStr(t, fm, "description") != boundaryDesc {
		t.Fatal("1024 恰好边界不应截")
	}
	if res.Note != "" {
		t.Fatalf("note 应为空: %q", res.Note)
	}
}

func TestCodexUnicodeCharsCountedNotBytes(t *testing.T) {
	// 1024 字符限制是 Unicode 字符数, 不是字节数。
	desc := strings.Repeat("中", 1020) + "aaa" // 1023 chars
	in := makeIR(irOpts{description: desc})
	cfg := loadAgentsCfg(t).Get("Codex")
	res := deployTo(t, emit.CodexEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if fmStr(t, fm, "description") != desc {
		t.Fatal("1023 字符不应截")
	}
	in2 := makeIR(irOpts{description: strings.Repeat("中", 1025)})
	res2 := deployTo(t, emit.CodexEmitter{}, in2, cfg, makeCanon(t))
	fm2, _ := splitFMBody(t, readDeployed(t, res2))
	if len([]rune(fmStr(t, fm2, "description"))) > 1024 {
		t.Fatal("1025 中文字符超限应截到 ≤1024")
	}
}

func TestCodexManualLevelDisableModelInvocationTrue(t *testing.T) {
	in := makeIR(irOpts{level: ir.Experimental})
	cfg := loadAgentsCfg(t).Get("Codex")
	res := deployTo(t, emit.CodexEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if fmGet(t, fm, "disable-model-invocation") != true {
		t.Fatal("experimental 级应映射 disable-model-invocation: true")
	}
}

func TestCodexTruncatePreservesUseWhenTrigger(t *testing.T) {
	// P0 #4: 长 description 含 "Use when ..." 触发短语, 截断后应保留末段。
	longDesc := strings.Repeat("x", 1100) + ". Use when the user asks to generate a poster."
	in := makeIR(irOpts{description: longDesc})
	cfg := loadAgentsCfg(t).Get("Codex")
	res := deployTo(t, emit.CodexEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	desc := fmStr(t, fm, "description")
	if len([]rune(desc)) > 1024 {
		t.Fatal("截断后长度应 ≤ 1024")
	}
	if !strings.Contains(desc, "Use when the user asks to generate a poster.") {
		t.Fatalf("触发短语应保留, got tail: %q", desc[len(desc)-80:])
	}
}

func TestCodexTruncateNoTriggerPlainCut(t *testing.T) {
	// 无触发短语时退化为普通末尾截 + ...(保持原行为)。
	longDesc := strings.Repeat("纯填充内容没有任何触发关键词。", 200)
	in := makeIR(irOpts{description: longDesc})
	cfg := loadAgentsCfg(t).Get("Codex")
	res := deployTo(t, emit.CodexEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	desc := fmStr(t, fm, "description")
	if len([]rune(desc)) > 1024 {
		t.Fatal("截断后长度应 ≤ 1024")
	}
	if !strings.HasSuffix(desc, "...") {
		t.Fatal("无触发短语应普通尾截 + ...")
	}
}

// --- Hermes ---

func TestHermesDeploysIntoCategorySubdir(t *testing.T) {
	// Hermes 默认走 imported/<name>/ 子目录(不污染 creative/)。
	in := makeIR(irOpts{})
	cfg := loadAgentsCfg(t).Get("Hermes")
	res := deployTo(t, emit.HermesEmitter{}, in, cfg, makeCanon(t))
	if !strings.Contains(res.DeployedPath, "imported/demo/SKILL.md") {
		t.Fatalf("应部署进 imported/ 子目录: %s", res.DeployedPath)
	}
	if res.Method != "cp" {
		t.Fatalf("method: %q", res.Method)
	}
}

func TestHermesBodyZeroLossInCategory(t *testing.T) {
	body := []byte("## Hermes body\r\nCRLF\r\npreserved\n")
	in := makeIR(irOpts{body: body})
	cfg := loadAgentsCfg(t).Get("Hermes")
	res := deployTo(t, emit.HermesEmitter{}, in, cfg, makeCanon(t))
	_, deployedBody := splitFMBody(t, readDeployed(t, res))
	if !bytes.Equal(deployedBody, body) {
		t.Fatal("Hermes 类目子目录部署 body 零损耗破")
	}
}

func TestHermesManualLevelMetadataHermesNamespace(t *testing.T) {
	// level manual → frontmatter 加 metadata.hermes.disable-model-invocation: true。
	in := makeIR(irOpts{level: ir.Manual})
	cfg := loadAgentsCfg(t).Get("Hermes")
	res := deployTo(t, emit.HermesEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	md, ok := fm["metadata"].(map[string]any)
	if !ok {
		t.Fatalf("metadata 应为 dict: %v", fm["metadata"])
	}
	hermes, ok := md["hermes"].(map[string]any)
	if !ok {
		t.Fatalf("metadata.hermes 应为 dict: %v", md)
	}
	if hermes["disable-model-invocation"] != true {
		t.Fatalf("metadata.hermes.disable-model-invocation 应为 true: %v", hermes)
	}
}

func TestHermesOverrideMetadataMergesNotOverwrites(t *testing.T) {
	// override 的 metadata.hermes 与 emitter 写的 metadata.hermes 应递归合并。
	// 回归: 此前叠加 overrides 整键跳过, override 里 metadata.hermes.{tags} 全部丢失。
	dir := t.TempDir()
	canon := filepath.Join(dir, "canonical", "demo")
	if err := os.MkdirAll(canon, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(canon, "SKILL.md"),
		[]byte("---\nname: demo\ndescription: a skill\nlevel: manual\n---\n## body\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	ovDir := filepath.Join(canon, ".agent_overrides")
	if err := os.MkdirAll(ovDir, 0o755); err != nil {
		t.Fatal(err)
	}
	ovToml := "[metadata.hermes]\ntags = [\"debugging\", \"troubleshooting\"]\n"
	if err := os.WriteFile(filepath.Join(ovDir, "Hermes.toml"), []byte(ovToml), 0o644); err != nil {
		t.Fatal(err)
	}
	parsed, err := parseCanonical(filepath.Join(canon, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	if parsed.FMRaw == nil {
		t.Fatal("parse 应保留 frontmatter 原始字节")
	}
	cfg := loadAgentsCfg(t).Get("Hermes")
	res, err := emit.HermesEmitter{}.Deploy(parsed, filepath.Join(dir, "x"), cfg, canon)
	if err != nil {
		t.Fatal(err)
	}
	fm, _ := splitFMBody(t, readDeployed(t, res))
	md, _ := fm["metadata"].(map[string]any)
	hermes, _ := md["hermes"].(map[string]any)
	if hermes["disable-model-invocation"] != true {
		t.Fatal("emitter 写的 disable-model-invocation 丢失")
	}
	tags, ok := hermes["tags"].([]any)
	if !ok || len(tags) != 2 || tags[0] != "debugging" || tags[1] != "troubleshooting" {
		t.Fatalf("override 的 tags 未合并进来: %v", hermes["tags"])
	}
}

func TestHermesDescriptionTruncated(t *testing.T) {
	// Hermes description 也有 1024 截断。
	longDesc := strings.Repeat("z", 1024+100)
	in := makeIR(irOpts{description: longDesc})
	cfg := loadAgentsCfg(t).Get("Hermes")
	res := deployTo(t, emit.HermesEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	desc := fmStr(t, fm, "description")
	if len([]rune(desc)) > 1024 {
		t.Fatal("截断后长度应 ≤ 1024")
	}
	if !strings.HasSuffix(desc, "...") {
		t.Fatal("截断应后缀省略号")
	}
}

func TestHermesOversizeFileSkipped(t *testing.T) {
	// deployed SKILL.md 总字符数 > 100_000 → skipped + 不写盘 + 加 note。
	hugeBody := []byte(strings.Repeat("line\n", 20_100)) // ~100_500 chars
	in := makeIR(irOpts{body: hugeBody})
	cfg := loadAgentsCfg(t).Get("Hermes")
	deployRoot := t.TempDir()
	res, err := emit.HermesEmitter{}.Deploy(in, deployRoot, cfg, makeCanon(t))
	if err != nil {
		t.Fatal(err)
	}
	if res.Method != "skipped" {
		t.Fatalf("超大 body 应 skipped, got method=%q", res.Method)
	}
	if !strings.Contains(res.Note, "file_size_max") && !strings.Contains(res.Note, "exceeded") {
		t.Fatalf("note 应含超限提示: %q", res.Note)
	}
	// 不写盘: 目标 skill 目录(imported/<name>/)不应被创建
	targetDir := filepath.Join(deployRoot, "imported", "demo")
	if _, err := os.Stat(targetDir); !os.IsNotExist(err) {
		t.Fatal("skipped 不应创建目标 skill 目录")
	}
}

func TestHermesOversizeOneAgentWhileOthersSync(t *testing.T) {
	// Hermes 超限跳过不影响其他 Agent(Codex 无 file_size_max 限制)。
	hugeBody := []byte(strings.Repeat("line\n", 20_100))
	in := makeIR(irOpts{body: hugeBody})
	canon := makeCanon(t)

	codexCfg := loadAgentsCfg(t).Get("Codex")
	codexRes, err := emit.CodexEmitter{}.Deploy(in, filepath.Join(t.TempDir(), "codex"), codexCfg, canon)
	if err != nil {
		t.Fatal(err)
	}
	if codexRes.Method != "cp" {
		t.Fatalf("Codex 应 cp: %q", codexRes.Method)
	}
	if _, err := os.Stat(codexRes.DeployedPath); err != nil {
		t.Fatal("Codex 部署产物应存在")
	}

	hermesCfg := loadAgentsCfg(t).Get("Hermes")
	hermesRes, err := emit.HermesEmitter{}.Deploy(in, filepath.Join(t.TempDir(), "hermes"), hermesCfg, canon)
	if err != nil {
		t.Fatal(err)
	}
	if hermesRes.Method != "skipped" {
		t.Fatalf("Hermes 应 skipped: %q", hermesRes.Method)
	}
}

// --- ZCode cp 三态(2026-08-16 从 ln 改 cp) ---

func TestZcodeCleanTargetCp(t *testing.T) {
	// 干净目标(~/.zcode/skills/demo 不存在)→ cp 真实文件。
	in := makeIR(irOpts{})
	cfg := loadAgentsCfg(t).Get("ZCode")
	res := deployTo(t, emit.ZCodeEmitter{}, in, cfg, makeCanon(t))
	target := filepath.Dir(res.DeployedPath) // <deployRoot>/demo
	info, err := os.Lstat(target)
	if err != nil {
		t.Fatalf("目标应存在: %v", err)
	}
	if info.Mode()&os.ModeSymlink != 0 {
		t.Fatal("干净目标应是真实目录非软链")
	}
	if _, err := os.Stat(filepath.Join(target, "SKILL.md")); err != nil {
		t.Fatal("SKILL.md 应存在")
	}
	if res.Method != "cp" {
		t.Fatalf("method: %q", res.Method)
	}
}

func TestZcodeExistingSymlinkReplacedWithCp(t *testing.T) {
	// 旧软链 → unlink 后 cp 真实文件(从 ln 改 cp 的迁移)。
	dir := t.TempDir()
	in := makeIR(irOpts{})
	cfg := loadAgentsCfg(t).Get("ZCode")
	deployRoot := filepath.Join(dir, "z")
	if err := os.MkdirAll(deployRoot, 0o755); err != nil {
		t.Fatal(err)
	}
	target := filepath.Join(deployRoot, "demo")
	fake := filepath.Join(dir, "old", "demo")
	if err := os.MkdirAll(fake, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(fake, "SKILL.md"),
		[]byte("---\nname: demo\ndescription: old\n---\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(fake, target); err != nil {
		t.Fatal(err)
	}
	res, err := emit.ZCodeEmitter{}.Deploy(in, deployRoot, cfg, makeCanon(t))
	if err != nil {
		t.Fatal(err)
	}
	info, err := os.Lstat(target)
	if err != nil {
		t.Fatal(err)
	}
	if info.Mode()&os.ModeSymlink != 0 {
		t.Fatal("旧软链应被 unlink 后 cp 替代")
	}
	if !info.IsDir() {
		t.Fatal("cp 后应是真实目录")
	}
	if _, err := os.Stat(filepath.Join(target, "SKILL.md")); err != nil {
		t.Fatal("SKILL.md 应存在")
	}
	if res.Method != "cp" {
		t.Fatalf("method: %q", res.Method)
	}
}

func TestZcodeRealDirCpOverwrite(t *testing.T) {
	// 真实目录(archify 类)→ cp 覆盖(改 cp 后不再 deferred)。
	dir := t.TempDir()
	in := makeIR(irOpts{})
	cfg := loadAgentsCfg(t).Get("ZCode")
	deployRoot := filepath.Join(dir, "z")
	if err := os.MkdirAll(deployRoot, 0o755); err != nil {
		t.Fatal(err)
	}
	target := filepath.Join(deployRoot, "demo")
	if err := os.MkdirAll(target, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(target, "SKILL.md"), []byte("-- OLD --\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	res, err := emit.ZCodeEmitter{}.Deploy(in, deployRoot, cfg, makeCanon(t))
	if err != nil {
		t.Fatal(err)
	}
	if res.Method != "cp" {
		t.Fatalf("method: %q", res.Method)
	}
	raw, err := os.ReadFile(filepath.Join(target, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	if bytes.Contains(raw, []byte("-- OLD --")) {
		t.Fatal("旧 SKILL.md 应被覆盖")
	}
	if !bytes.Contains(raw, []byte("## Step")) {
		t.Fatal("应写入 canonical body")
	}
}

// --- kimi cp ---

func TestKimiDeploysToKimiCodeSkills(t *testing.T) {
	// kimi cp 到 ~/.kimi-code/skills/<name>/, install_dir 与 agents.toml 配置一致。
	cfg := loadAgentsCfg(t).Get("kimi-code")
	if cfg.InstallDir != "~/.kimi-code/skills" {
		t.Fatalf("kimi install_dir 应为 ~/.kimi-code/skills, got %q", cfg.InstallDir)
	}
	in := makeIR(irOpts{})
	res := deployTo(t, emit.KimiEmitter{}, in, cfg, makeCanon(t))
	if res.Method != "cp" {
		t.Fatalf("method: %q", res.Method)
	}
	if filepath.Base(filepath.Dir(res.DeployedPath)) != "demo" {
		t.Fatalf("部署目录名: %s", res.DeployedPath)
	}
	if filepath.Base(res.DeployedPath) != "SKILL.md" {
		t.Fatalf("部署文件名: %s", res.DeployedPath)
	}
}

func TestKimiBodyZeroLoss(t *testing.T) {
	body := []byte("kimi body\r\nwith CRLF\n")
	in := makeIR(irOpts{body: body})
	cfg := loadAgentsCfg(t).Get("kimi-code")
	res := deployTo(t, emit.KimiEmitter{}, in, cfg, makeCanon(t))
	_, deployedBody := splitFMBody(t, readDeployed(t, res))
	if !bytes.Equal(deployedBody, body) {
		t.Fatal("kimi body 零损耗破")
	}
}

func TestKimiFrontmatterMinimalSubset(t *testing.T) {
	// kimi frontmatter 只剩 name + description; canonical 元字段不污染。
	in := makeIR(irOpts{native: sp("Hermes"), requires: []string{"web_search"}})
	in.Version = sp("1.0")
	in.License = sp("MIT")
	cfg := loadAgentsCfg(t).Get("kimi-code")
	res := deployTo(t, emit.KimiEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if len(fm) != 2 {
		t.Fatalf("kimi fm 应只剩 name+description, got %v", fm)
	}
	for _, forbidden := range []string{"native_agent", "requires", "version", "license", "level"} {
		if _, ok := fm[forbidden]; ok {
			t.Fatalf("元字段 %q 污染 kimi frontmatter", forbidden)
		}
	}
}

func TestKimiManualLevelNoDisableInvokeField(t *testing.T) {
	// kimi 配置里 disable_invoke_field 为空; manual 级不写额外 frontmatter 字段。
	cfg := loadAgentsCfg(t).Get("kimi-code")
	if cfg.DisableInvokeField != "" {
		t.Fatalf("kimi 不应配 frontmatter 禁止触发字段, got %q", cfg.DisableInvokeField)
	}
	in := makeIR(irOpts{level: ir.Manual})
	res := deployTo(t, emit.KimiEmitter{}, in, cfg, makeCanon(t))
	fm, _ := splitFMBody(t, readDeployed(t, res))
	if _, ok := fm["disable-model-invocation"]; ok {
		t.Fatal("kimi 不应有 disable-model-invocation")
	}
	if _, ok := fm["enabled_at"]; ok {
		t.Fatal("kimi 不应有 enabled_at")
	}
	if len(fm) != 2 {
		t.Fatal("manual 级也不应给 kimi 加额外字段")
	}
}