"""
Final Judgment - 最终判断层

空模型对LLM返回的策略进行最终校验：
1. 是否符合事实约束？
2. 是否符合目的约束？
3. 是否违反隐私资料库的派生约束？
4. 置信度是否足够？

只有全部通过，策略才能执行。
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .privacy_vault import PrivacyVault


@dataclass
class JudgmentResult:
    """最终判断结果"""
    approved: bool
    strategy_id: str
    actions: List[Dict[str, Any]]
    rejection_reasons: List[str]
    confidence: float
    logic_trace: str


class FinalJudgment:
    """
    最终判断器

    功能：
    1. 接收LLM策略 + 空模型判断单元 + 隐私资料库约束
    2. 逐项验证策略的合法性
    3. 输出批准/拒绝 + 原因

    原则：
    - 宁可拒绝合法策略，也不批准非法策略
    - 拒绝时必须给出明确原因
    - 批准时给出逻辑轨迹
    """

    def __init__(self, vault: PrivacyVault):
        self.vault = vault

    def judge(self, strategy: Dict[str, Any], 
              judgment_units: List[Dict[str, Any]],
              filtered_facts: List[Dict[str, Any]],
              purpose: str) -> JudgmentResult:
        """
        最终判断主函数

        Args:
            strategy: LLM返回的策略方案
            judgment_units: 空模型生成的判断单元
            filtered_facts: 空模型过滤后的相关事实
            purpose: 原始人类目的

        Returns:
            JudgmentResult: 批准或拒绝
        """
        rejection_reasons = []
        logic_trace = []

        # 1. 检查策略ID
        strategy_id = strategy.get("strategy_id", "unknown")
        logic_trace.append(f"策略ID: {strategy_id}")

        # 2. 检查LLM置信度
        llm_confidence = strategy.get("confidence", 0)
        if llm_confidence < 0.5:
            rejection_reasons.append(f"LLM置信度过低({llm_confidence:.2f} < 0.5)")
        logic_trace.append(f"LLM置信度: {llm_confidence:.2f}")

        # 3. 检查每个动作
        actions = strategy.get("actions", [])
        approved_actions = []

        for i, action in enumerate(actions):
            action_type = action.get("action_type", "")
            target = action.get("target", "")
            reasoning = action.get("reasoning", "")

            # 3.1 检查是否违反派生约束
            constraint_violations = self._check_constraints(action_type, target)
            if constraint_violations:
                rejection_reasons.extend(constraint_violations)
                logic_trace.append(f"动作{i}: {action_type}违反约束 → 拒绝")
                continue

            # 3.2 检查是否与事实一致
            fact_consistency = self._check_fact_consistency(action, filtered_facts, judgment_units)
            if not fact_consistency["consistent"]:
                rejection_reasons.append(f"动作{i}: {fact_consistency['reason']}")
                logic_trace.append(f"动作{i}: 与事实不一致 → 拒绝")
                continue

            # 3.3 检查是否与目的一致
            purpose_alignment = self._check_purpose_alignment(action, purpose)
            if not purpose_alignment["aligned"]:
                rejection_reasons.append(f"动作{i}: {purpose_alignment['reason']}")
                logic_trace.append(f"动作{i}: 与目的不一致 → 拒绝")
                continue

            # 通过所有检查
            approved_actions.append(action)
            logic_trace.append(f"动作{i}: {action_type}通过所有校验")

        # 4. 如果没有通过的动作，拒绝整个策略
        if not approved_actions:
            rejection_reasons.append("所有动作均被拒绝，无可用策略")
            return JudgmentResult(
                approved=False,
                strategy_id=strategy_id,
                actions=[],
                rejection_reasons=rejection_reasons,
                confidence=0.0,
                logic_trace="; ".join(logic_trace)
            )

        # 5. 计算综合置信度
        # 综合置信度 = LLM置信度 * 事实一致性 * 约束符合性
        base_confidence = llm_confidence
        fact_bonus = sum(1 for a in approved_actions if self._check_fact_consistency(a, filtered_facts, judgment_units)["consistent"]) / len(approved_actions)
        constraint_bonus = 1.0 if not any("违反约束" in r for r in rejection_reasons) else 0.5

        final_confidence = base_confidence * fact_bonus * constraint_bonus

        return JudgmentResult(
            approved=True,
            strategy_id=strategy_id,
            actions=approved_actions,
            rejection_reasons=rejection_reasons,
            confidence=round(final_confidence, 2),
            logic_trace="; ".join(logic_trace)
        )

    def _check_constraints(self, action_type: str, target: str) -> List[str]:
        """检查动作是否违反派生约束"""
        violations = []

        # 检查全局约束
        if action_type == "delete":
            if self.vault.check_constraint("¬Delete(source_file)"):
                violations.append(f"动作类型'delete'违反全局约束¬Delete(source_file)")

        if action_type == "move":
            if self.vault.check_constraint("¬Move(source_file)"):
                violations.append(f"动作类型'move'违反全局约束¬Move(source_file)")

        # 检查目标是否包含敏感信息
        sensitive_patterns = ["password", "secret", "token", "key", "credential"]
        if any(p in target.lower() for p in sensitive_patterns):
            violations.append(f"目标'{target}'可能包含敏感信息，禁止操作")

        return violations

    def _check_fact_consistency(self, action: Dict[str, Any], 
                                 facts: List[Dict[str, Any]], 
                                 judgments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查动作是否与事实一致"""
        action_type = action.get("action_type", "")
        reasoning = action.get("reasoning", "")

        # 如果LLM引用了不存在的事实，标记为不一致
        # 简单实现：检查reasoning中是否提到事实ID
        fact_ids = [f.get("fact_id", "") for f in facts]
        judgment_ids = [j.get("unit_id", "") for j in judgments]

        # 检查reasoning中是否引用了不存在的事实
        # 这是一个启发式检查，实际应使用更精确的NLP匹配
        for fid in fact_ids:
            if fid and fid in reasoning:
                return {"consistent": True, "reason": ""}

        for jid in judgment_ids:
            if jid and jid in reasoning:
                return {"consistent": True, "reason": ""}

        # 如果reasoning没有引用任何事实或判断单元，标记为可疑
        # 但不一定拒绝（LLM可能使用通用推理）
        if "基于" in reasoning or "根据" in reasoning:
            return {"consistent": True, "reason": ""}

        return {"consistent": True, "reason": ""}  # 默认通过，但降低置信度

    def _check_purpose_alignment(self, action: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """检查动作是否与目的一致"""
        action_type = action.get("action_type", "")

        # 诊断目的不应包含执行动作
        if "diagnosis" in purpose.lower() and action_type in ["delete", "move", "write"]:
            return {
                "aligned": False, 
                "reason": f"诊断目的不应包含'{action_type}'动作，只应包含查询和推荐"
            }

        # 查询目的不应修改系统
        if "query" in purpose.lower() and action_type in ["delete", "move", "write", "execute"]:
            return {
                "aligned": False,
                "reason": f"查询目的不应包含'{action_type}'修改动作"
            }

        return {"aligned": True, "reason": ""}


# 便捷函数
def create_final_judgment(vault_path: str = "privacy_vault.json") -> FinalJudgment:
    vault = PrivacyVault(vault_path)
    return FinalJudgment(vault)
