// Package cli — Skillbank CLI 子命令 dispatch。(移植 src/skillbank/cli.py)
//
// 子命令:
//
//	sync           canonical → 该机器 Agents(collect→show→confirm→execute;无 flag 交互选)
//	use            绑定本机身份(哪个 machines.toml 机器别名);--machine 默认取它
//	add            导入新 skill(本地路径 / git URL)
//	import         从某 Agent 目录反向导入既有 skill 进 canonical
//	rm             删除部署副本(manifest 驱动;canonical 保留)
//	list           部署状态表(skill × agent)
//	doctor         环境体检(配置/路径/manifest/canonical/git)
//	scan           探测本机 Agent skills 目录, 确认写入 machines.toml
//	zcode-cleanup  清理 ~/.zcode/skills 真实副本(交互确认 + mv 备份 → 软链 canonical)
//	set-level / archive / unarchive / archive-list
//
// Go 版差异:repo 根不再是 __file__ 推导, 由 App.RepoRoot 显式传入
// (cmd/skillbank 按 --repo > env > config.toml > cwd 向上 链解析)。
package cli

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/ite-rate/skillbank/internal/config"
	"github.com/ite-rate/skillbank/internal/identity"
)

// BindingNote — 绑定说明(cli.py BINDING_NOTE 等价)。
var BindingNote = "绑定文件 ./" + identity.BindingFilename + ", gitignored"

// App — 一次 CLI 运行的上下文。测试可注入 RepoRoot/TTY/In。
type App struct {
	RepoRoot string
	TTY      bool          // 调用方判好 stdin+stdout 是否 tty
	In       *bufio.Reader // 交互输入(测试可注入;nil = os.Stdin)
}

func (a *App) in() *bufio.Reader {
	if a.In != nil {
		return a.In
	}
	return bufio.NewReader(os.Stdin)
}

// ManifestPath — repo 的 deployments.json 路径。
func (a *App) ManifestPath() string {
	return filepath.Join(a.RepoRoot, "manifests", "deployments.json")
}

func (a *App) loadConfigs() (*config.AgentsConfig, *config.MachinesConfig, error) {
	agentsCfg, err := config.LoadAgents(filepath.Join(a.RepoRoot, "agents.toml"))
	if err != nil {
		return nil, nil, err
	}
	machines, err := config.LoadMachines(
		filepath.Join(a.RepoRoot, "machines.toml"), agentsCfg.Names())
	if err != nil {
		return nil, nil, err
	}
	return agentsCfg, machines, nil
}

// resolveMachine — 解析本命令的 machine:显式 flag > 本机绑定;未绑定 → 报错退出。
//
// destructive: 命令会动本机磁盘(sync 执行/rm/archive 等)— 显式 flag 与
// 本机绑定不同时打 ⚠(防在别的机器上按它机名义删/标本机文件)。
// 返回 exitCode != 0 表示已打印错误, 调用方直接返回。
func (a *App) resolveMachine(cmd string, machines *config.MachinesConfig,
	explicit string, destructive bool) (machine string, exitCode int) {
	machine, err := identity.ResolveMachine(a.RepoRoot, machines, explicit)
	if err != nil {
		fmt.Printf("[%s] ✗ %v\n", cmd, err)
		return "", 2
	}
	if destructive && explicit != "" {
		bound := identity.ReadBinding(a.RepoRoot)
		if bound != "" && bound != explicit {
			fmt.Printf("  ⚠ 显式 --machine %q ≠ 本机绑定 %q:以下将对本机磁盘按 %q 名义操作\n",
				explicit, bound, explicit)
		}
	}
	return machine, 0
}

// confirm — y/n 确认(等价 interactive.confirm, 但走 App 的输入)。
func (a *App) confirm(msg string, def bool) bool {
	suffix := " [y/N]"
	if def {
		suffix = " [Y/n]"
	}
	fmt.Printf("%s%s ", msg, suffix)
	ans, _ := a.in().ReadString('\n')
	ans = strings.ToLower(strings.TrimSpace(strings.TrimSuffix(ans, "\n")))
	if ans == "" {
		return def
	}
	return ans == "y" || ans == "yes"
}

// input — 读一行(交互问句用)。
func (a *App) input(prompt string) string {
	fmt.Print(prompt)
	ans, _ := a.in().ReadString('\n')
	return strings.TrimSpace(strings.TrimSuffix(ans, "\n"))
}

// selectMany — 编号多选(等价 interactive.select_many, 但走 App 的输入)。
func (a *App) selectMany(title string, options []string, noneOK bool) []int {
	fmt.Printf("\n%s\n", title)
	for i, opt := range options {
		fmt.Printf("  [%d] %s\n", i+1, opt)
	}
	for {
		fmt.Print("选择(逗号分隔编号, 回车=全选, none=不选): ")
		ans := a.input("")
		switch {
		case ans == "":
			out := make([]int, len(options))
			for i := range out {
				out[i] = i
			}
			return out
		case strings.EqualFold(ans, "none"):
			if noneOK {
				return []int{}
			}
			fmt.Println("  至少选一项")
		default:
			var idxs []int
			ok := true
			for _, x := range strings.Split(strings.ReplaceAll(ans, " ", ""), ",") {
				if x == "" {
					continue
				}
				n := 0
				valid := true
				for _, c := range x {
					if c < '0' || c > '9' {
						valid = false
						break
					}
					n = n*10 + int(c-'0')
				}
				if !valid || n < 1 || n > len(options) {
					ok = false
					break
				}
				idxs = append(idxs, n-1)
			}
			if !ok {
				fmt.Println("  无法解析或越界, 例: 1,3,5")
				continue
			}
			return idxs
		}
	}
}

// renameCallback — 重名时交互问改名:回车=建议名 / m=<自定> / s=skip。
// 返回 ("", true) 表示用户跳过。
func (a *App) renameCallback(origName, suggested, native string) (string, bool) {
	if native == "" {
		native = "?"
	}
	fmt.Printf("\n  ⚠ 重名冲突: name=%q body 与既有不同(native=%s)\n", origName, native)
	fmt.Printf("  建议名: %s\n", suggested)
	ans := a.input("  改名为? [回车=建议名 / m=<自定名> / s=跳过]: ")
	if strings.EqualFold(ans, "s") {
		return "", true
	}
	if strings.HasPrefix(strings.ToLower(ans), "m=") && len(ans) > 2 {
		return strings.TrimSpace(ans[2:]), false
	}
	return suggested, false
}

// --- flag 解析(极简, 镜像 argparse 的子集) ---

type flagSet struct {
	args     []string // positional
	str      map[string]*string
	boolF    map[string]*bool
	strSlice map[string]*[]string
	allowed  map[string]bool // 已注册 flag(未注册 → 报错)
}

func newFlagSet(flags ...string) *flagSet {
	fs := &flagSet{str: map[string]*string{}, boolF: map[string]*bool{},
		strSlice: map[string]*[]string{}, allowed: map[string]bool{}}
	for _, f := range flags {
		fs.allowed[f] = true
	}
	return fs
}

func (fs *flagSet) strP(name, def string) *string {
	p := new(string)
	*p = def
	fs.str[name] = p
	return p
}

func (fs *flagSet) boolP(name string) *bool {
	p := new(bool)
	fs.boolF[name] = p
	return p
}

func (fs *flagSet) sliceP(name string) *[]string {
	p := new([]string)
	fs.strSlice[name] = p
	return p
}

// parse — 解析 args。返回 (usage-error message, true) 时调用方打 usage 退出 2。
func (fs *flagSet) parse(args []string) (string, bool) {
	i := 0
	for i < len(args) {
		arg := args[i]
		if !strings.HasPrefix(arg, "-") || arg == "-" {
			fs.args = append(fs.args, arg)
			i++
			continue
		}
		name := strings.TrimLeft(arg, "-")
		val := ""
		hasVal := false
		if eq := strings.Index(name, "="); eq >= 0 {
			val, name = name[eq+1:], name[:eq]
			hasVal = true
		}
		if !fs.allowed[name] {
			return fmt.Sprintf("无法识别的参数: %s", arg), true
		}
		switch {
		case fs.str[name] != nil:
			if !hasVal {
				if i+1 >= len(args) {
					return fmt.Sprintf("参数 %s 需要值", name), true
				}
				i++
				val = args[i]
			}
			*fs.str[name] = val
		case fs.strSlice[name] != nil:
			if !hasVal {
				if i+1 >= len(args) {
					return fmt.Sprintf("参数 %s 需要值", name), true
				}
				i++
				val = args[i]
			}
			*fs.strSlice[name] = append(*fs.strSlice[name], val)
		default: // bool
			if hasVal {
				*fs.boolF[name] = val == "true" || val == "1"
			} else {
				*fs.boolF[name] = true
			}
		}
		i++
	}
	return "", false
}

const usageHeader = "Skillbank: 中心 skill 仓库 → 7 个 AI agent(body 字节零损耗)\n\n子命令:\n" +
	"  sync / use / add / import / install / rm / list / doctor / scan / zcode-cleanup\n" +
	"  set-level / archive / unarchive / archive-list / init / bootstrap / pull\n"

// Run — 分发子命令, 返回进程 exit code。
func (a *App) Run(args []string) int {
	if len(args) == 0 {
		fmt.Fprint(os.Stderr, usageHeader)
		return 2
	}
	cmd, rest := args[0], args[1:]
	switch cmd {
	case "sync":
		return a.cmdSync(rest)
	case "add":
		return a.cmdAdd(rest)
	case "import":
		return a.cmdImport(rest)
	case "install":
		return a.cmdInstall(rest)
	case "pull":
		return a.cmdPull(rest)
	case "rm":
		return a.cmdRm(rest)
	case "list":
		return a.cmdList(rest)
	case "doctor":
		return a.cmdDoctor(rest)
	case "use":
		return a.cmdUse(rest)
	case "scan":
		return a.cmdScan(rest)
	case "zcode-cleanup":
		return a.cmdZcodeCleanup(rest)
	case "set-level":
		return a.cmdSetLevel(rest)
	case "archive":
		return a.cmdArchive(rest)
	case "unarchive":
		return a.cmdUnarchive(rest)
	case "archive-list":
		return a.cmdArchiveList(rest)
	case "init":
		return a.cmdInit(rest)
	case "bootstrap":
		return a.cmdBootstrap(rest)
	default:
		fmt.Fprintf(os.Stderr, "未知子命令: %s\n\n%s", cmd, usageHeader)
		return 2
	}
}