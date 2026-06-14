"""
Empty Model Main Controller (Fixed)

修正内容：
1. 整合物理预算模块（在LLM调用前计算资源）
2. 整合原子执行模块（保证事务性）
3. 提取前调度（探针只执行允许提取）
4. 六步流水线完整映射
"""

import json
from typing import Dict, Any, List
from dataclasses import asdict

from .purpose_parser import PurposeParser, PurposeStructure
from .causal_skeleton import CausalSkeleton
from .fact_extractor import FactExtractor, FactAtom
from .perception_scheduler import PerceptionScheduler, ScheduleResult
from .privacy_vault import PrivacyVault
from .desensitizer import Desensitizer
from .final_judgment import FinalJudgment, JudgmentResult
from .physical_budget import PhysicalBudget
from .atomic_executor import AtomicExecutor


class EmptyModel:
    """
    空模型主控器（修正版）

    完整六步流水线：
    1. Problem → 人类输入目的
    2. Null Model (Strategy) → 物理预算 + 感知调度 + 约束锁定
    3. Full Model (Cognition) → LLM语义理解
    4. Database (Knowledge) → 隐私资料库查询
    5. Full Model (Synthesis) → LLM组装策略
    6. Null Model (Judgment & Execution) → 评估 + 选择 + 原子执行 + 回滚
    """

    def __init__(self, vault_path: str = "privacy_vault.json"):
        self.vault = PrivacyVault(vault_path)
        self.parser = PurposeParser()
        self.skeleton = CausalSkeleton()
        self.extractor = FactExtractor()
        self.scheduler = PerceptionScheduler(self.vault)
        self.desensitizer = Desensitizer()
        self.judgment = FinalJudgment(self.vault)
        self.budget = PhysicalBudget()
        self.executor = AtomicExecutor()

    def process(self, question: str, raw_data: Dict[str, Any], 
                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        主处理流程（不含LLM交互）

        修正：
        - 物理预算在LLM调用前计算
        - 感知调度在探针执行前完成
        """
        # Step 1: 目的形式化
        purpose = self.parser.parse(question)

        # Step 2a: 物理预算（在LLM调用前）
        total_items = raw_data.get("total_items", 1)
        budget = self.budget.compute_budget(total_items=total_items)
        safety_check = self.budget.check_llm_safety(budget)

        if not safety_check["safe"]:
            # 资源不足，直接返回降级方案，不调用LLM
            return {
                "purpose": asdict(purpose),
                "budget": asdict(budget),
                "safety_check": safety_check,
                "llm_input": None,
                "fallback": "资源不足，使用本地确定性策略",
                "output": [{"action_type": "alert", "target": "user", "parameters": {"message": safety_check["warning"]}}]
            }

        # Step 2b: 感知调度（在探针执行前）
        schedule = self.scheduler.schedule(
            purpose=purpose.concern_type,
            target_entities=purpose.target_entities,
            context=context
        )

        # Step 2c: 探针执行（只执行允许提取）
        # 注意：实际中，探针接收schedule指令，只提取允许的事实
        # 这里假设raw_data已经只包含允许的事实
        probe_command = self.scheduler.create_probe_command(schedule)

        # Step 3: 事实提取（基于调度指令）
        atoms = self.extractor.extract(raw_data, schedule)

        # Step 4: 因果骨架验证 + 相关性排序
        start_nodes, missing = self.parser.get_causal_start_nodes(purpose)
        ranked = self.extractor.rank_facts(atoms, purpose, start_nodes, self.skeleton)

        # Step 5: 生成判断单元
        judgments = self.extractor.generate_judgments(ranked, purpose, missing)

        # Step 6: 脱敏处理
        desensitized_facts = self.desensitizer.process(ranked, schedule)

        # Step 7: 构造给LLM的输入
        llm_input = {
            "human_purpose": question,
            "purpose_structure": asdict(purpose),
            "budget": {
                "safe_batch_size": budget.safe_batch_size,
                "total_batches": budget.total_batches_needed,
                "safety_margin": budget.safety_margin
            },
            "relevant_facts": desensitized_facts,
            "judgment_units": [
                {
                    "unit_id": j.unit_id,
                    "unit_type": j.unit_type,
                    "premise_facts": j.premise_facts,
                    "conclusion": j.conclusion,
                    "confidence": j.confidence,
                    "logic_trace": j.logic_trace,
                    "purpose_relevance": j.purpose_relevance
                }
                for j in judgments
            ],
            "uncertainty": [
                f"实体'{m}'的事实缺失，无法评估其与目的的关系" 
                for m in missing
            ] + [
                f"判断单元'{j.unit_id}'置信度低于0.7，建议人工复核"
                for j in judgments if j.confidence < 0.7 and j.unit_type != "gap"
            ],
            "instruction": "基于以上事实与判断单元，给出策略建议。禁止引入外部知识。"
        }

        return {
            "purpose": asdict(purpose),
            "budget": asdict(budget),
            "safety_check": safety_check,
            "probe_command": probe_command,
            "schedule": {
                "enabled_probes": schedule.enabled_probes,
                "disabled_probes": schedule.disabled_probes,
                "extraction_permissions": [
                    {"entity": p.entity, "attributes": p.attributes} 
                    for p in schedule.extraction_permissions
                ],
                "forbidden_entities": schedule.forbidden_entities,
                "derived_constraints": schedule.derived_constraints
            },
            "total_facts": len(atoms),
            "relevant_facts": [
                {
                    "fact_id": r["fact"].fact_id,
                    "entity": r["fact"].entity,
                    "attribute": r["fact"].attribute,
                    "value": r["fact"].value,
                    "relevance": r["relevance"],
                    "distance": r["distance"],
                    "relation_type": r["relation_type"],
                    "reasoning": r["reasoning"]
                }
                for r in ranked if r["relevance"] > 0.1
            ],
            "filtered_facts": desensitized_facts,
            "judgment_units": [
                {
                    "unit_id": j.unit_id,
                    "unit_type": j.unit_type,
                    "premise_facts": j.premise_facts,
                    "conclusion": j.conclusion,
                    "confidence": j.confidence,
                    "logic_trace": j.logic_trace,
                    "purpose_relevance": j.purpose_relevance
                }
                for j in judgments
            ],
            "llm_input": llm_input,
            "uncertainty_boundary": llm_input["uncertainty"]
        }

    def execute_with_llm(self, question: str, raw_data: Dict[str, Any],
                        llm_client, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        完整流程：包含LLM交互 + 原子执行

        六步流水线完整实现：
        1. Problem
        2. Null Model (Strategy) → 物理预算 + 感知调度 + 约束锁定
        3. Full Model (Cognition) → LLM语义理解
        4. Database (Knowledge) → 隐私资料库
        5. Full Model (Synthesis) → LLM组装策略
        6. Null Model (Judgment & Execution) → 评估 + 原子执行 + 回滚
        """
        # Step 1-2: 获取中间结果（含物理预算和感知调度）
        intermediate = self.process(question, raw_data, context)

        # 如果资源不足，直接返回降级方案
        if intermediate.get("safety_check", {}).get("safe") is False:
            return {
                **intermediate,
                "llm_strategy": None,
                "final_judgment": None,
                "execution_report": None,
                "output": intermediate.get("output", [])
            }

        # Step 3-5: 调用LLM（认知 + 合成）
        llm_response = llm_client.query(
            purpose=question,
            filtered_facts=intermediate["filtered_facts"],
            judgment_units=intermediate["judgment_units"],
            uncertainty=intermediate["uncertainty_boundary"]
        )

        # Step 6a: 最终判断
        final = self.judgment.judge(
            strategy={
                "strategy_id": llm_response.strategy_id,
                "actions": llm_response.actions,
                "confidence": llm_response.confidence,
                "reasoning": llm_response.reasoning,
                "fallback": llm_response.fallback
            },
            judgment_units=intermediate["judgment_units"],
            filtered_facts=intermediate["filtered_facts"],
            purpose=question
        )

        # Step 6b: 原子执行
        execution_report = None
        if final.approved and final.actions:
            # 创建操作批次
            operations = [
                {
                    "action_type": a["action_type"],
                    "source": a.get("source", ""),
                    "target": a.get("target"),
                    "parameters": a.get("parameters", {})
                }
                for a in final.actions
            ]

            batch = self.executor.create_batch(operations)

            # 锁定预算
            budget_locked = self.budget.lock_budget(
                self.budget.compute_budget(total_items=len(operations))
            )

            if budget_locked:
                # 原子执行
                success = self.executor.execute_batch(batch)
                execution_report = self.executor.get_execution_report(batch)

                if not success:
                    # 执行失败，回滚已完成操作
                    final.approved = False
                    final.rejection_reasons.append("原子执行失败，已回滚")
            else:
                final.approved = False
                final.rejection_reasons.append("资源锁定失败，无法执行")

        return {
            **intermediate,
            "llm_strategy": {
                "strategy_id": llm_response.strategy_id,
                "actions": llm_response.actions,
                "confidence": llm_response.confidence,
                "reasoning": llm_response.reasoning
            },
            "final_judgment": {
                "approved": final.approved,
                "actions": final.actions,
                "rejection_reasons": final.rejection_reasons,
                "confidence": final.confidence,
                "logic_trace": final.logic_trace
            },
            "execution_report": execution_report,
            "output": final.actions if final.approved else []
        }
