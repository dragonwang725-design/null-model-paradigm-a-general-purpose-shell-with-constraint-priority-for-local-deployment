"""
Fact Extractor - 事实提取器

将probe.py采集的原始系统信息，转化为事实原子。
只提取观测值，不做判断。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

from .causal_skeleton import CausalSkeleton
from .purpose_parser import PurposeStructure


class FactType(Enum):
    METRIC = "metric"
    BOOLEAN = "boolean"
    STRING = "string"
    CATEGORICAL = "categorical"
    EVENT = "event"


@dataclass
class FactAtom:
    fact_id: str
    entity: str
    attribute: str
    value: Any
    fact_type: FactType
    source: str
    raw_text: str = ""


class FactExtractor:
    """事实原子化器"""

    FACT_TO_NODE = {
        ("memory", "usage_percent"): "memory_high_usage",
        ("memory", "state_high_usage"): "memory_high_usage",
        ("memory", "state_low_free"): "memory_low_free",
        ("memory", "free_gb"): "memory_low_free",
        ("cpu", "usage_percent"): "cpu_high_usage",
        ("cpu", "state_high_usage"): "cpu_high_usage",
        ("disk", "usage_percent"): "disk_high_usage",
        ("disk", "state_high_usage"): "disk_high_usage",
        ("ollama", "service_running"): "service_running",
        ("ollama", "version"): "service_available",
        ("ollama", "installed_models"): "model_loadable",
        ("network", "port_11434_listening"): "port_listening",
        ("system", "error_present"): "system_error_present",
        ("system", "error_type_tpm"): "tpm_error",
        ("process", "top_0_name"): "process_high_cpu",
        ("process", "top_1_name"): "process_high_cpu",
    }

    def extract(self, raw_data: Dict[str, Any], schedule) -> List[FactAtom]:
        atoms = []

        ollama = raw_data.get("ollama", {})
        if ollama:
            atoms.append(FactAtom("f_ollama_run", "ollama", "service_running", ollama.get("service_running", False), FactType.BOOLEAN, "ollama_cmd", f"Ollama服务: {ollama.get('service_running', False)}"))
            atoms.append(FactAtom("f_ollama_port", "network", "port_11434_listening", ollama.get("port_11434_listening", False), FactType.BOOLEAN, "socket_check", f"端口11434: {ollama.get('port_11434_listening', False)}"))
            if ollama.get("version"):
                atoms.append(FactAtom("f_ollama_ver", "ollama", "version", ollama.get("version"), FactType.STRING, "ollama_cmd", f"版本: {ollama.get('version')}"))
            models = ollama.get("installed_models", [])
            if models:
                atoms.append(FactAtom("f_ollama_models", "ollama", "installed_models", models, FactType.CATEGORICAL, "ollama_cmd", f"模型: {', '.join(models)}"))

        mem = raw_data.get("memory", {})
        if mem:
            total_gb = mem.get("total_gb", 0)
            used_pct = mem.get("used_percent", 0)
            free_gb = total_gb * (1 - used_pct/100) if total_gb else 0
            atoms.append(FactAtom("f_mem_total", "memory", "total_gb", round(total_gb, 2), FactType.METRIC, "psutil", f"内存总共: {total_gb}GB"))
            atoms.append(FactAtom("f_mem_used_pct", "memory", "usage_percent", round(used_pct, 1), FactType.METRIC, "psutil", f"内存已用: {used_pct}%"))
            atoms.append(FactAtom("f_mem_free_gb", "memory", "free_gb", round(free_gb, 2), FactType.METRIC, "psutil", f"空闲内存: ~{round(free_gb, 2)}GB"))
            if used_pct > 80:
                atoms.append(FactAtom("f_mem_high", "memory", "state_high_usage", True, FactType.BOOLEAN, "derived", f"内存高使用率: True"))
            if free_gb < 2.0:
                atoms.append(FactAtom("f_mem_low_free", "memory", "state_low_free", True, FactType.BOOLEAN, "derived", f"内存低空闲: True"))

        cpu = raw_data.get("cpu", {})
        if cpu:
            usage = cpu.get("usage_percent", 0)
            atoms.append(FactAtom("f_cpu_usage", "cpu", "usage_percent", round(usage, 1), FactType.METRIC, "psutil", f"CPU: {usage}%"))
            if usage > 80:
                atoms.append(FactAtom("f_cpu_high", "cpu", "state_high_usage", True, FactType.BOOLEAN, "derived", f"CPU高使用率: True"))

        disks = raw_data.get("disks", [])
        if disks:
            main = disks[0]
            atoms.append(FactAtom("f_disk_main_used", "disk", "usage_percent", main.get("used_percent", 0), FactType.METRIC, "psutil", f"磁盘使用率: {main.get('used_percent', 0)}%"))
            if main.get("used_percent", 0) > 85:
                atoms.append(FactAtom("f_disk_high", "disk", "state_high_usage", True, FactType.BOOLEAN, "derived", "磁盘高使用率: True"))

        errors = raw_data.get("recent_errors", [])
        if errors:
            atoms.append(FactAtom("f_sys_error", "system", "error_present", True, FactType.BOOLEAN, "event_log", f"系统错误: {errors[0][:100]}"))
            first_err = errors[0] if errors else ""
            if "tpm" in first_err.lower():
                atoms.append(FactAtom("f_tpm_error", "system", "error_type_tpm", True, FactType.BOOLEAN, "event_log", "TPM错误: True"))

        procs = raw_data.get("top_processes", [])
        if procs:
            for i, p in enumerate(procs[:3]):
                atoms.append(FactAtom(f"f_proc_{i}", "process", f"top_{i}_name", p.get("name", "unknown"), FactType.STRING, "psutil", f"进程: {p.get('name')} ({p.get('cpu_percent')}%)"))

        if raw_data.get("os"):
            atoms.append(FactAtom("f_os", "os", "platform", raw_data.get("os"), FactType.STRING, "platform", f"OS: {raw_data.get('os')}"))

        return atoms

    def rank_facts(self, atoms: List[FactAtom], purpose: PurposeStructure, 
                   start_nodes: List[str], skeleton: CausalSkeleton) -> List[Dict[str, Any]]:
        ranked = []
        for atom in atoms:
            fact_node = self.FACT_TO_NODE.get((atom.entity, atom.attribute))
            if not fact_node:
                ranked.append({"fact": atom, "relevance": 0.0, "distance": -1, "relation_type": "unmapped", "reasoning": f"未映射: {atom.entity}.{atom.attribute}"})
                continue

            distances = skeleton.bfs_distance(start_nodes, max_depth=3)
            if fact_node in distances:
                weight, depth, rel_type = distances[fact_node]
                decay = 0.7 ** depth
                score = weight * decay
                ranked.append({"fact": atom, "relevance": round(score, 3), "distance": depth, "relation_type": rel_type, "reasoning": f"目的->{fact_node}: {rel_type}, 深度{depth}, 权重{weight:.2f}"})
            elif fact_node in start_nodes:
                ranked.append({"fact": atom, "relevance": 1.0, "distance": 0, "relation_type": "direct_target", "reasoning": f"直接目标: {fact_node}"})
            else:
                ranked.append({"fact": atom, "relevance": 0.0, "distance": -1, "relation_type": "disconnected", "reasoning": f"无连接: {fact_node}"})

        ranked.sort(key=lambda x: (-x["relevance"], x["distance"]))
        return ranked

    def generate_judgments(self, ranked_facts: List[Dict], purpose: PurposeStructure, missing_entities: List[str]):
        from dataclasses import dataclass

        @dataclass
        class JudgmentUnit:
            unit_id: str
            unit_type: str
            premise_facts: List[str]
            conclusion: str
            confidence: float
            logic_trace: str
            purpose_relevance: float

        units = []
        relevant = [r for r in ranked_facts if r["relevance"] > 0.3]

        ollama_run = next((r for r in relevant if r["fact"].entity == "ollama" and r["fact"].attribute == "service_running"), None)
        port_listen = next((r for r in relevant if r["fact"].entity == "network" and r["fact"].attribute == "port_11434_listening"), None)
        if ollama_run and port_listen:
            run_val = ollama_run["fact"].value
            port_val = port_listen["fact"].value
            if run_val and port_val:
                units.append(JudgmentUnit("ju_ollama_avail", "causal", [ollama_run["fact"].fact_id, port_listen["fact"].fact_id], "ollama_service_available", 0.95, "service_running=True AND port_listening=True → available", 1.0))
            else:
                units.append(JudgmentUnit("ju_ollama_unavail", "causal", [ollama_run["fact"].fact_id, port_listen["fact"].fact_id], "ollama_service_unavailable", 0.95, "service_running or port_listening异常 → unavailable", 1.0))

        mem_used = next((r for r in relevant if r["fact"].entity == "memory" and r["fact"].attribute == "usage_percent"), None)
        mem_free = next((r for r in relevant if r["fact"].entity == "memory" and r["fact"].attribute == "free_gb"), None)
        if mem_used and mem_free:
            used_val = mem_used["fact"].value
            free_val = mem_free["fact"].value
            if used_val > 80 or free_val < 2.0:
                units.append(JudgmentUnit("ju_mem_pressure", "conditional", [mem_used["fact"].fact_id, mem_free["fact"].fact_id], "memory_pressure_present", 0.85, f"memory_used={used_val}% AND free={free_val}GB → pressure", 0.90))
            else:
                units.append(JudgmentUnit("ju_mem_normal", "descriptive", [mem_used["fact"].fact_id, mem_free["fact"].fact_id], "memory_state_normal", 0.90, f"memory_used={used_val}% AND free={free_val}GB → normal", 0.85))

        sys_err = next((r for r in relevant if r["fact"].entity == "system" and r["fact"].attribute == "error_present"), None)
        tpm_err = next((r for r in relevant if r["fact"].entity == "system" and r["fact"].attribute == "error_type_tpm"), None)
        if sys_err and sys_err["fact"].value:
            premise = [sys_err["fact"].fact_id]
            if tpm_err:
                premise.append(tpm_err["fact"].fact_id)
                units.append(JudgmentUnit("ju_sys_risk", "causal", premise, "tpm_error_present_stability_risk_low", 0.60, "TPM错误 → stability_risk (低)", 0.70))
            else:
                units.append(JudgmentUnit("ju_sys_risk", "causal", premise, "system_error_present_stability_risk", 0.75, "system_error → stability_risk", 0.70))

        for missing in missing_entities:
            units.append(JudgmentUnit(f"ju_gap_{missing}", "gap", [], f"missing_facts_for_{missing}", 1.0, f"目的关切实体'{missing}'无因果节点", 0.0))

        return units
