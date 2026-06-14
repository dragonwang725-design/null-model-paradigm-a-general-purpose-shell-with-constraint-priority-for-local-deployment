#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMP Phase 1 完整演示

基于用户提供的真实 probe.py 输出，运行完整的空模型流程。
"""

import sys
sys.path.insert(0, "../local")

from null_model import EmptyModel
from cloud.llm_client import LLMClient


def main():
    # 用户提供的真实 probe.py 输出
    probe_output = {
        "timestamp": "2026-06-09T09:38:37",
        "os": "Windows-10-10.0.19045-SP0",
        "cpu": {
            "physical_cores": 4,
            "logical_cores": 8,
            "usage_percent": 3.9
        },
        "memory": {
            "total_gb": 8.49,
            "available_gb": 5.21,
            "used_percent": 63.8,
            "swap_total_gb": 2.0
        },
        "disks": [
            {
                "device": "C:",
                "mountpoint": "C:",
                "total_gb": 100.0,
                "free_gb": 28.2,
                "used_percent": 71.8
            }
        ],
        "top_processes": [
            {"pid": 0, "name": "System Idle Process", "cpu_percent": 96.1, "memory_percent": 0.0},
            {"pid": 4, "name": "System", "cpu_percent": 0.5, "memory_percent": 0.1},
            {"pid": 380, "name": "smss.exe", "cpu_percent": 0.0, "memory_percent": 0.1},
            {"pid": 512, "name": "fontdrvhost.exe", "cpu_percent": 0.0, "memory_percent": 0.2}
        ],
        "recent_errors": [
            "Event[0] Source: Microsoft-Windows-TPM-WMI TPM（通用加密模块）相关事件"
        ],
        "ollama": {
            "service_running": True,
            "port_11434_listening": True,
            "installed_models": ["qwen2.5:3b", "qwen2.5:1.5b", "qwen2.5:0.5b"],
            "version": "0.24.0"
        }
    }

    # 用户原始问题
    question = "运行日志 显卡，内存ollama"

    print("=" * 70)
    print("【NMP Phase 1 完整演示】")
    print("=" * 70)
    print(f"
用户目的: {question}")
    print(f"数据来源: probe.py 系统探针")
    print(f"数据时间: {probe_output['timestamp']}")

    # 初始化空模型
    print("
[1/6] 初始化空模型...")
    model = EmptyModel()

    # 执行处理（不含LLM）
    print("[2/6] 执行空模型流程...")
    result = model.process(question, probe_output)

    # 输出结果
    print("
" + "=" * 70)
    print("【空模型输出报告】")
    print("=" * 70)

    print("
【1. 目的形式化解析】")
    p = result["purpose"]
    print(f"  目的类型: {p['concern_type']}")
    print(f"  目标实体: {p['target_entities']}")
    print(f"  评估维度: {p['evaluation_dimensions']}")
    print(f"  时间范围: {p['temporal_scope']}")

    print("
【2. 隐私资料库调度指令】")
    s = result["schedule"]
    print(f"  启用探针: {s['enabled_probes']}")
    print(f"  禁用探针: {s['disabled_probes']}")
    print(f"  提取权限: {len(s['extraction_permissions'])} 项")
    for perm in s['extraction_permissions']:
        print(f"    • {perm['entity']}: {perm['attributes']}")
    print(f"  禁止提取: {len(s['forbidden_entities'])} 项")
    for forb in s['forbidden_entities']:
        print(f"    • {forb['entity']}: {forb['attributes']}")
    print(f"  派生约束: {s['derived_constraints']}")

    print("
【3. 事实相关性排序（Top 10）】")
    for i, f in enumerate(result["relevant_facts"][:10], 1):
        bar = "█" * int(f["relevance"] * 20) + "░" * (20 - int(f["relevance"] * 20))
        print(f"  {i}. [{f['fact_id']}] {f['entity']}.{f['attribute']} = {f['value']}")
        print(f"     相关度: {f['relevance']:.2f} {bar} | 距离: {f['distance']} | 类型: {f['relation_type']}")
        print(f"     推理: {f['reasoning']}")

    print("
【4. 脱敏后的高相关事实（输入LLM的原料）】")
    for f in result["filtered_facts"]:
        print(f"  • [{f['fact_id']}] {f['entity']}.{f['attribute']} = {f['value']}")

    print("
【5. 判断单元（空模型的核心输出）】")
    for j in result["judgment_units"]:
        icon = {"causal": "🔗", "conditional": "❓", "descriptive": "📋", "gap": "⚠️"}.get(j["unit_type"], "•")
        print(f"  {icon} [{j['unit_id']}] 类型: {j['unit_type']}")
        print(f"     结论: {j['conclusion']}")
        print(f"     置信度: {j['confidence']:.2f} | 目的相关: {j['purpose_relevance']:.2f}")
        print(f"     逻辑: {j['logic_trace']}")

    print("
【6. 不确定性边界】")
    for u in result["uncertainty_boundary"]:
        print(f"  ? {u}")

    # 可选：调用LLM
    print("
" + "=" * 70)
    print("【LLM交互（可选）】")
    print("=" * 70)

    llm_client = LLMClient()
    full_result = model.execute_with_llm(question, probe_output, llm_client)

    print(f"
LLM策略ID: {full_result['llm_strategy']['strategy_id']}")
    print(f"LLM置信度: {full_result['llm_strategy']['confidence']}")
    print(f"LLM推理: {full_result['llm_strategy']['reasoning']}")

    print(f"
【最终判断】")
    fj = full_result["final_judgment"]
    print(f"  批准: {fj['approved']}")
    print(f"  置信度: {fj['confidence']}")
    print(f"  逻辑轨迹: {fj['logic_trace']}")
    if fj['rejection_reasons']:
        print(f"  拒绝原因: {fj['rejection_reasons']}")

    print(f"
【输出动作】")
    if full_result['output']:
        for action in full_result['output']:
            print(f"  ✓ {action['action_type']}: {action['target']}")
    else:
        print("  ✗ 无批准动作")

    print("
" + "=" * 70)
    print("【与LLM的接口JSON（用于调试）】")
    print("=" * 70)
    import json
    print(json.dumps(result["llm_input"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
