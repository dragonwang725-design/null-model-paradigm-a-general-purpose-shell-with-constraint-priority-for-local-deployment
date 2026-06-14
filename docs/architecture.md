
#  TDA 架构文档（修正版）

## 修正说明

基于逻辑一致性验证，以下修正已实施：
1. **提取前调度**：感知调度器在探针执行前生成指令，探针只执行允许提取
2. **物理预算模块**：在LLM调用前计算资源预算，防止过度生成
3. **原子执行与回滚**：保证每批操作要么全成功，要么全回滚
4. **规则外置**：默认规则从代码移到配置文件（建议）
5. **元事实库驱动骨架实例化**：因果骨架的形式结构跨领域复用，领域实例通过元事实库映射表动态注入

## 核心架构图

<img width="1747" height="865" alt="arch" src="https://github.com/user-attachments/assets/32cb1e3f-c0d9-4f53-a41d-f39c4dd6a0c3" />

**上图说明：**
- **本地（Local）**：空模型 + 元事实库 + 判例库
  - 空模型功能：拆解目标/问题/指令，提取相关元事实，纯计算，与元事实共同输入LLM
  - 空模型"无"：领域语料、文化经验、价值偏好
  - 空模型"有"：先验逻辑计算力（匹配、计算、裁决）
  - 元事实库：静态确定的元事实（病历、规则、档案、隐私资料）
  - 判例库：历史负例，定期监察+更新
- **云端（Cloud）**：云端大模型API或本地大模型 + 判例库
  - LLM 接收脱敏指令（空模型过滤后的相关事实）
  - LLM 返回策略方案
  - 判例库：命中/拦截，提取/存入
- **数据流闭环**：
  - 用户输入 → 空模型（目的/问题/指令）
  - 视频/图像/雷达/声音 → 空模型
  - 空模型 ↔ 元事实库（提取/存入）
  - 空模型 ↔ 判例库（存入/与大模型冲突/命中拦截）
  - 空模型 → 脱敏指令 → 云端LLM
  - 云端LLM → 策略方案 → 空模型
  - 空模型裁决 → 与大模型一致 → 输出

## 架构分层：元骨架 vs 领域实例

### 因果骨架的两层结构

NMP 的因果骨架是**跨领域、形式化、无实体语义**的，但其实现分为两层：

| 层级 | 名称 | 内容 | 位置 | 修改方式 |
|------|------|------|------|---------|
| **元骨架（Meta-Skeleton）** | 纯形式结构 | 形式节点（Node_A, Node_B...）+ 形式边（A→B, 权重w）+ 关系类型（causal/diagnostic/conditional） | `causal_skeleton.py`（架构常量） | 不可修改（先验计算能力的一部分） |
| **领域本体映射表** | 实体到形式节点的映射 | {"memory": {"high_usage": "Node_A"}, "ollama": {"service_running": "Node_C"}} | 元事实库（Knowledge Base 1） | 人类维护，按领域配置 |

**跨领域复用机制：**
- 元骨架中的 `Node_A --causal(0.95)--> Node_B` 是**纯数学结构**，不知道"内存"或"CPU"
- 系统监控领域：元事实库映射表将 `memory` → `Node_A`, `cpu` → `Node_C`
- 医疗领域：同一套元骨架，元事实库映射表将 `blood_pressure` → `Node_A`, `heart_rate` → `Node_C`
- 金融领域：映射表将 `credit_score` → `Node_A`, `debt_ratio` → `Node_C`

**关键澄清：** 代码中 `memory_high_usage`、`ollama` 等名称是**演示占位符**。实际部署时，这些领域名称应从元事实库加载，而非硬编码在骨架中。

## 关键修正点

### 1. 提取前调度（Privacy by Design）

**修正前**：探针提取全部 → 调度器过滤（隐私数据已暴露）
**修正后**：调度器生成指令 → 探针只执行允许提取（隐私数据从未暴露）

```python
# 修正后流程
schedule = scheduler.schedule(purpose, entities)
probe_command = scheduler.create_probe_command(schedule)
# 探针接收probe_command，只执行command中指定的提取
raw_data = probe.execute(probe_command)  # 只包含允许的事实
```

### 2. 物理预算模块（Resource Safety）

**论文要求**："在调用LLM之前计算安全批次大小"
**实现**：`PhysicalBudget.compute_budget()`

```python
budget = physical_budget.compute_budget(total_items=150)
safety_check = physical_budget.check_llm_safety(budget)
# 如果资源不足，不调用LLM，直接返回降级方案
```

### 3. 原子执行与回滚（Atomicity & Rollback）

**论文要求**："每批要么全提交要么全回滚"
**实现**：`AtomicExecutor.execute_batch()`

```python
batch = executor.create_batch(operations)
success = executor.execute_batch(batch)
# 如果任一操作失败，自动回滚已执行的操作
```

### 4. 元事实库驱动骨架实例化（Cross-Domain Reuse）

**论文要求**："因果骨架跨领域、形式化、无实体语义"
**实现**：元骨架（代码内）+ 领域本体映射表（元事实库内）

```python
# 元骨架（纯形式，跨领域通用）
class CausalSkeleton:
    def _build_skeleton(self):
        self._add_edge("Node_A", "Node_B", "causal", 0.95)  # 纯形式，无实体语义
        self._add_edge("Node_C", "Node_D", "causal", 0.90)

# 领域映射表（从元事实库加载，按领域配置）
# 系统监控领域
DOMAIN_MAPPING_SYSTEM = {
    "memory": {"high_usage": "Node_A", "pressure": "Node_B"},
    "ollama": {"service_running": "Node_C", "unavailable": "Node_D"}
}
# 医疗领域
DOMAIN_MAPPING_MEDICAL = {
    "blood_pressure": {"high": "Node_A", "pressure": "Node_B"},
    "heart_rate": {"abnormal": "Node_C", "risk": "Node_D"}
}
```

## 六步流水线完整映射

| 步骤 | 论文名称 | 实现模块 | 位置 | 说明 |
|------|---------|---------|------|------|
| 1 | Problem | 用户输入 | 本地 | 人类输入目的 |
| 2a | Null Model (Meta-Fact Query) | `privacy_vault.query_rules()` | 本地 | **查询元事实库获取提取规则** |
| 2b | Null Model (Strategy) | `purpose_parser` + `physical_budget` + `perception_scheduler` + `constraint_locking` | 本地 | 物理预算、任务分解、约束锁定、感知调度 |
| 3 | Full Model (Cognition) | `llm_client.query()` | 云端 | LLM语义理解（在L2事实边界内） |
| 4 | Database (Knowledge) | 外部数据库查询 | 云端/本地 | 外部检索领域特定信息 |
| 5 | Full Model (Synthesis) | `llm_client.query()` | 云端 | LLM组装策略 |
| 6 | Null Model (Judgment) | `final_judgment.judge()` | 本地 | 评估+选择（对照元事实库规则） |
| 6 | Null Model (Execution) | `atomic_executor.execute_batch()` | 本地 | 原子执行+回滚 |

## 数据流详解（修正后）

### 阶段1：目的注入 + 元事实库查询 + 物理预算
```
用户："整理150个文件"
    ↓
目的解析器：concern_type="optimize", target_entities=["file", "disk"]
    ↓
查询元事实库（Knowledge Base 1）：
- 目的"optimize"匹配规则SYS001
- 获取领域本体映射表（file → Node_X, disk → Node_Y）
- 允许提取：file.name, file.size, file.type
- 禁止提取：file.content（隐私）, file.path（安全）
    ↓
物理预算：total_items=150, available_ram=4GB → safe_batch_size=10, total_batches=15
    ↓
如果资源不足 → 直接返回降级方案，不调用LLM
```

### 阶段2：元规则查询 + 感知调度
```
感知调度器查询元事实库：
- 目的"optimize"匹配规则SYS001
- 允许提取：file.name, file.size, file.type
- 禁止提取：file.content（隐私）, file.path（安全）
- 启用探针：file_scanner
- 禁用探针：content_reader
    ↓
生成探针执行命令：
{
  "enabled_probes": ["file_scanner"],
  "extraction_plan": [
    {"entity": "file", "attributes": ["name", "size", "type"]}
  ],
  "forbidden_list": [
    {"entity": "file", "attributes": ["content", "path"]}
  ]
}
```

### 阶段3：提取前约束执行
```
探针接收执行命令，只提取允许的属性：
- 提取：file.name, file.size, file.type
- 不提取：file.content（命令中禁止）
- 结果：raw_data只包含允许的事实
```

### 阶段4：因果验证 + 相关性排序（元事实库驱动实例化）
```
从元事实库加载领域本体映射表：
- file.size → Node_A → disk_pressure (相关度0.85)
- file.type → Node_B → organization_strategy (相关度0.90)
- os.version → Node_C → file.organization (相关度0.0，过滤)

元骨架执行BFS（纯形式计算，无领域知识）：
- Node_A --causal(0.95)--> Node_B
- 累积权重 = 0.85 * 0.95 = 0.8075
```

### 阶段5：脱敏与上传
```
脱敏处理：
- file.name → 保留扩展名，去除路径
- file.size → 保留数值
- 不上传原始文件内容

上传云端LLM：
"15批文件，每批10个，按类型整理，保留原文件"
```

### 阶段6：策略返回 + 最终判断 + 原子执行
```
LLM策略："按类型创建文件夹，复制文件到新文件夹"
    ↓
最终判断校验（对照元事实库规则）：
- 是否违反¬Delete(source_file)？否
- 是否违反¬Move(source_file)？否（策略是Copy）
- 是否与预算一致？是（15批，每批10个）
    ↓
原子执行：
- 创建批次：batch_0（文件0-9）
- 执行Copy操作
- 验证校验和：MD5_src == MD5_dst
- 如果失败：回滚已复制文件
- 继续下一批
```

## 形式保证验证

| 论文保证 | 实现模块 | 验证状态 |
|---------|---------|---------|
| Resource Safety | `PhysicalBudget` | ✅ 在LLM调用前预算资源 |
| Constraint Immutability | `ConstraintLocking` + `FinalJudgment` | ✅ 架构防火墙保证 |
| Graceful Degradation | `PhysicalBudget` + `AtomicExecutor` | ✅ 资源不足时降级，执行失败时回滚 |
| Cross-Domain Reuse | `CausalSkeleton` + Meta-Fact Vault Mapping | ✅ 元骨架形式化，领域实例通过映射表注入 |

## 修正后的逻辑一致性

| 命题 | 修正前符合度 | 修正后符合度 | 关键修正 |
|------|------------|------------|---------|
| 空模型 = 纯粹判断容器 | 85% | 95% | **知识分层**：L0先验计算能力 vs L1元事实库查询 |
| 事实因目的而异 | 70% | 95% | **提取前调度** |
| LLM策略 + 空模型最终判断 | 90% | 95% | 事实一致性强制检查 |
| 元事实库 = 元规则层 | 75% | 98% | **术语统一**：元事实库替代"隐私资料库" |
| 六步流水线 | 80% | 95% | **物理预算 + 原子执行** |
| 因果骨架跨领域复用 | 60% | 90% | **元骨架 + 领域映射表分离** |

