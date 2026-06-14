
# NMP 论文原理精要

> 来源：*The Null Model Paradigm: Constraint-First Architecture for Reliable LLM Agents*  
> 作者：loweswang  中文名： 王龙 
> 发布：Zenodo正式版（DOI：10.5281/zenodo.20463703，DOI：10.5281/zenodo.20636262)

---

## 一、问题诊断：DuMate崩溃的范式意义

### 观察事实
2026年5月，DuMate（本地部署的AI办公助手）在消费级设备（i5-7400, 8GB RAM, 120GB SSD, Win10）上执行文件整理任务时：
- 任务：整理约100个文本文件和数十个Word文档
- 指令："按内容和类型整理；汇总相同内容；保留原文件；保存到kb文件夹"
- 结果：连续三次失败，报错Internal Server Error: Bad Gateway

### 核心论点
**这不是工程缺陷，而是范式缺陷。**

当前Agent采用**Full-Model Paradigm（全模型范式）**：让单一LLM同时承担理解意图、规划操作、执行物理动作。LLM满载互联网语料、文化知识、统计模式，却缺乏物理世界所需的骨架结构。

---

## 二、AlphaGo直觉：结构先例

| 组件 | AlphaGo | NMP Agent |
|------|---------|-----------|
| 问题来源 | 对手的棋步 | 人类意图 + 世界状态 |
| 判断引擎 | MCTS + 价值网络 | **Null Model** |
| 知识来源 | 人类棋谱 / 自我对弈 | LLM + 元事实库 |
| 最终权威 | 引擎选择棋步 | **Null Model选择动作** |

**关键洞察**：AlphaGo/AlphaZero的搜索-评估引擎**没有围棋文化、没有人类直觉、没有开局库**——它只有通用的计算骨架（搜索、评估、选择）。人类棋谱只是候选来源，引擎决定哪一步真正执行。

NMP将这一分离推广到物理世界Agent：
- **LLM是开局库（Opening Book）**——提供候选策略
- **Null Model是棋手（Player）**——计算、评估、选择、执行

---

## 三、形式定义

### 3.1 三层双视角辩证（TDA）架构总览

以下流程图展示了NMP的哲学架构：输入层同时驱动LLM（认知生成）和空模型（计算判断），在结构化辩论层形成冲突图，最终由元受动极层的裁决AI在动态阈值下做出决策，经非认知结构性熔断器校验后输出。

<img width="2307" height="3089" alt="三层双视角（TDA）辩证架构流程图" src="https://github.com/user-attachments/assets/ff84ca1d-33ab-41f7-b4c8-b1024951d403" />

**架构分层说明：**

| 层级 | 名称 | 功能 | 关键机制 |
| :--- | :--- | :--- | :--- |
| **输入层** | Input Layer | 接收人类目的与自然语言问题 | — |
| **认知层** | LLM + 判例库 | 语言理解、策略生成、历史案例匹配 | 命中/拦截机制 |
| **计算层** | 空模型 + 元事实库 + 判例库 | 目的拆解、事实提取、约束校验、逻辑裁决 | 匹配、裁决、存入 |
| **辩论层** | 结构化辩论层 / 冲突图构建 | LLM输出与空模型输出的形式化对比 | 识别冲突、构建对抗图 |
| **裁决层** | 元受动极层 / 裁决AI | 动态阈值τ下的有依据随机裁决 | 历史先验分布 + 定期审计/异常介入 |
| **熔断层** | 非认知结构性熔断器 | 通过/否决/中断的刚性校验 | 人工审计/外部锚点的最高否决权 |
| **记忆层** | 外挂扬弃记忆 | 反馈误报/漏案例，更新判例库 | 经验数据中心 / 判例法体系 |
| **输出层** | Output Layer | 最终执行结果输出 | — |

### 3.2 Full Model（全模型）
知识层被领域语料、文化经验、价值偏好、自主目标生成机制**最大化饱和**的AI系统。当代LLM（GPT-4、Qwen、Claude）及其衍生Agent是典型全模型。

### 3.3 Null Model（空模型）
**知识自由的计算判断基底（Knowledge-free computational judgment substrate）**。

"Null"不是空集（∅），而是**撤离（Evacuation）**：
- 系统性地剥离所有**后天领域知识**（a posteriori knowledge）：领域语料、文化经验、价值偏好、自主目的
- 保留完整的**先验计算骨架**（a priori computational capacity）：判断、搜索、评估、约束满足、最优路径选择、校验和验证
- 不包含领域知识、文化数据、价值偏好、自主目的

**操作输入**：
1. 人类目的（Human Purpose）
2. 物理世界状态（Physical-world State，经元事实库规则过滤后）
3. 形式约束（物理学、数学、逻辑、因果性）
4. **元事实库规则**（Meta-Fact Vault Rules）：决定什么事实允许被提取

**操作输出**：
- 允许的动作序列（Permitted Action Sequences）
- 执行裁决（Execution Verdicts）

**所有语义解释所需的知识都向Full Model（LLM）查询，但LLM对Null Model的裁决零修改权。**

### 3.4 元事实库（Meta-Fact Vault / 知识库1）

**定位**：人类确认的静态事实层，空模型的**外部只读寄存器**。

**核心原则**：
- **静态确定性**：内容100%确定，由人类维护，非概率生成
- **提取前约束**：决定空模型**能否**从物理世界提取某类事实，而非提取后过滤
- **对LLM不可见**：即使LLM被攻击或越狱，也无法绕过——因为约束在本地空模型中执行

**内容组成**：

| 类型 | 说明 | 示例 |
| :--- | :--- | :--- |
| **元规则** | 不可违背的硬约束 | ¬Delete(source_file), ¬Move(source_file) |
| **元事实** | 确定性静态数据 | 性别、病历、设备规格、档案 |
| **历史档案** | 带人类反馈的执行记录 | 误报案例、成功修复记录 |
| **领域本体** | 因果骨架的实体映射表 | "memory" → Node_A, "ollama" → Node_C |

**与LLM训练知识的本质区别**：

| 维度 | 元事实库（知识库1） | LLM训练知识 |
| :--- | :--- | :--- |
| **确定性** | 100%确定 | 概率性 |
| **修改权** | 仅人类可修改 | 模型内部权重，不可直接修改 |
| **可见性** | 对空模型只读，对LLM不可见 | 对LLM内部可见，对空模型不可见 |
| **作用** | 约束提取动作、提供因果映射 | 提供语言理解、生成候选策略 |
| **更新方式** | 定期监察 + 人工更新 | 预训练/微调 |

> **命名说明**："隐私资料库"是元事实库的别名。隐私保护是元事实的**属性**（因为它们涉及敏感信息），而非库的**目的**。建议统一使用"元事实库"以避免误解。

### 3.5 LLM的约束机制：不是"剥夺权限"，而是"输入边界锁"

LLM拥有完整的语言理解和生成能力，它的"自由"在计算层面不受限制。它的"约束"体现在：

1. **输入边界锁**：LLM只能接收空模型过滤后的**相关事实+目的目标**，共同构成约束条件。LLM无法接触原始感知数据。
2. **目的边界锁**：LLM的策略必须服务于人类注入的目的，空模型会校验目的对齐性。
3. **事实边界锁**：LLM若引用不存在的事实，空模型会标记为"不一致"并降低置信度。

**类比**：LLM不是"被阉割的模型"，而是"在封闭考场答题的考生"：
- 考场提供所有必要的题目条件（空模型提取的事实）
- 考生可以任意推理（LLM的自由计算）
- 但答案必须符合给定条件（空模型的校验）
- 考生不能要求额外资料（LLM不能请求额外数据）

**关键澄清**：LLM与空模型是**两种功能模型**，不要混淆：
- **LLM** = 大语言模型，负责语言理解和策略生成
- **空模型** = 纯计算判断容器，负责事实提取、约束校验、最终裁决

### 3.6 六步流水线（Six-Step Pipeline）

1. **Problem**：人类以自然语言表达意图
2. **Null Model (Strategy Computation)**：查询元事实库获取提取规则 → 物理资源预算 → 数学任务分解 → 约束锁定 → 候选执行路径生成
3. **Full Model (Cognition)**：LLM执行语义理解与分类，只输出文本标签和知识片段
4. **Database (Knowledge)**：外部检索领域特定信息（在元事实库规则允许范围内）
5. **Full Model (Synthesis)**：LLM在Null Model约束下组装文本-only执行蓝图
6. **Null Model (Judgment & Execution)**：评估LLM蓝图的形式约束符合性（对照元事实库规则），选择最优允许路径，强制执行原子性，提供回滚保证
7. **Solution**：物理世界执行结果

---

## 四、三层架构防火墙与知识分层

### 4.1 三层架构防火墙

#### L1：意图注入（Intent Injection）——人类主权
人类提供目标、价值排序、成功标准。这一层**不可计算、不可委托**。

#### L2：Null Model层——计算判断引擎
**唯一拥有物理世界执行权限的层**。它不只是"过滤"LLM输出，而是**从零计算执行策略**。LLM（L3）拥有：
- 零文件系统写入权限
- 零进程生成权限
- 零修改执行计划权限

**四个刚性计算模块**：

1. **Physical Budgeting Module**：监控RAM、磁盘空间、文件句柄、网络状态。在调用任何LLM之前计算安全批次大小（如8GB机器上每批10个文件）。

2. **Mathematical Planning Module**：在复杂度和资源约束下将任务分解为最优原子操作序列。这是**规划计算**，不是知识查询。

3. **Constraint Formalization Module**：将自然语言意图转化为不可变的逻辑断言。例如"不删除原文件"形式化为公理 ¬Delete(S_source)，永久剪枝Delete类中的任何候选操作。

4. **Verification & Rollback Module**：强制执行因果性（每个效果有可追溯的原因）、同一性（复制文件保持校验和一致）、可逆性（每批要么全提交要么全回滚）。

#### L3：Full Model层——生成认知
LLM和外部数据库在此运行。它们的唯一权限：
- 读取文件内容（文本-only输入）
- 输出文本标签（如"Contract"、"Meeting Minutes"）
- 生成人类可读摘要

**零文件系统写入权限、零进程生成权限、零修改执行计划权限。**

### 4.2 知识分层总表

| 层级 | 知识/能力类型 | 性质 | 来源 | 是否可计算 | 是否可委托 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **L1** | 人类目的、价值判断 | 非计算性 | 人类注入 | ❌ | ❌ |
| **L2** | 先验计算能力（BFS、约束满足、校验和） | 形式化、跨领域 | 架构内置 | ✅ | ✅（给机器） |
| **L2 ↔ 元事实库** | 元规则、元事实、领域本体映射 | 静态确定性 | 人类确认维护 | ✅ | ✅（给机器） |
| **L3** | LLM训练知识（语料、文化、经验） | 概率性动态 | 预训练数据 | ✅ | ✅（给机器） |
| **L3 ↔ 外部DB** | 领域数据、实时信息 | 上下文依赖 | 外部系统 | ✅ | ✅（给机器） |

**核心洞察**：空模型的"无知识"是指**无后天领域知识**（a posteriori knowledge），而非**无先验计算能力**（a priori computational capacity）。因果骨架、约束满足、路径搜索属于先验计算能力，不是"知识"。元事实库提供的是**边界条件**（什么允许提取），不是空模型"学习"的内容。

---

## 五、DuMate案例：反事实分析

### 全模型范式的失败链
1. **无物理预算**：LLM尝试同时处理150+文件，耗尽8GB RAM
2. **无元事实库约束**：没有¬Delete(source_file)的形式化规则，LLM"统计性理解"了请求
3. **无原子性**：操作未分批次；中途崩溃导致文件系统不一致
4. **无回滚**：遇到Bad Gateway时，Agent生成道歉文本而非回滚部分复制

**LLM不是在"被缺失层支撑"，而是在物理世界上裸体翻滚。**

### NMP范式的反事实成功
1. **L2查询元事实库**：提取规则SYS001形式化约束：Operation ∈ {Copy}, ¬Delete, ¬Move
2. **L2物理模块**扫描F:\ai：150个文件，总大小X，可用RAM≈4GB（扣除OS占用）。计算安全批次大小为10。
3. **L3 LLM**每批只接收10个文件的文本内容，返回标签（如"Contract"）。
4. **L2**清洗标签（剥离路径遍历字符、阻断保留名称）。
5. **L2**执行Copy(src, dst)，验证校验和同一性（MD5_src = MD5_dst），因果日志记录，继续执行。
6. **如果LLM超时（Bad Gateway）**，L2不会崩溃。它优雅降级：标签默认回退到文件扩展名，复制继续执行，异常记录供人类审查。

---

## 六、形式保证

NMP架构提供全模型范式无法提供的三项结构保证：

1. **Resource Safety（资源安全）**：Null Model在调用LLM之前先预算资源，保证物理耗尽不可能由LLM过度生成导致。

2. **Constraint Immutability（约束不可变性）**：一旦¬Delete(S)在L2中被形式化（来自元事实库），任何LLM输出都无法覆盖它——由架构防火墙保证。

3. **Graceful Degradation（优雅降级）**：如果L3失败（超时、幻觉），L2回退到确定性默认值，保证系统始终处于安全状态。

---

## 七、AGI启示

当前工业实践通过**饱和**追求AGI：更多参数、更多数据、更多模态、更多自主行为。NMP认为这是一个**范畴错误**。

AGI不是一个膨胀的、"无所不知"的Full Model；它是一个最小的、"永不跌倒"的Null Model。

安全AGI的路径不是：
```
More Data → More Knowledge → More Autonomy
```

而是：
```
Harder Constraints → Reliable Judgment → Safe Execution
```

---

## 八、核心论断

> "The DuMate failure is not an anecdote; it is a paradigm indicator. LLM agents will continue to collapse in physical environments until the industry recognizes that generation without constraint is hallucination, and execution without judgment is destruction."

> "The Null Model Paradigm does not reject LLMs; it provides them with a structured examination hall. The LLM is not caged; it is given a clear proposition and verified facts, within which it can reason freely. The Null Model is not merely a cage; it is the examiner that sets the proposition, verifies the reasoning, and enforces the final verdict."

> "Intelligence is not the accumulation of knowledge; it is the discipline to know when not to act—and the hard shell that enforces that discipline."


