// zcode-cleanup / set-level / archive / unarchive / archive-list 子命令。
// (移植 cli.py _cmd_zcode_cleanup/_cmd_set_level/_cmd_archive/_cmd_unarchive/_cmd_archive_list)
package cli

import (
	"fmt"
	iofs "io/fs"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/ite-rate/skillbank/internal/archive"
	"github.com/ite-rate/skillbank/internal/emit"
	"github.com/ite-rate/skillbank/internal/ir"
	"github.com/ite-rate/skillbank/internal/manifest"
	"github.com/ite-rate/skillbank/internal/parser"
)

// cmdZcodeCleanup — 把 ZCode skills 目录里的真实副本 mv 备份后软链到 canonical(逐个交互确认)。
func (a *App) cmdZcodeCleanup(args []string) int {
	fs := newFlagSet("machine", "yes", "dry-run")
	machineFlag := fs.strP("machine", "")
	yes := fs.boolP("yes")
	dryRun := fs.boolP("dry-run")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[zcode-cleanup] %s\n", msg)
		return 2
	}

	_, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[zcode-cleanup] ✗ %v\n", err)
		return 1
	}
	machine, rc := a.resolveMachine("zcode-cleanup", machines, *machineFlag, false)
	if rc != 0 {
		return rc
	}
	zdir := machines.GetSkillsDir(machine, "ZCode")
	if zdir == "" {
		fmt.Printf("[zcode-cleanup] ZCode skills 目录未配置(machine=%s)\n", machine)
		return 2
	}
	if _, err := os.Stat(zdir); err != nil {
		fmt.Printf("[zcode-cleanup] ZCode skills 目录不存在: %s(machine=%s)\n", zdir, machine)
		return 2
	}

	backupRoot := filepath.Join(filepath.Dir(zdir), "skills.bak",
		time.Now().Format("20060102-150405"))
	converted := 0

	entries, err := os.ReadDir(zdir)
	if err != nil {
		fmt.Printf("[zcode-cleanup] ✗ %v\n", err)
		return 1
	}
	var reals []iofs.DirEntry
	for _, e := range entries {
		if fi, err := os.Lstat(filepath.Join(zdir, e.Name())); err == nil && fi.Mode()&os.ModeSymlink == 0 {
			reals = append(reals, e)
		}
	}
	if len(reals) == 0 {
		fmt.Printf("[zcode-cleanup] 无真实副本需要处理(共 %d 项, 全是软链/文件)\n", len(entries))
		return 0
	}

	for _, e := range reals {
		name := e.Name()
		real := filepath.Join(zdir, name)
		canonical := filepath.Join(a.RepoRoot, "skills", name)
		_, hasCanonical := os.Stat(filepath.Join(canonical, "SKILL.md"))
		nItems := countEntries(real)
		fmt.Printf("\n  %s: 真实目录(%d 项)\n", name, nItems)
		action := ""
		if hasCanonical == nil {
			fmt.Printf("    canonical 存在: %s\n", canonical)
			action = "备份+软链"
		} else {
			fmt.Printf("    canonical 不存在 — 先跑: skillbank import %s\n", real)
		}

		if *dryRun {
			if action != "" {
				fmt.Printf("    [dry-run] WOULD %s (备份到 %s)\n", action, filepath.Join(backupRoot, name))
			} else {
				fmt.Println("    [dry-run] 仅提示 import")
			}
			continue
		}
		if hasCanonical != nil {
			continue // 无 canonical 不能链, 不动
		}

		doIt := *yes || !a.TTY
		if !doIt {
			doIt = a.confirm(fmt.Sprintf("    %s: mv → %s 再 ln -s canonical?",
				action, filepath.Join(backupRoot, name)), false)
		}
		if !doIt {
			fmt.Println("    跳过")
			continue
		}

		if err := os.MkdirAll(backupRoot, 0o755); err != nil {
			fmt.Printf("    ✗ %v\n", err)
			continue
		}
		if err := os.Rename(real, filepath.Join(backupRoot, name)); err != nil {
			fmt.Printf("    ✗ %v\n", err)
			continue
		}
		abs, _ := filepath.Abs(canonical)
		if err := os.Symlink(abs, filepath.Join(zdir, name)); err != nil {
			fmt.Printf("    ✗ 软链失败: %v\n", err)
			continue
		}
		fmt.Printf("    ✓ 备份 %s + 软链 → %s\n", filepath.Join(backupRoot, name), canonical)
		converted++
	}

	fmt.Printf("\n[zcode-cleanup] 完成: 转换 %d 个(dry-run=%v)\n", converted, *dryRun)
	if converted > 0 && !*dryRun {
		fmt.Printf("[zcode-cleanup] 备份在 %s(确认 ZCode 正常后可删)\n", backupRoot)
	}
	return 0
}

func countEntries(dir string) int {
	n := 0
	_ = filepath.WalkDir(dir, func(_ string, _ iofs.DirEntry, _ error) error {
		n++
		return nil
	})
	return n
}

// cmdSetLevel — 修改 canonical SKILL.md 的 level 字段(改触发策略)。
//
// 被 level 切换触发的下游变化由下次 `skillbank sync` 推动:
//   - 改 disable → 该 skill 在所有 Agent 副本被清(下次 sync)
//   - 改 auto   → 同步后 Agent 前端的 disable-model-invocation 也跟着消
func (a *App) cmdSetLevel(args []string) int {
	if len(args) < 2 {
		fmt.Fprintln(os.Stderr, "[set-level] 用法: skillbank set-level <name> <level>")
		return 2
	}
	name, newLevel := args[0], args[1]
	if !validLevel(newLevel) {
		fmt.Fprintf(os.Stderr, "[set-level] level 必须是 %s 之一\n", strings.Join(levelValues, "/"))
		return 2
	}
	skillMD := filepath.Join(a.RepoRoot, "skills", name, "SKILL.md")
	if _, err := os.Stat(skillMD); err != nil {
		fmt.Printf("[set-level] canonical 不存在: skills/%s/\n", name)
		return 2
	}

	oldIR, err := parser.ParseCanonical(skillMD)
	if err != nil {
		fmt.Printf("[set-level] ✗ %v\n", err)
		return 1
	}
	if string(oldIR.Level) == newLevel {
		fmt.Printf("[set-level] %s 已是 %s, 无变化\n", name, newLevel)
		return 0
	}
	oldLevel := string(oldIR.Level)
	oldIR.Level = ir.Level(newLevel)
	// 重写 canonical(body bytes 原样不丢 — emit_canonical 字段级透传保证)
	if err := emit.EmitCanonical(oldIR, skillMD); err != nil {
		fmt.Printf("[set-level] ✗ %v\n", err)
		return 1
	}
	fmt.Printf("[set-level] %s: %s → %s\n", name, oldLevel, newLevel)
	fmt.Printf("  canonical 已更新: %s\n", skillMD)
	fmt.Println("  下一步: skillbank sync 推到各 Agent(同步行为因 level 已变而不同)")
	if newLevel == "disable" {
		fmt.Println("    ⚠ disable 级:下次 sync 会清掉所有已部署副本(canonical 保留, git 可恢复)")
	} else if oldLevel == "disable" {
		fmt.Println("    ⚠ 从 disable 改回:下次 sync 会重新部署该 skill")
	}
	return 0
}

// cmdArchive — 归档 skill: mv canonical → skills/.archive/ + 清已部署副本(canonical 移走, 非删)。
//
// 与 rm 的区别: rm 只删部署副本保留 canonical 在 skills/ 里; archive 把 canonical
// 也移到 .archive/(list 默认不显示, 完全"暂存"), 需要时 unarchive 恢复。
func (a *App) cmdArchive(args []string) int {
	fs := newFlagSet("machine", "dry-run")
	machineFlag := fs.strP("machine", "")
	dryRun := fs.boolP("dry-run")
	if msg, bad := fs.parse(args); bad {
		fmt.Fprintf(os.Stderr, "[archive] %s\n", msg)
		return 2
	}
	if len(fs.args) == 0 {
		fmt.Fprintln(os.Stderr, "[archive] 缺 <name>(canonical skill 名)")
		return 2
	}
	name := fs.args[0]

	_, machines, err := a.loadConfigs()
	if err != nil {
		fmt.Printf("[archive] ✗ %v\n", err)
		return 1
	}
	machine, rc := a.resolveMachine("archive", machines, *machineFlag, true)
	if rc != 0 {
		return rc
	}

	if *dryRun {
		// dry-run: 不动盘, 只报告会做什么
		if !archive.SkillExists(a.RepoRoot, name) {
			fmt.Printf("[archive] %q: canonical 不存在(skills/%s/)\n", name, name)
			if archive.ArchivedExists(a.RepoRoot, name) {
				fmt.Printf("  (已在归档区: skills/.archive/%s/)\n", name)
			}
			return 0
		}
		fmt.Printf("[archive] %q: WOULD mv skills/%s/ → skills/.archive/%s/\n", name, name, name)
		m, err := manifest.Load(a.ManifestPath())
		if err != nil {
			fmt.Printf("[archive] ✗ %v\n", err)
			return 1
		}
		recs := m.Find(name, "", "")
		local, remote := 0, 0
		for _, r := range recs {
			if r.Machine == machine {
				local++
			} else {
				remote++
			}
		}
		fmt.Printf("  WOULD 清本机副本 %d 个\n", local)
		fmt.Printf("  WOULD 标其它机器 pending %d 个\n", remote)
		return 0
	}

	m, err := manifest.Load(a.ManifestPath())
	if err != nil {
		fmt.Printf("[archive] ✗ %v\n", err)
		return 1
	}
	msg, err := archive.ArchiveSkill(a.RepoRoot, name, m, machine)
	if err != nil {
		fmt.Printf("[archive] ✗ %v\n", err)
		return 1
	}
	fmt.Printf("[archive] %s\n", msg)
	return 0
}

// cmdUnarchive — 恢复归档 skill: mv 回 skills/ + set-level manual(默认不自动触发, 审过再 set-level auto)。
func (a *App) cmdUnarchive(args []string) int {
	if len(args) == 0 {
		fmt.Fprintln(os.Stderr, "[unarchive] 缺 <name>(归档区 skill 名)")
		return 2
	}
	msg, err := archive.UnarchiveSkill(a.RepoRoot, args[0])
	if err != nil {
		fmt.Printf("[unarchive] ✗ %v\n", err)
		return 1
	}
	fmt.Printf("[unarchive] %s\n", msg)
	if strings.Contains(msg, "已恢复") {
		fmt.Printf("  下一步: skillbank sync -s %s 重新部署\n", args[0])
	}
	return 0
}

// cmdArchiveList — 列出归档区的 skill。
func (a *App) cmdArchiveList(args []string) int {
	archived := archive.ListArchived(a.RepoRoot)
	if len(archived) == 0 {
		fmt.Println("[archive-list] 归档区为空")
		return 0
	}
	fmt.Printf("[archive-list] %d 个已归档 skill(skills/.archive/):\n", len(archived))
	for _, name := range archived {
		fmt.Printf("  - %s\n", name)
	}
	fmt.Println("  恢复: skillbank unarchive <name>")
	return 0
}