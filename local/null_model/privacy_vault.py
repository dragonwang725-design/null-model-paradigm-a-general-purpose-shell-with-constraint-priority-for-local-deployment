"""
Privacy Vault - 人类元规则层
空模型在提取任何事实之前必须查询的先验约束源
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class ExtractionPermission:
    entity: str
    attributes: List[str]
    confidence_threshold: float = 0.7
    retention: str = "7_days"
    granularity: Optional[str] = None  # 时间粒度：hour, day
    anonymization: Optional[str] = None  # 匿名化策略


@dataclass
class Rule:
    rule_id: str
    name: str
    trigger_purposes: List[str]
    trigger_entities: List[str]
    priority: int = 100
    permitted: List[ExtractionPermission] = field(default_factory=list)
    forbidden_entities: List[Dict[str, Any]] = field(default_factory=list)
    enabled_probes: List[str] = field(default_factory=list)
    disabled_probes: List[str] = field(default_factory=list)
    enabled_models: List[str] = field(default_factory=list)
    disabled_models: List[str] = field(default_factory=list)
    alert_conditions: List[Dict[str, Any]] = field(default_factory=list)
    derived_constraints: List[str] = field(default_factory=list)


@dataclass
class Knowledge:
    knowledge_id: str
    domain: str
    entity: str
    fact: str
    source: str = "human_confirmed"
    confidence: float = 1.0
    applies_to: List[str] = field(default_factory=list)


@dataclass
class Log:
    log_id: str
    timestamp: str
    purpose: str
    extracted_facts: List[str]
    outcome: str
    feedback: str = ""
    adjustment: Optional[Dict[str, Any]] = None


@dataclass
class MetaFact:
    meta_fact_id: str
    entity: str
    attribute: str
    fact: str
    calibration: Optional[Dict[str, Any]] = None


class PrivacyVault:
    """
    元事实库：人类元规则层

    核心原则：
    1. 规则是硬约束，空模型必须遵守
    2. 知识是人类确认的先验事实
    3. 日志是历史反馈，用于优化
    4. 元事实用于校准感知器
    """

    def __init__(self, vault_path: str = "privacy_vault.json"):
        self.vault_path = Path(vault_path)
        self.rules: List[Rule] = []
        self.knowledge: List[Knowledge] = []
        self.logs: List[Log] = []
        self.meta_facts: List[MetaFact] = []
        self._load()

    def _load(self):
        """从JSON文件加载元事实资料库"""
        if not self.vault_path.exists():
            self._init_default()
            return

        with open(self.vault_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for r in data.get("rules", []):
            self.rules.append(Rule(
                rule_id=r["rule_id"],
                name=r["name"],
                trigger_purposes=r["trigger"]["purposes"],
                trigger_entities=r["trigger"].get("entities", []),
                priority=r["trigger"].get("priority", 100),
                permitted=[ExtractionPermission(**p) for p in r["permitted"]["extractions"]],
                forbidden_entities=r["forbidden"]["extractions"],
                enabled_probes=r["permitted"].get("probes", []),
                disabled_probes=r["forbidden"].get("probes", []),
                enabled_models=r["permitted"].get("models", []),
                disabled_models=r["forbidden"].get("models", []),
                alert_conditions=r.get("alert_conditions", []),
                derived_constraints=r.get("derived_constraints", [])
            ))

        for k in data.get("knowledge", []):
            self.knowledge.append(Knowledge(**k))

        for l in data.get("logs", []):
            self.logs.append(Log(**l))

        for m in data.get("meta_facts", []):
            self.meta_facts.append(MetaFact(**m))

    def _init_default(self):
        """初始化默认规则（系统监控场景）"""
        self.rules = [
            Rule(
                rule_id="SYS001",
                name="系统性能诊断规则",
                trigger_purposes=["diagnosis", "query", "optimize"],
                trigger_entities=["cpu", "memory", "disk", "ollama"],
                priority=100,
                permitted=[
                    ExtractionPermission(entity="cpu", attributes=["usage_percent", "cores"]),
                    ExtractionPermission(entity="memory", attributes=["total_gb", "used_percent", "free_gb"]),
                    ExtractionPermission(entity="disk", attributes=["usage_percent", "free_gb"]),
                    ExtractionPermission(entity="ollama", attributes=["service_running", "version", "installed_models"]),
                    ExtractionPermission(entity="network", attributes=["port_listening"]),
                    ExtractionPermission(entity="process", attributes=["name", "cpu_percent", "memory_percent"]),
                    ExtractionPermission(entity="system", attributes=["error_present", "error_type"]),
                    ExtractionPermission(entity="os", attributes=["platform"])
                ],
                forbidden_entities=[
                    {"entity": "network", "attributes": ["ip_address", "mac_address"]},
                    {"entity": "system", "attributes": ["hostname", "username"]}
                ],
                enabled_probes=["system_probe", "ollama_probe"],
                disabled_probes=[],
                derived_constraints=["¬Transmit(hostname)", "¬Transmit(username)", "¬Transmit(ip_address)"]
            ),
            Rule(
                rule_id="SYS002",
                name="安全监控隐私规则",
                trigger_purposes=["anomaly_detection", "intrusion_alert"],
                trigger_entities=["human_shape", "motion"],
                priority=200,
                permitted=[
                    ExtractionPermission(entity="human_shape", attributes=["presence", "count", "motion_direction"], confidence_threshold=0.7),
                    ExtractionPermission(entity="time", attributes=["timestamp"], granularity="hour"),
                    ExtractionPermission(entity="location", attributes=["zone_id"], anonymization="zone_alias")
                ],
                forbidden_entities=[
                    {"entity": "face", "attributes": ["facial_features", "identity", "emotion"]},
                    {"entity": "audio", "attributes": ["voice_print", "conversation_content"]},
                    {"entity": "video", "attributes": ["raw_frame", "full_resolution"]}
                ],
                enabled_probes=["video_human_detection", "radar_motion"],
                disabled_probes=["audio_recorder", "face_recognition"],
                enabled_models=["yolov8n-person"],
                disabled_models=["facenet", "speaker_id"],
                derived_constraints=["¬Upload(raw_video_frame)", "¬Store(face_embedding)", "¬Transmit(audio_waveform)"]
            )
        ]
        self._save()

    def _save(self):
        """保存到JSON文件"""
        data = {
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "trigger": {"purposes": r.trigger_purposes, "entities": r.trigger_entities, "priority": r.priority},
                    "permitted": {
                        "extractions": [{"entity": p.entity, "attributes": p.attributes, "confidence_threshold": p.confidence_threshold, "retention": p.retention, "granularity": p.granularity, "anonymization": p.anonymization} for p in r.permitted],
                        "probes": r.enabled_probes,
                        "models": r.enabled_models
                    },
                    "forbidden": {
                        "extractions": r.forbidden_entities,
                        "probes": r.disabled_probes,
                        "models": r.disabled_models
                    },
                    "alert_conditions": r.alert_conditions,
                    "derived_constraints": r.derived_constraints
                }
                for r in self.rules
            ],
            "knowledge": [{"knowledge_id": k.knowledge_id, "domain": k.domain, "entity": k.entity, "fact": k.fact, "source": k.source, "confidence": k.confidence, "applies_to": k.applies_to} for k in self.knowledge],
            "logs": [{"log_id": l.log_id, "timestamp": l.timestamp, "purpose": l.purpose, "extracted_facts": l.extracted_facts, "outcome": l.outcome, "feedback": l.feedback, "adjustment": l.adjustment} for l in self.logs],
            "meta_facts": [{"meta_fact_id": m.meta_fact_id, "entity": m.entity, "attribute": m.attribute, "fact": m.fact, "calibration": m.calibration} for m in self.meta_facts]
        }
        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def query_rules(self, purpose: str, entities: List[str]) -> List[Rule]:
        """
        根据目的和实体查询匹配的规则

        匹配逻辑：
        1. 目的匹配：purpose在rule.trigger_purposes中
        2. 实体匹配：任意entity在rule.trigger_entities中
        3. 按优先级降序排序
        """
        matched = []
        for rule in self.rules:
            purpose_match = purpose in rule.trigger_purposes
            entity_match = any(e in rule.trigger_entities for e in entities)
            if purpose_match or entity_match:
                matched.append(rule)

        matched.sort(key=lambda r: r.priority, reverse=True)
        return matched

    def get_perception_schedule(self, rules: List[Rule]) -> Dict[str, Any]:
        """
        获取感知调度指令

        合并多个规则的感知指令：
        - enabled_probes：取并集
        - disabled_probes：取并集（如果同时在enabled和disabled中，disabled优先）
        - enabled_models：取并集
        - disabled_models：取并集
        """
        enabled_probes = set()
        disabled_probes = set()
        enabled_models = set()
        disabled_models = set()
        confidence_thresholds = {}

        for rule in rules:
            enabled_probes.update(rule.enabled_probes)
            disabled_probes.update(rule.disabled_probes)
            enabled_models.update(rule.enabled_models)
            disabled_models.update(rule.disabled_models)
            for p in rule.permitted:
                if p.entity not in confidence_thresholds or p.confidence_threshold < confidence_thresholds[p.entity]:
                    confidence_thresholds[p.entity] = p.confidence_threshold

        # disabled优先
        final_probes = list(enabled_probes - disabled_probes)
        final_models = list(enabled_models - disabled_models)

        return {
            "enabled_probes": final_probes,
            "disabled_probes": list(disabled_probes),
            "enabled_models": final_models,
            "disabled_models": list(disabled_models),
            "confidence_thresholds": confidence_thresholds
        }

    def get_extraction_permissions(self, rules: List[Rule]) -> Dict[str, Any]:
        """
        获取提取权限

        合并多个规则的权限：
        - allowed：取并集
        - forbidden：取并集（如果同时在allowed和forbidden中，forbidden优先）
        """
        allowed = []
        forbidden = []

        for rule in rules:
            for p in rule.permitted:
                allowed.append({"entity": p.entity, "attributes": p.attributes})
            forbidden.extend(rule.forbidden_entities)

        # 去重
        allowed_unique = []
        seen = set()
        for a in allowed:
            key = (a["entity"], tuple(sorted(a["attributes"])))
            if key not in seen:
                seen.add(key)
                allowed_unique.append(a)

        return {
            "allowed": allowed_unique,
            "forbidden": forbidden
        }

    def get_historical_feedback(self, purpose: str, entity: Optional[str] = None) -> Dict[str, Any]:
        """获取历史反馈"""
        relevant_logs = [l for l in self.logs if l.purpose == purpose]
        if entity:
            relevant_logs = [l for l in relevant_logs if any(entity in f for f in l.extracted_facts)]

        if not relevant_logs:
            return {"count": 0, "suggestion": "no_history"}

        fp_rate = sum(1 for l in relevant_logs if l.outcome == "false_positive") / len(relevant_logs)

        # 提取建议调整
        adjustments = [l.adjustment for l in relevant_logs if l.adjustment]

        return {
            "count": len(relevant_logs),
            "false_positive_rate": round(fp_rate, 2),
            "adjustments": adjustments,
            "suggestion": "review_threshold" if fp_rate > 0.2 else "maintain"
        }

    def check_constraint(self, constraint: str) -> bool:
        """
        检查派生约束

        例如：¬Delete(source_file) → 返回True（禁止删除）
        """
        all_constraints = []
        for rule in self.rules:
            all_constraints.extend(rule.derived_constraints)

        return constraint in all_constraints

    def add_log(self, log: Log):
        """添加日志记录"""
        self.logs.append(log)
        self._save()

    def add_knowledge(self, knowledge: Knowledge):
        """添加知识（需人类确认）"""
        self.knowledge.append(knowledge)
        self._save()

    def add_meta_fact(self, meta_fact: MetaFact):
        """添加元事实"""
        self.meta_facts.append(meta_fact)
        self._save()


# 便捷函数
def load_vault(path: str = "privacy_vault.json") -> PrivacyVault:
    return PrivacyVault(path)
