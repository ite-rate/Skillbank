// Interactive — 零依赖的简单交互(编号多选/确认)。(移植 src/skillbank/interactive.py)
//
// 不引第三方交互库(分发二进制要在任意云服务器裸跑)。
// 调用方须先判 stdin 是否 tty;这里不做兜底(CI/管道场景由 CLI 层走 --yes)。
package interactive

import (
	"bufio"
	"fmt"
	"io"
	"sort"
	"strconv"
	"strings"
)

// SelectMany — 编号多选。返回选中的下标列表(0-based, 升序)。
//
// 输入格式: `1,3,5` / 回车(全选) / none(全不选)。
func SelectMany(out io.Writer, in *bufio.Reader, title string, options []string, noneOK bool) []int {
	fmt.Fprintf(out, "\n%s\n", title)
	for i, opt := range options {
		fmt.Fprintf(out, "  [%d] %s\n", i+1, opt)
	}
	for {
		fmt.Fprint(out, "选择(逗号分隔编号, 回车=全选, none=不选): ")
		ans, _ := in.ReadString('\n')
		ans = strings.TrimSpace(strings.TrimSuffix(ans, "\n"))
		switch {
		case ans == "":
			return indexAll(len(options))
		case strings.EqualFold(ans, "none"):
			if noneOK {
				return []int{}
			}
			fmt.Fprintln(out, "  至少选一项")
		default:
			idxs := map[int]bool{}
			ok := true
			for _, x := range strings.Split(strings.ReplaceAll(ans, " ", ""), ",") {
				if x == "" {
					continue
				}
				n, err := strconv.Atoi(x)
				if err != nil || n < 1 || n > len(options) {
					ok = false
					break
				}
				idxs[n-1] = true
			}
			if !ok {
				fmt.Fprintln(out, "  无法解析或越界, 例: 1,3,5")
				continue
			}
			var out2 []int
			for i := range idxs {
				out2 = append(out2, i)
			}
			sort.Ints(out2)
			return out2
		}
	}
}

// Confirm — y/n 确认, 回车 = 默认值。
func Confirm(in *bufio.Reader, msg string, def bool) bool {
	suffix := " [y/N]"
	if def {
		suffix = " [Y/n]"
	}
	fmt.Printf("%s%s ", msg, suffix)
	ans, _ := in.ReadString('\n')
	ans = strings.ToLower(strings.TrimSpace(strings.TrimSuffix(ans, "\n")))
	if ans == "" {
		return def
	}
	return ans == "y" || ans == "yes"
}

func indexAll(n int) []int {
	out := make([]int, n)
	for i := range out {
		out[i] = i
	}
	return out
}