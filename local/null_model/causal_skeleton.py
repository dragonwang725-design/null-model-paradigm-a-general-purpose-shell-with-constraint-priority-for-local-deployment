"""
Causal Skeleton - 因果骨架（形式层 / Meta-Skeleton）

================================================================================
架构说明：元骨架（Meta-Skeleton）与领域实例（Domain Instances）的分离
================================================================================

本模块实现的是**元骨架（Meta-Skeleton）**——纯形式化的因果图结构，
只包含形式节点（Node_A, Node_B...）和形式边（A→B, 权重w, 关系类型），
不包含任何领域语义（不知道"内存"是什么，不知道"Ollama"是什么）。

领域实例（如 "memory" → Node_A, "ollama" → Node_C 的映射）存储在
**元事实库（Meta-Fact Vault / Knowledge Base 1）** 中，通过外部配置注入。

┌─────────────────────────────────────────────────────────────────────────────┐
│                         知识分层与职责分离                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  层级          │  内容                          │  位置              │ 修改权  │
│  ──────────────┼────────────────────────────────┼────────────────────┼────────│
│  元骨架         │  形式节点/边（Node_A→Node_B）   │  causal_skeleton.py │ 不可修改 │
│  （本模块）     │  纯数学结构，无实体语义           │  （架构常量）       │ （L0）  │
│  ──────────────┼────────────────────────────────┼────────────────────┼────────│
│  领域本体映射   │  实体→形式节点（memory→Node_A） │  元事实库           │ 人类维护 │
│  （外部注入）   │  按领域配置（系统监控/医疗/金融） │  （Knowledge Base 1）│        │
└─────────────────────────────────────────────────────────────────────────────┘

跨领域复用示例：
- 系统监控：memory.high_usage → Node_A, memory.pressure → Node_B
- 医疗诊断：blood_pressure.high → Node_A, blood_pressure.pressure → Node_B
- 金融风控：credit_score.low → Node_A, default_risk → Node_B

同一套元骨架（Node_A→Node_B），三套不同的领域映射表，零代码修改。

================================================================================
关于代码中的领域名称
================================================================================

当前代码中出现的领域名称（memory_high_usage, ollama, port_11434 等）
是**演示占位符（Demo Placeholders）**，用于 Phase 1 系统监控场景的原型验证。

实际部署时，这些名称应从元事实库的领域本体映射表中动态加载：

    # 伪代码：从元事实库加载映射
    mapping = meta_fact_vault.get_ontology_mapping(domain="system_monitor")
    # 返回: {"memory": {"high_usage": "Node_A", ...}, ...}

    # 运行时动态绑定
    node_id = mapping["memory"]["high_usage"]  # "Node_A"
    skeleton.validate(node_id)

TODO：后续版本将实现映射表动态加载，移除所有硬编码领域名称。

================================================================================
设计原则
================================================================================

- 不知道"Chrome是什么"，但知道"进程占用资源 → 资源耗尽"
- 不知道"Ollama是什么"，但知道"服务端口关闭 → 服务不可用"
- 不知道"内存是什么"，但知道"Node_A → Node_B（权重0.95）"

"""

from collections import defaultdict, deque
from typing import Dict, List, Tuple


class CausalSkeleton:
    """
    最小因果骨架——形式化的有向无环图（DAG）

    注意：本类只包含**形式结构**，领域语义通过外部映射表注入。
    当前硬编码的领域名称（如 memory_high_usage）是演示占位符，
    实际应从元事实库（Meta-Fact Vault）加载。
    """

    def __init__(self):
        self.graph = defaultdict(list)  # 邻接表：形式节点 → [(形式节点, 关系类型, 权重)]
        self.nodes = set()              # 所有形式节点的集合
        self._build_skeleton()

    def _add_edge(self, from_node: str, to_node: str, relation: str, weight: float = 1.0):
        """添加形式边——纯数学结构，无领域语义"""
        self.graph[from_node].append((to_node, relation, weight))
        self.nodes.add(from_node)
        self.nodes.add(to_node)

    def _build_skeleton(self):
        """
        构建形式因果骨架——纯结构，无领域实例

        ⚠️ 演示占位符警告：
        以下节点名称（memory_high_usage, ollama 等）是 Phase 1 原型中
        为方便理解而使用的**领域占位符**。实际部署时，这些名称应通过
        元事实库的领域本体映射表动态注入，而非硬编码在此处。

        形式骨架的正确理解方式：
        - "memory_high_usage" 应理解为 "Node_A"（形式节点A）
        - "memory_pressure" 应理解为 "Node_B"（形式节点B）
        - "memory_high_usage → memory_pressure" 应理解为 "Node_A --causal(0.95)--> Node_B"
        """
        # === 资源子系统（形式结构：Node_A → Node_B） ===
        # 占位符：Node_A=memory_high_usage, Node_B=memory_pressure
        self._add_edge("memory_high_usage", "memory_pressure", "causal", 0.95)
        # 占位符：Node_C=memory_low_free, Node_B=memory_pressure
        self._add_edge("memory_low_free", "memory_pressure", "causal", 0.90)
        # 占位符：Node_B=memory_pressure, Node_D=system_performance_degradation
        self._add_edge("memory_pressure", "system_performance_degradation", "causal", 0.85)
        # 占位符：Node_B=memory_pressure, Node_E=oom_risk
        self._add_edge("memory_pressure", "oom_risk", "causal", 0.80)

        # 占位符：Node_F=cpu_high_usage, Node_G=cpu_pressure
        self._add_edge("cpu_high_usage", "cpu_pressure", "causal", 0.95)
        # 占位符：Node_G=cpu_pressure, Node_D=system_performance_degradation
        self._add_edge("cpu_pressure", "system_performance_degradation", "causal", 0.90)

        # 占位符：Node_H=disk_high_usage, Node_I=disk_pressure
        self._add_edge("disk_high_usage", "disk_pressure", "causal", 0.85)
        # 占位符：Node_I=disk_pressure, Node_D=system_performance_degradation
        self._add_edge("disk_pressure", "system_performance_degradation", "causal", 0.70)
        # 占位符：Node_I=disk_pressure, Node_J=write_failure_risk
        self._add_edge("disk_pressure", "write_failure_risk", "causal", 0.75)

        # === Ollama 服务子系统（形式结构：Node_K → Node_L） ===
        # 占位符：Node_K=service_not_running, Node_L=service_unavailable
        self._add_edge("service_not_running", "service_unavailable", "causal", 0.98)
        # 占位符：Node_M=port_not_listening, Node_K=service_not_running
        self._add_edge("port_not_listening", "service_not_running", "causal", 0.95)
        # 占位符：Node_N=port_listening, Node_O=service_running
        self._add_edge("port_listening", "service_running", "causal", 0.90)
        # 占位符：Node_O=service_running, Node_P=service_available
        self._add_edge("service_running", "service_available", "causal", 0.95)
        # 占位符：Node_L=service_unavailable, Node_Q=model_unavailable
        self._add_edge("service_unavailable", "model_unavailable", "causal", 0.90)
        # 占位符：Node_R=model_missing, Node_Q=model_unavailable
        self._add_edge("model_missing", "model_unavailable", "causal", 0.95)
        # 占位符：Node_P=service_available, Node_S=model_loadable
        self._add_edge("service_available", "model_loadable", "conditional", 0.85)

        # === 错误与稳定性子系统（形式结构：Node_T → Node_U） ===
        # 占位符：Node_T=system_error_present, Node_U=system_stability_risk
        self._add_edge("system_error_present", "system_stability_risk", "causal", 0.75)
        # 占位符：Node_U=system_stability_risk, Node_D=system_performance_degradation
        self._add_edge("system_stability_risk", "system_performance_degradation", "causal", 0.60)
        # 占位符：Node_V=tpm_error, Node_U=system_stability_risk
        self._add_edge("tpm_error", "system_stability_risk", "causal", 0.50)

        # === 进程子系统（形式结构：Node_W → Node_F） ===
        # 占位符：Node_W=process_high_cpu, Node_F=cpu_high_usage
        self._add_edge("process_high_cpu", "cpu_high_usage", "causal", 0.95)
        # 占位符：Node_X=process_high_memory, Node_A=memory_high_usage
        self._add_edge("process_high_memory", "memory_high_usage", "causal", 0.90)

        # === 反向边（诊断推理：Node_D → Node_B） ===
        # 占位符：Node_D=system_performance_degradation, Node_B=memory_pressure
        self._add_edge("system_performance_degradation", "memory_pressure", "diagnostic", 0.85)
        # 占位符：Node_D=system_performance_degradation, Node_G=cpu_pressure
        self._add_edge("system_performance_degradation", "cpu_pressure", "diagnostic", 0.90)
        # 占位符：Node_D=system_performance_degradation, Node_I=disk_pressure
        self._add_edge("system_performance_degradation", "disk_pressure", "diagnostic", 0.70)

    def get_neighbors(self, node: str) -> List[Tuple[str, str, float]]:
        """获取形式节点的邻接边——纯结构查询，无领域语义"""
        return self.graph.get(node, [])

    def bfs_distance(self, start_nodes: List[str], max_depth: int = 3) -> Dict[str, Tuple[float, int, str]]:
        """
        从起始形式节点出发，计算到所有可达形式节点的距离。

        这是**纯数学计算**：BFS 遍历形式图，累积权重，不考虑任何领域语义。

        参数:
            start_nodes: 起始形式节点列表（如 ["Node_A", "Node_F"]）
            max_depth: 最大搜索深度

        返回:
            Dict[str, Tuple[float, int, str]]: 
                {形式节点: (累积权重, 跳数, 路径关系类型)}

        注意：start_nodes 中的名称是**形式节点ID**（如 "Node_A"），
        实际调用时应通过元事实库的领域映射表将领域实体（如 "memory"）
        转换为形式节点ID。
        """
        distances = {}
        queue = deque()

        for start in start_nodes:
            if start in self.nodes:
                queue.append((start, 1.0, 0, "direct"))
                distances[start] = (1.0, 0, "direct")

        while queue:
            current, acc_weight, depth, relation = queue.popleft()
            if depth >= max_depth:
                continue

            for neighbor, rel_type, weight in self.graph.get(current, []):
                new_weight = acc_weight * weight
                new_depth = depth + 1

                if neighbor not in distances or distances[neighbor][0] < new_weight:
                    distances[neighbor] = (new_weight, new_depth, rel_type)
                    queue.append((neighbor, new_weight, new_depth, rel_type))

        return distances


# TODO: 后续版本增加从元事实库动态加载领域映射的功能
# def load_domain_mapping(vault: MetaFactVault, domain: str) -> Dict[str, Dict[str, str]]:
#     """
#     从元事实库加载领域本体映射表
#     
#     示例返回:
#     {
#       "memory": {"high_usage": "Node_A", "pressure": "Node_B"},
#       "cpu": {"high_usage": "Node_F", "pressure": "Node_G"}
#     }
#     """
#     return vault.get_ontology_mapping(domain)
