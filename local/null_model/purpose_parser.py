"""
Purpose Parser - 目的形式化解析器

将人类自然语言目的解析为形式结构。
不使用LLM，使用受控规则 + 关键词映射。
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class PurposeStructure:
    """目的的形式化结构——无价值负载，只有结构"""
    concern_type: str
    target_entities: List[str]
    evaluation_dimensions: List[str]
    temporal_scope: str = "current"
    raw_question: str = ""


class PurposeParser:
    """
    目的形式化解析器
    """

    CONCERN_PATTERNS = {
        "diagnosis": ["为什么", "怎么", "问题", "故障", "异常", "卡", "慢", "崩溃", "日志"],
        "query": ["多少", "什么", "状态", "信息", "配置", "版本"],
        "optimize": ["优化", "提升", "加速", "清理", "释放"],
        "predict": ["会不会", "可能", "风险", "将要"],
        "trend_analysis": ["趋势", "变化", "走势", "越来越"],
        "anomaly_detection": ["异常", "突然", "骤变", "报警"],
        "forecast": ["预测", "将要", "未来", "明天", "下周"],
        "comparative": ["比", "对比", "昨天", "上次", "之前"]
    }

    ENTITY_MAP = {
        "内存": "memory", "memory": "memory", "ram": "memory", "显存": "memory",
        "cpu": "cpu", "处理器": "cpu", "中央处理器": "cpu",
        "磁盘": "disk", "硬盘": "disk", "disk": "disk", "c盘": "disk", "d盘": "disk",
        "存储": "disk",
        "ollama": "ollama", "模型": "ollama", "大模型": "ollama", "llm": "ollama",
        "端口": "network", "网络": "network", "服务": "network",
        "系统": "system", "日志": "system", "运行日志": "system", "事件": "system",
        "错误": "system",
        "显卡": "gpu", "gpu": "gpu", "图形处理器": "gpu", "显示": "gpu",
        "进程": "process", "程序": "process", "应用": "process", "软件": "process"
    }

    ENTITY_TO_NODES = {
        "memory": ["memory_high_usage", "memory_low_free", "memory_pressure"],
        "cpu": ["cpu_high_usage", "cpu_pressure"],
        "disk": ["disk_high_usage", "disk_pressure"],
        "ollama": ["service_running", "service_unavailable", "model_unavailable", "model_loadable"],
        "network": ["port_listening", "port_not_listening"],
        "system": ["system_error_present", "system_stability_risk", "system_performance_degradation"],
        "process": ["process_high_cpu", "process_high_memory"],
        "gpu": ["gpu_high_usage", "gpu_pressure"]
    }

    def parse(self, question: str) -> PurposeStructure:
        q_lower = question.lower()

        concern_type = "query"
        for ctype, patterns in self.CONCERN_PATTERNS.items():
            if any(p in q_lower for p in patterns):
                concern_type = ctype
                break

        target_entities = []
        for keyword, entity in self.ENTITY_MAP.items():
            if keyword in q_lower:
                if entity not in target_entities:
                    target_entities.append(entity)

        evaluation_dimensions = []
        if concern_type == "diagnosis":
            evaluation_dimensions = ["stability", "performance", "availability"]
        elif concern_type == "query":
            evaluation_dimensions = ["state", "configuration"]
        elif concern_type == "optimize":
            evaluation_dimensions = ["performance", "resource_efficiency"]

        if "ollama" in target_entities and "availability" not in evaluation_dimensions:
            evaluation_dimensions.append("availability")

        return PurposeStructure(
            concern_type=concern_type,
            target_entities=target_entities,
            evaluation_dimensions=evaluation_dimensions,
            temporal_scope="current",
            raw_question=question
        )

    def get_causal_start_nodes(self, purpose: PurposeStructure) -> Tuple[List[str], List[str]]:
        from .causal_skeleton import CausalSkeleton

        start_nodes = []
        missing_entities = []

        for entity in purpose.target_entities:
            nodes = self.ENTITY_TO_NODES.get(entity, [])
            valid_nodes = [n for n in nodes if n in CausalSkeleton().nodes]
            if valid_nodes:
                start_nodes.extend(valid_nodes)
            else:
                missing_entities.append(entity)

        return start_nodes, missing_entities
