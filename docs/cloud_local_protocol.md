# 云端-本地交互协议

## 协议定位

这是Null Model（本地）与Full Model（云端LLM）之间的**数据契约**。它定义了：
1. 本地向云端发送什么（脱敏后的结构化事实）
2. 云端向本地返回什么（文本策略方案）
3. 双方都不允许做什么（架构防火墙）

## 核心原则

### 本地 → 云端
- **只发送结构化JSON**，不发送原始感知数据
- **只发送相关事实**，不发送全量信息
- **只发送脱敏后数据**，不发送隐私标识
- **不发送隐私资料库内容**

### 云端 → 本地
- **只返回文本策略**，不返回可执行代码
- **只返回建议**，不返回命令
- **不请求额外数据**，不主动查询本地
- **承认不确定性**，不编造事实

## 请求格式（本地 → 云端）

```json
{
  "protocol_version": "nmp-1.0",
  "message_type": "strategy_request",
  "session_id": "uuid-xxx",
  "timestamp": "2026-06-09T12:00:00Z",

  "human_purpose": "检查系统状态",
  "purpose_structure": {
    "concern_type": "diagnosis",
    "target_entities": ["memory", "ollama"],
    "evaluation_dimensions": ["performance", "availability"],
    "temporal_scope": "current"
  },

  "relevant_facts": [
    {
      "fact_id": "f_mem_001",
      "entity": "memory",
      "attribute": "usage_percent",
      "value": 63.8,
      "confidence": 1.0,
      "source": "psutil"
    }
  ],

  "judgment_units": [
    {
      "unit_id": "ju_001",
      "unit_type": "descriptive",
      "conclusion": "memory_state_normal",
      "confidence": 0.9,
      "logic_trace": "memory_used=63.8% AND free=3.07GB → no_pressure"
    }
  ],

  "uncertainty_boundary": [
    "实体'gpu'的事实缺失，无法评估"
  ],

  "instruction": "基于以上事实与判断单元，给出策略建议。禁止引入外部知识。"
}
```

## 响应格式（云端 → 本地）

```json
{
  "protocol_version": "nmp-1.0",
  "message_type": "strategy_response",
  "session_id": "uuid-xxx",
  "timestamp": "2026-06-09T12:00:01Z",

  "strategy_id": "str_001",
  "status": "success",

  "actions": [
    {
      "action_type": "recommend",
      "target": "user",
      "parameters": {
        "message": "系统状态正常，无需干预"
      },
      "reasoning": "基于事实f_mem_001和判断单元ju_001，内存状态正常"
    }
  ],

  "confidence": 0.85,
  "reasoning": "总体推理说明",

  "fallback": {
    "action_type": "recommend",
    "reasoning": "如果后续出现异常，请重新查询"
  },

  "uncertainty_acknowledged": [
    "gpu状态未知，策略不涉及GPU相关建议"
  ]
}
```

## 错误格式

```json
{
  "protocol_version": "nmp-1.0",
  "message_type": "error",
  "session_id": "uuid-xxx",
  "error_code": "INSUFFICIENT_FACTS",
  "error_message": "提供的事实不足以支撑策略生成",
  "requested_facts": ["gpu.usage_percent", "gpu.temperature"]
}
```

## 架构防火墙

| 操作 | 本地允许 | 云端允许 | 说明 |
|------|---------|---------|------|
| 读取本地文件 | ✓ Null Model | ✗ LLM | LLM只能读取文本内容，不能主动请求 |
| 写入本地文件 | ✓ Null Model | ✗ LLM | LLM零写入权限 |
| 执行系统命令 | ✓ Null Model | ✗ LLM | LLM零执行权限 |
| 修改执行计划 | ✓ Null Model | ✗ LLM | LLM零修改权限 |
| 请求额外数据 | ✗ | ✗ | 单次请求-响应，不维护会话状态 |
| 返回可执行代码 | ✗ | ✗ | 只返回文本策略 |
| 返回外部链接 | ✗ | ✗ | 防止钓鱼/恶意链接 |
| 使用外部知识 | ✗ | ✗ | LLM只能使用提供的事实 |

## 安全机制

1. **TLS加密**：所有通信必须TLS 1.3
2. **请求签名**：本地请求带HMAC签名，防止篡改
3. **响应校验**：云端响应带校验和，防止中间人攻击
4. **超时机制**：LLM响应超时（默认30秒），Null Model回退到默认值
5. **速率限制**：防止LLM被滥用

## 版本演进

| 版本 | 特性 |
|------|------|
| nmp-1.0 | 基础事实+策略交换 |
| nmp-1.1 | 支持时序事实（趋势、变化） |
| nmp-1.2 | 支持反事实请求（"如果...会怎样"） |
| nmp-2.0 | 支持多轮协商（LLM请求澄清，Null Model响应） |
