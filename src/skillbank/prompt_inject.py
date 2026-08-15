"""Prompt injection — body 顶前言注入(native_agent + 缺能力提示)。

零损耗实现关键:
- body bytes 不动
- 前言是 emitter 写盘时拼到 SKILL.md 输出的 body 之前的独立段(bytes)
- 前言用 markdown blockquote `>` 标注, 物理上 sequence 在 body 前
- parser 回环测试只对 canonical 的 body 段做等值, deployed copy 的 body 不需要回环

注入触发逻辑(决策 4.3 + native_agent 决策):
1. native_agent 非空且 != 当前目标 Agent -> 注入"原生于 X 用 X 模型效果最佳"前言
2. requires 中某能力 = unsupported on target Agent -> 注入"建议换 Agent"硬警告
3. requires 中某能力 = unknown on target Agent -> 注入"未证实"软警告(不阻止执行)
4. 其它 supported / partial 状态不注入
"""

from __future__ import annotations

from typing import Iterable

from skillbank.ir import SkillIR

__all__ = ["inject_prompts", "CapabilityState"]


# 与 capabilities.toml 中的四态对应(字符串)
class CapabilityState:
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    PARTIAL = "partial"


def _native_hint(ir: SkillIR, target_agent: str) -> bytes:
    """原生于 X, 用 X 模型效果最佳。"""
    text = (
        f"> \U0001faa7 来源提示:此 skill 原生于 `{ir.native_agent}`, "
        f"用 `{ir.native_agent}` 模型效果最佳。"
        f"当前在 `{target_agent}` 上运行, 质量可能有差异。\n\n"
    )
    return text.encode("utf-8")


def _unsupported_hint(cap: str, target_agent: str, recommendations: Iterable[str]) -> bytes:
    """建议换 Agent 硬警告(不强制阻止, 留给模型自己判断)。"""
    rec_list = " / ".join(recommendations) if recommendations else "(暂无推荐)"
    text = (
        f"> \u26a0\ufe0f 能力缺失:此任务需要 `{cap}` 能力, 当前 Agent `{target_agent}` 不具备。\n"
        f"> 建议改用具备该能力的 Agent:{rec_list}。\n"
        f"> 如确实要在当前 Agent 上执行, 请人工替代该能力步骤。\n\n"
    )
    return text.encode("utf-8")


def _unknown_hint(cap: str, target_agent: str) -> bytes:
    """未证实软警告(措辞柔和, 不让模型中断执行)。

    与 unsupported 硬警告区分:unknown 仅"未证实",不代表不支持;
    实测过它可能跑得通则继续, 失败再换也不迟。
    """
    text = (
        f"> \u2753 `{cap}` 在当前 Agent `{target_agent}` 上未被证实(可能支持也可能不支持)。"
        f"可尝试先用当前 Agent 执行, 不必中止 — 仅在收到能力不可用时再斟酌是否换已证实 Agent。\n\n"
    )
    return text.encode("utf-8")


def inject_prompts(
    ir: SkillIR,
    target_agent: str,
    capability_lookup,
) -> bytes:
    """生成 body 顶的前言 bytes。

    capability_lookup: Callable[[capability_tag, agent_name]) -> state_str
        (M2 起把 capabilities.CapabilityMatrix.query 包成 callable 传进来)

    返回前言 bytes(不含 body; 调用方拼到 body 前面)。空也返回 b"" 让调用方安全拼接。
    """
    chunks: list[bytes] = []

    # 1. native_agent 前言
    if ir.native_agent and ir.native_agent != target_agent:
        chunks.append(_native_hint(ir, target_agent))

    # 2/3. 能力提示 — 收 unsupported/unknown 两态, 并查哪些 Agent 支持作 recommendations
    matrix = capability_lookup.matrix if hasattr(capability_lookup, "matrix") else capability_lookup
    for cap in ir.requires:
        state = matrix.query(cap, target_agent)
        if state == CapabilityState.UNSUPPORTED:
            recs = matrix.recommend_agents(cap, exclude=target_agent)
            chunks.append(_unsupported_hint(cap, target_agent, recs))
        elif state == CapabilityState.UNKNOWN:
            chunks.append(_unknown_hint(cap, target_agent))

    return b"".join(chunks)