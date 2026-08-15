"""Interactive — 零依赖的简单交互(编号多选/确认)。

不引 questionary(3 台机器都要能裸跑, conda/brew 环境不确定)。
调用方须先判 sys.stdin.isatty();这里不做兜底(CI/管道场景由 CLI 层走 --yes)。
"""

from __future__ import annotations

__all__ = ["select_many", "confirm"]


def select_many(title: str, options: list[str], none_ok: bool = True) -> list[int]:
    """编号多选。返回选中的下标列表(0-based)。

    输入格式: `1,3,5` / `all` 或回车(全选) / `none`(全不选)。
    """
    print(f"\n{title}")
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    while True:
        ans = input(f"选择(逗号分隔编号, 回车=全选, none=不选): ").strip()
        if ans == "":
            return list(range(len(options)))
        if ans.lower() == "none":
            if none_ok:
                return []
            print("  至少选一项")
            continue
        try:
            idxs = sorted({int(x) - 1 for x in ans.replace(" ", "").split(",") if x})
            bad = [i for i in idxs if i < 0 or i >= len(options)]
            if bad:
                print(f"  越界: {[i + 1 for i in bad]}")
                continue
            return idxs
        except ValueError:
            print("  无法解析, 例: 1,3,5")


def confirm(msg: str, default: bool = False) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    ans = input(f"{msg}{suffix} ").strip().lower()
    if ans == "":
        return default
    return ans in ("y", "yes")
