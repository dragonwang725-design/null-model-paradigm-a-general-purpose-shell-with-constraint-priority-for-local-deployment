"""
LLM Client - 云端大模型接口

设计原则：
1. 最小化：只负责发送/接收，不做任何本地处理
2. 只读：不访问本地文件系统
3. 无状态：每次调用独立，不保留上下文
4. 受约束：接收的数据必须经过空模型脱敏和过滤

注意：这不是"智能体"，这是"被笼养的知识源"
"""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM响应结构"""
    strategy_id: str
    purpose: str
    actions: list
    confidence: float
    reasoning: str
    fallback: Optional[Dict[str, Any]] = None
    raw_response: str = ""


class LLMClient:
    """
    LLM客户端

    功能：
    1. 将空模型过滤后的结构化事实+目的发送给云端LLM
    2. 接收LLM的策略方案
    3. 不做任何策略验证（验证由空模型的Final Judgment完成）

    约束：
    - 只发送JSON结构化数据
    - 不发送原始感知数据
    - 不发送隐私资料库内容
    - 不接收可执行代码（只接收文本策略）
    """

    def __init__(self, api_endpoint: str = "https://api.openai.com/v1", 
                 model: str = "gpt-4", api_key: Optional[str] = None):
        self.api_endpoint = api_endpoint
        self.model = model
        self.api_key = api_key

    def query(self, purpose: str, filtered_facts: list, 
              judgment_units: list, uncertainty: list,
              instruction: str = "") -> LLMResponse:
        """
        向LLM查询策略

        Args:
            purpose: 人类目的（已脱敏）
            filtered_facts: 空模型过滤后的相关事实
            judgment_units: 空模型生成的判断单元
            uncertainty: 不确定性边界
            instruction: 额外指令（如"禁止引入外部知识"）

        Returns:
            LLMResponse: 策略方案
        """
        # 构造prompt
        system_prompt = """你是一位策略顾问。你的职责是基于提供的事实和判断单元，给出策略建议。

约束：
1. 你只能基于以下提供的事实和判断单元进行推理。
2. 如果判断单元中有gap类型（事实缺失），你必须明确告知"无法判断"。
3. 禁止引入训练数据中的外部知识。
4. 禁止做价值判断（如"你应该..."），只提供"如果...那么..."的条件策略。
5. 你的输出将被本地空模型验证，不符合事实约束的策略会被拒绝。
"""

        user_prompt = self._construct_prompt(
            purpose=purpose,
            facts=filtered_facts,
            judgments=judgment_units,
            uncertainty=uncertainty,
            instruction=instruction
        )

        # 调用LLM API（这里用伪代码，实际应替换为真实API调用）
        raw_response = self._call_api(system_prompt, user_prompt)

        # 解析响应
        parsed = self._parse_response(raw_response)

        return LLMResponse(
            strategy_id=parsed.get("strategy_id", "unknown"),
            purpose=purpose,
            actions=parsed.get("actions", []),
            confidence=parsed.get("confidence", 0.5),
            reasoning=parsed.get("reasoning", ""),
            fallback=parsed.get("fallback"),
            raw_response=raw_response
        )

    def _construct_prompt(self, purpose: str, facts: list, 
                          judgments: list, uncertainty: list,
                          instruction: str) -> str:
        """构造发送给LLM的prompt"""

        facts_text = json.dumps(facts, indent=2, ensure_ascii=False)
        judgments_text = json.dumps(judgments, indent=2, ensure_ascii=False)
        uncertainty_text = json.dumps(uncertainty, indent=2, ensure_ascii=False)

        prompt = f"""用户目的：{purpose}

以下是由本地空模型提取并验证的相关事实（按相关性排序）：
{facts_text}

以下是由本地空模型生成的形式判断单元（含逻辑轨迹与置信度）：
{judgments_text}

不确定性边界：
{uncertainty_text}

{instruction}

请基于以上信息，生成策略建议。输出格式必须是JSON：
{{
  "strategy_id": "str_xxx",
  "actions": [
    {{
      "action_type": "recommend",
      "target": "...",
      "parameters": {{}},
      "reasoning": "基于事实X和判断单元Y..."
    }}
  ],
  "confidence": 0.85,
  "reasoning": "总体推理说明",
  "fallback": {{
    "action_type": "...",
    "reasoning": "如果主策略失败..."
  }}
}}"""

        return prompt

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """
        调用LLM API

        注意：这是占位实现。实际应替换为：
        - OpenAI API
        - Anthropic API
        - 本地Ollama API
        - 或其他LLM服务
        """
        # 伪代码：实际API调用
        # import requests
        # response = requests.post(self.api_endpoint, json={
        #     "model": self.model,
        #     "messages": [
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt}
        #     ]
        # })
        # return response.json()["choices"][0]["message"]["content"]

        # 返回模拟响应（用于测试）
        return json.dumps({
            "strategy_id": "str_demo_001",
            "actions": [
                {
                    "action_type": "recommend",
                    "target": "user",
                    "parameters": {"message": "基于当前系统状态，建议保持现状"},
                    "reasoning": "内存使用率63.8%处于正常范围，Ollama服务运行正常"
                }
            ],
            "confidence": 0.85,
            "reasoning": "系统状态正常，无需干预",
            "fallback": {
                "action_type": "recommend",
                "reasoning": "如果后续出现异常，请重新查询"
            }
        }, ensure_ascii=False)

    def _parse_response(self, raw_response: str) -> Dict[str, Any]:
        """解析LLM的JSON响应"""
        try:
            # 尝试直接解析JSON
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # 如果不是JSON，尝试从文本中提取JSON
            import re
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            # 如果无法解析，返回原始文本
            return {
                "strategy_id": "parse_failed",
                "actions": [{"action_type": "recommend", "target": "user", "parameters": {"message": raw_response[:500]}}],
                "confidence": 0.0,
                "reasoning": "LLM响应格式异常，无法解析为JSON"
            }


# 便捷函数
def create_llm_client(endpoint: str = "https://api.openai.com/v1", 
                      model: str = "gpt-4") -> LLMClient:
    return LLMClient(api_endpoint=endpoint, model=model)
