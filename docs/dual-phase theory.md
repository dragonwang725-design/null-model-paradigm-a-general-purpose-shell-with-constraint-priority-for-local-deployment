
# 元事实库（Meta-Fact Vault）设计


> **别名：知识库1（Knowledge Base 1）、隐私资料库（Privacy Vault）**
> 
> 注意："隐私资料库"是旧称，强调其隐私保护属性；"元事实库"是新称，强调其作为**人类确认的静态事实层**的本质定位。两者指同一实体。

## 定位

元事实库不是"数据库"，也不是单纯的"隐私合规工具"。它是**人类确认的静态事实层（Human-Confirmed Static Fact Layer）**，是空模型在提取任何事实之前必须查询的**先验约束源**。

> **核心原则：隐私不是"提取后删除"，而是"提取动作本身被元规则约束"。**

### 本质定义

元事实库是**确定性、静态性、人类维护**的事实集合，与 LLM 的**概率性、动态性、模型内部**训练知识形成严格对立：

| 维度 | 元事实库（Knowledge Base 1） | LLM 训练知识 |
|------|---------------------------|-------------|
| **确定性** | 100% 确定 | 概率性 |
| **修改权** | 仅人类可修改 | 模型内部权重，不可直接修改 |
| **可见性** | 对空模型只读，对 LLM **完全不可见** | 对 LLM 内部可见，对空模型不可见 |
| **作用** | 约束提取动作、提供因果映射、存储档案 | 提供语言理解、生成候选策略 |
| **来源** | 人类确认、规则录入、档案导入、病历系统 | 互联网语料、预训练数据 |
| **内容示例** | ¬Delete(source_file)、性别、病历、设备规格 | "C盘满了要清理"、文化经验、统计模式 |

### 与空模型的关系

**空模型查询元事实库，但不"拥有"元事实库。**

类比：
- 空模型 = CPU（有计算能力，无数据）
- 元事实库 = 内存（有数据，无计算能力）
- 查询 = CPU 读取内存（数据进入 CPU 寄存器，但不成为 CPU 的"知识"）

空模型在每次任务开始时查询元事实库：
1. "这个目的允许提取哪些实体/属性？"
2. "这个目的禁止提取哪些实体/属性？"
3. "这个领域的因果映射表是什么？"
4. "历史反馈中有没有误报/漏报记录？"

查询结果是**约束条件**，不是空模型的"记忆"。任务结束后，约束条件丢弃，空模型回到"无记忆"状态。

## 核心功能

1. **目的-规则映射**：给定人类目的，返回允许/禁止的提取策略
2. **感知调度指令**：决定启用哪些探针、哪些模型、哪些参数
3. **领域本体映射**：将领域实体（memory、ollama、blood_pressure）映射到因果骨架的形式节点（Node_A、Node_B）
4. **历史经验反馈**：基于日志调整提取策略（降低误报、提高召回）
5. **元事实校准**：提供感知器特性（如"夜间摄像头帧率降低"）以校准提取置信度

## 数据结构

### 顶层结构

```json
{
  "vault_id": "home_security_v1",
  "version": "2026.06.09",
  "domains": ["home_security", "system_monitor"],
  "rules": [...],
  "knowledge": [...],
  "logs": [...],
  "meta_facts": [...],
  "domain_ontology_mappings": [...]
}
```

### 规则（Rules）

规则是**不可违背的硬约束**。空模型必须遵守，不得覆盖。

```json
{
  "rule_id": "R001",
  "name": "入侵检测隐私规则",
  "trigger": {
    "purposes": ["anomaly_detection", "intrusion_alert", "security_monitor"],
    "entities": ["human_shape"],
    "priority": 100
  },
  "permitted": {
    "extractions": [
      {
        "entity": "human_shape",
        "attributes": ["presence", "count", "motion_direction", "bounding_box"],
        "confidence_threshold": 0.7,
        "retention": "7_days"
      },
      {
        "entity": "time",
        "attributes": ["timestamp", "duration"],
        "granularity": "hour",
        "retention": "30_days"
      },
      {
        "entity": "location",
        "attributes": ["zone_id"],
        "anonymization": "zone_alias"
      }
    ],
    "probes": ["video_human_detection", "radar_motion"],
    "models": ["yolov8n-person"]
  },
  "forbidden": {
    "extractions": [
      {"entity": "face", "attributes": ["facial_features", "identity", "emotion"]},
      {"entity": "audio", "attributes": ["voice_print", "conversation_content", "speaker_identity"]},
      {"entity": "video", "attributes": ["raw_frame", "full_resolution"]}
    ],
    "probes": ["audio_recorder", "face_recognition"],
    "models": ["facenet", "speaker_id"]
  },
  "alert_conditions": [
    {
      "condition": "human_shape.count > 1 AND time.hour BETWEEN 0 AND 5",
      "action": "urgent_extract_additional",
      "additional_permitted": [{"entity": "audio", "attributes": ["loud_sound_detected"]}]
    }
  ],
  "derived_constraints": [
    "¬Upload(raw_video_frame)",
    "¬Store(face_embedding)",
    "¬Transmit(audio_waveform)"
  ]
}
```

### 领域本体映射（Domain Ontology Mappings）

**新增结构**：将领域实体映射到因果骨架的形式节点，实现跨领域复用。

```json
{
  "mapping_id": "M001",
  "domain": "system_monitor",
  "description": "系统监控领域的因果骨架映射",
  "mappings": {
    "memory": {
      "high_usage": "Node_A",
      "low_free": "Node_B",
      "pressure": "Node_C"
    },
    "cpu": {
      "high_usage": "Node_D",
      "pressure": "Node_E"
    },
    "disk": {
      "high_usage": "Node_F",
      "pressure": "Node_G"
    },
    "ollama": {
      "service_running": "Node_H",
      "service_unavailable": "Node_I",
      "model_unavailable": "Node_J",
      "model_loadable": "Node_K"
    }
  }
}
```

```json
{
  "mapping_id": "M002",
  "domain": "medical",
  "description": "医疗领域的因果骨架映射（复用同一套元骨架）",
  "mappings": {
    "blood_pressure": {
      "high": "Node_A",
      "low": "Node_B",
      "pressure": "Node_C"
    },
    "heart_rate": {
      "abnormal": "Node_D",
      "pressure": "Node_E"
    },
    "blood_sugar": {
      "high": "Node_F",
      "pressure": "Node_G"
    }
  }
}
```

### 知识（Knowledge）

知识是**人类确认的领域事实**，供空模型在提取时参照。不是LLM的训练数据，而是**硬编码的先验**。

```json
{
  "knowledge_id": "K001",
  "domain": "system_monitor",
  "entity": "memory",
  "fact": "8GB RAM运行7B参数模型需要约4GB可用内存",
  "source": "human_confirmed",
  "confidence": 1.0,
  "applies_to": ["ollama", "llm_local"]
}
```

### 日志（Logs）

日志是**历史执行记录**，用于反馈优化。

```json
{
  "log_id": "L001",
  "timestamp": "2026-06-08T23:15:00",
  "purpose": "anomaly_detection",
  "extracted_facts": ["human_shape.presence", "human_shape.count"],
  "outcome": "false_positive",
  "feedback": "邻居夜归，非入侵",
  "adjustment": {
    "rule_id": "R001",
    "change": "increase_motion_threshold_from_0.3_to_0.5"
  }
}
```

### 元事实（Meta-Facts）

元事实是**关于事实的事实**，用于校准感知器。

```json
{
  "meta_fact_id": "MF001",
  "entity": "video_camera",
  "attribute": "night_mode",
  "fact": "夜间帧率从30fps降至15fps，人形检测置信度需下调0.15",
  "calibration": {
    "day_confidence": 0.85,
    "night_confidence": 0.70
  }
}
```

## 查询接口

空模型通过以下接口查询元事实库：

```python
# 伪代码
vault = MetaFactVault.load("home_security_v1")

# 1. 根据目的获取规则
rules = vault.query_rules(purpose="anomaly_detection", entities=["human_shape"])
# 返回: [R001, R003]（匹配的规则列表）

# 2. 获取感知调度指令
schedule = vault.get_perception_schedule(rules=rules)
# 返回: {
#   "enabled_probes": ["video_human_detection", "radar_motion"],
#   "disabled_probes": ["audio_recorder", "face_recognition"],
#   "enabled_models": ["yolov8n-person"],
#   "confidence_thresholds": {"human_shape": 0.7}
# }

# 3. 获取提取权限
permissions = vault.get_extraction_permissions(rules=rules)
# 返回: {
#   "allowed": [{"entity": "human_shape", "attributes": ["presence", "count"]}],
#   "forbidden": [{"entity": "face", "attributes": ["identity"]}]
# }

# 4. 获取领域本体映射（新增）
mapping = vault.get_ontology_mapping(domain="system_monitor")
# 返回: {"memory": {"high_usage": "Node_A", ...}, ...}

# 5. 获取历史反馈
feedback = vault.get_historical_feedback(purpose="anomaly_detection", zone="Zone-A")
# 返回: {"last_7_days_false_positive_rate": 0.15, "suggested_threshold": 0.5}
```

## 冲突解决

当多个规则冲突时（如"婴儿看护"需要提取哭声，但"隐私保护"禁止提取音频）：

1. **优先级比较**：规则中的`priority`字段，高优先级覆盖低优先级
2. **目的精确匹配**：更精确匹配当前目的的规则优先
3. **人类仲裁**：如果自动解决失败，暂停提取并请求人类确认

## 更新机制

```
定期监察 + 更新 → 元事实库
```

- **自动更新**：基于日志反馈自动调整阈值（如降低误报率）
- **人工审核**：规则变更需人类确认（特别是`forbidden`列表的缩减）
- **版本控制**：每次更新生成新版本，保留历史规则用于审计
- **领域映射更新**：新增领域时，人类维护新的本体映射表

## 与LLM的隔离

**元事实库对LLM完全不可见。** LLM：
- 不知道存在哪些规则
- 不知道哪些事实被过滤
- 不知道哪些感知器被禁用
- 不知道元事实库的存在
- 只接收**脱敏后的结构化事实**

这是架构防火墙的一部分：即使LLM被攻击或越狱，它也无法绕过元事实库的约束——因为约束在**本地空模型**中执行，不在云端。

## 跨领域复用示例

### 场景1：系统监控（已部署）
- 元骨架：`Node_A --causal--> Node_B`（纯形式）
- 元事实库映射：`memory.high_usage → Node_A`, `memory.pressure → Node_B`
- 元事实库规则：允许提取 CPU/内存/磁盘状态，禁止提取 IP/主机名

### 场景2：医疗诊断（新增领域）
- **同一套元骨架**：`Node_A --causal--> Node_B`（复用，零修改）
- 元事实库映射（新增）：`blood_pressure.high → Node_A`, `blood_pressure.pressure → Node_B`
- 元事实库规则（新增）：允许提取血压/心率/血糖，禁止提取患者姓名/身份证号

### 场景3：金融风控（新增领域）
- **同一套元骨架**：`Node_A --causal--> Node_B`（复用，零修改）
- 元事实库映射（新增）：`credit_score.low → Node_A`, `default_risk → Node_B`
- 元事实库规则（新增）：允许提取信用分/负债比/交易记录，禁止提取用户密码/银行卡号

**结论**：跨领域扩展不需要修改因果骨架代码，只需要在元事实库中新增**领域本体映射表**和**规则集**。

