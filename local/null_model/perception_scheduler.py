"""
Perception Scheduler - 感知调度器（修正版）

核心修正："提取前调度"，非"提取后过滤"
- 调度器在探针执行前决定提取策略
- 探针只接收调度指令，只执行允许提取
- 隐私数据从未被提取，不是提取后删除
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .privacy_vault import PrivacyVault, Rule, ExtractionPermission


@dataclass
class ScheduleResult:
    """感知调度结果"""
    enabled_probes: List[str]
    disabled_probes: List[str]
    enabled_models: List[str]
    disabled_models: List[str]
    extraction_permissions: List[ExtractionPermission]
    forbidden_entities: List[Dict[str, Any]]
    confidence_thresholds: Dict[str, float]
    derived_constraints: List[str]
    historical_feedback: Dict[str, Any]
    meta_calibrations: Dict[str, Any]


class PerceptionScheduler:
    """
    感知调度器（修正版）

    核心修正：
    1. 调度器在探针执行前生成指令
    2. 探针只执行指令中允许的操作
    3. 禁止的数据从未进入提取流程
    """

    def __init__(self, vault: PrivacyVault):
        self.vault = vault

    def schedule(self, purpose: str, target_entities: List[str], 
                 context: Optional[Dict[str, Any]] = None) -> ScheduleResult:
        """
        主调度函数 - 在探针执行前调用

        Args:
            purpose: 人类目的类型
            target_entities: 目标实体列表
            context: 额外上下文

        Returns:
            ScheduleResult: 探针执行指令
        """
        # 1. 查询匹配的元规则
        rules = self.vault.query_rules(purpose=purpose, entities=target_entities)

        if not rules:
            # 无匹配规则：默认拒绝所有敏感提取
            return ScheduleResult(
                enabled_probes=["system_probe"],  # 只启用最小系统探针
                disabled_probes=["audio_recorder", "face_recognition", "camera_full", "video_raw"],
                enabled_models=[],
                disabled_models=["facenet", "speaker_id", "ocr_full"],
                extraction_permissions=[],  # 无允许提取
                forbidden_entities=[{"entity": "*", "attributes": ["*"]}],  # 禁止所有
                confidence_thresholds={},
                derived_constraints=["¬Transmit(raw_data)", "¬Store(raw_data)", "¬Extract(sensitive)"],
                historical_feedback={"warning": "no_matching_rules, default_deny_all"},
                meta_calibrations={}
            )

        # 2. 合并规则生成调度指令
        schedule = self.vault.get_perception_schedule(rules)
        permissions = self.vault.get_extraction_permissions(rules)

        # 3. 收集所有约束
        all_constraints = []
        for rule in rules:
            all_constraints.extend(rule.derived_constraints)

        # 4. 获取历史反馈
        feedback = self.vault.get_historical_feedback(purpose=purpose)

        # 5. 获取元事实校准
        calibrations = self._get_meta_calibrations(context, rules)

        # 6. 合并提取权限（去重）
        extraction_perms = []
        for rule in rules:
            for p in rule.permitted:
                if not self._is_forbidden(p.entity, p.attributes, rules):
                    extraction_perms.append(p)

        # 去重
        seen = set()
        unique_perms = []
        for p in extraction_perms:
            key = (p.entity, tuple(sorted(p.attributes)))
            if key not in seen:
                seen.add(key)
                unique_perms.append(p)

        # 7. 收集所有禁止项
        all_forbidden = []
        for rule in rules:
            all_forbidden.extend(rule.forbidden_entities)

        return ScheduleResult(
            enabled_probes=schedule["enabled_probes"],
            disabled_probes=schedule["disabled_probes"],
            enabled_models=schedule["enabled_models"],
            disabled_models=schedule["disabled_models"],
            extraction_permissions=unique_perms,
            forbidden_entities=all_forbidden,
            confidence_thresholds=schedule["confidence_thresholds"],
            derived_constraints=list(set(all_constraints)),
            historical_feedback=feedback,
            meta_calibrations=calibrations
        )

    def _is_forbidden(self, entity: str, attributes: List[str], rules: List[Rule]) -> bool:
        """检查实体/属性是否被任何规则禁止"""
        for rule in rules:
            for f in rule.forbidden_entities:
                if f["entity"] == entity or f["entity"] == "*":
                    forbidden_attrs = f["attributes"]
                    if "*" in forbidden_attrs or any(a in forbidden_attrs for a in attributes):
                        return True
        return False

    def _get_meta_calibrations(self, context: Optional[Dict[str, Any]], rules: List[Rule]) -> Dict[str, Any]:
        """根据上下文获取元事实校准参数"""
        calibrations = {}

        if not context:
            return calibrations

        # 时间校准：夜间模式
        if context.get("time_of_day") in ["night", "evening"]:
            for mf in self.vault.meta_facts:
                if "night" in mf.fact.lower() or "frame_rate" in mf.fact.lower():
                    calibrations["night_mode"] = mf.calibration

        # 天气校准
        if context.get("weather") == "rain":
            calibrations["radar"] = {"confidence_adjustment": -0.1}

        # 历史反馈校准
        for rule in rules:
            fb = self.vault.get_historical_feedback(purpose=rule.trigger_purposes[0] if rule.trigger_purposes else "")
            if fb.get("false_positive_rate", 0) > 0.2:
                calibrations["threshold_adjustment"] = "increase"

        return calibrations

    def create_probe_command(self, schedule: ScheduleResult) -> Dict[str, Any]:
        """
        生成探针执行命令

        探针接收此命令，只执行命令中指定的提取操作
        禁止的数据永远不会被提取
        """
        return {
            "command_type": "perception_execute",
            "enabled_probes": schedule.enabled_probes,
            "disabled_probes": schedule.disabled_probes,
            "enabled_models": schedule.enabled_models,
            "disabled_models": schedule.disabled_models,
            "extraction_plan": [
                {
                    "entity": p.entity,
                    "attributes": p.attributes,
                    "confidence_threshold": p.confidence_threshold,
                    "granularity": p.granularity,
                    "anonymization": p.anonymization
                }
                for p in schedule.extraction_permissions
            ],
            "forbidden_list": schedule.forbidden_entities,
            "calibrations": schedule.meta_calibrations
        }


# 便捷函数
def create_scheduler(vault_path: str = "privacy_vault.json") -> PerceptionScheduler:
    vault = PrivacyVault(vault_path)
    return PerceptionScheduler(vault)
