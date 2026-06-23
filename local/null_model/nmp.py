#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事实约束LLM插件 —— 轻量化版
核心：以事实为唯一判断依据，压制LLM逻辑脑补、发散、幻觉
UI：基于Gradio，支持手动输入/文件导入事实库
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import gradio as gr
import numpy as np
from sentence_transformers import SentenceTransformer

# ========== 配置项 ==========
# 嵌入模型（多语言、轻量）
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
# 检索相关事实数量
TOP_K = 6
# 相关性阈值（低于此值的事实不参与约束）
SIMILARITY_THRESHOLD = 0.2
# 单条事实最小长度（过滤无意义碎片）
FACT_MIN_LENGTH = 15

# ========== 1. 事实向量检索核心（仅处理事实，剥离判例） ==========
class FactRetriever:
    """事实检索器：仅处理纯事实文本，聚焦与问题的强相关性"""
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.facts: List[str] = []  # 事实文本列表
        self.fact_embeddings: Optional[np.ndarray] = None  # 事实向量
    
    def load_facts(self, fact_text: str) -> None:
        """加载事实文本（支持换行/空行分隔）"""
        # 清洗事实：去重、过滤短文本、去空白
        raw_facts = [f.strip() for f in re.split(r'\n\n|\n', fact_text) if f.strip()]
        cleaned_facts = []
        seen = set()
        for fact in raw_facts:
            if (len(fact) >= FACT_MIN_LENGTH) and (fact not in seen):
                cleaned_facts.append(fact)
                seen.add(fact)
        self.facts = cleaned_facts
        
        # 生成事实向量
        if self.facts:
            self.fact_embeddings = self.model.encode(
                self.facts, 
                show_progress_bar=False,
                normalize_embeddings=True
            )
    
    def search_relevant_facts(self, question: str) -> List[Dict[str, Any]]:
        """检索与问题强相关的事实"""
        if not self.facts or self.fact_embeddings is None:
            return []
        
        # 生成问题向量
        q_embedding = self.model.encode(
            [question], 
            normalize_embeddings=True
        )[0]
        
        # 计算余弦相似度（已归一化，直接点积）
        similarities = np.dot(self.fact_embeddings, q_embedding)
        # 筛选高相关事实
        high_sim_indices = [
            idx for idx, sim in enumerate(similarities)
            if sim >= SIMILARITY_THRESHOLD
        ]
        # 按相似度排序，取TOP_K
        sorted_indices = sorted(
            high_sim_indices, 
            key=lambda idx: similarities[idx], 
            reverse=True
        )[:TOP_K]
        
        # 构造结果
        results = []
        for idx in sorted_indices:
            results.append({
                "fact_content": self.facts[idx],
                "similarity_score": round(float(similarities[idx]), 4)
            })
        return results

# ========== 2. LLM调用（兼容本地Ollama/模拟模式） ==========
def call_constrained_llm(prompt: str) -> str:
    """调用受事实约束的LLM，失败则返回模拟结果"""
    import requests
    try:
        # Ollama API调用（本地部署）
        payload = {
            "model": "qwen2.5:1.5b",  # 可替换为llama3/phi3等
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": 0.1,  # 极低温度，减少发散
                "top_p": 0.1,
                "seed": 42  # 固定种子，保证一致性
            }
        }
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["message"]["content"]
        raise Exception(f"Ollama响应异常：{response.status_code}")
    except Exception as e:
        print(f"⚠️ LLM调用失败：{e}，启用模拟模式")
        return "[模拟约束回复] 我仅基于提供的事实回答问题，未找到足够事实支撑时会明确说明，绝不会编造信息。"

# ========== 3. 核心处理逻辑（事实约束+LLM推理） ==========
def process_constrained_query(
    question: str,
    fact_text: str,
    fact_file: Optional[gr.File] = None
) -> Tuple[str, str, str]:
    """
    核心流程：加载事实 → 检索相关事实 → 构造约束Prompt → 调用LLM
    返回：LLM回答、相关事实JSON、约束Prompt
    """
    # 1. 校验输入
    if not question.strip():
        return "❌ 请输入有效问题", "", ""
    
    # 2. 加载事实（优先文件导入，其次手动输入）
    final_fact_text = ""
    if fact_file and fact_file.name:
        # 读取上传的事实文件（txt/md）
        try:
            with open(fact_file.name, "r", encoding="utf-8") as f:
                final_fact_text = f.read()
        except:
            return "❌ 事实文件读取失败（仅支持UTF-8编码）", "", ""
    elif fact_text.strip():
        final_fact_text = fact_text.strip()
    
    if not final_fact_text:
        return "❌ 未提供任何事实（请输入或上传事实文件）", "", ""
    
    # 3. 检索相关事实
    retriever = FactRetriever()
    retriever.load_facts(final_fact_text)
    relevant_facts = retriever.search_relevant_facts(question)
    
    if not relevant_facts:
        return "⚠️ 未找到与问题相关的事实，无法进行约束判断", "", ""
    
    # 4. 构造事实包（供展示）
    fact_package = {
        "question": question,
        "relevant_facts_count": len(relevant_facts),
        "relevant_facts": relevant_facts,
        "constraint_rule": "所有判断仅基于上述事实，禁止脑补/发散/编造"
    }
    fact_json = json.dumps(fact_package, indent=2, ensure_ascii=False)
    
    # 5. 构造极致约束的Prompt（核心：杜绝幻觉）
    facts_list = "\n".join([
        f"{i+1}. {fact['fact_content']}（相关度：{fact['similarity_score']}）"
        for i, fact in enumerate(relevant_facts)
    ])
    
    constrained_prompt = f"""# 核心规则（必须严格遵守）
1. 你的唯一判断依据是下方「相关事实」，**绝对禁止**使用任何外部知识、经验、猜测补充。
2. 仅回答与用户问题直接相关的内容，**禁止**发散、脑补、扩展逻辑、添加无关信息。
3. 如果「相关事实」不足以支撑回答，**必须明确回复**："根据现有事实无法判断"。
4. 回答必须简洁、精准，仅保留核心结论，无多余话术。

# 相关事实
{facts_list}

# 用户问题
{question}

# 你的回答（仅保留核心内容）
"""
    
    # 6. 调用LLM并返回结果
    llm_answer = call_constrained_llm(constrained_prompt)
    return llm_answer, fact_json, constrained_prompt

# ========== 4. Gradio UI（轻量化、聚焦核心） ==========
with gr.Blocks(title="事实约束LLM插件", theme=gr.themes.Base()) as demo:
    gr.Markdown("""
    # 🎯 事实约束LLM插件
    ### 核心能力：仅基于给定事实做判断，压制幻觉/脑补/逻辑发散
    - 事实是唯一判断依据，杜绝LLM使用外部知识编造答案
    - 高相关度筛选，仅保留与问题强相关的事实
    - 极致约束Prompt，强制LLM聚焦事实、简洁回答
    """)
    
    # 第一行：事实输入区 + 问题输入区
    with gr.Row():
        with gr.Column(scale=5):
            gr.Markdown("### 📝 事实库（输入或上传）")
            fact_text = gr.Textbox(
                label="手动输入事实（每行/空行分隔单条事实）",
                placeholder="示例：\n服务器内存总容量为16GB\n内存使用率超过90%时会触发告警\n当前内存使用率为95%\n告警阈值可通过配置文件修改",
                lines=8
            )
            fact_file = gr.File(
                label="或上传事实文件（.txt/.md）",
                file_types=[".txt", ".md"],
                type="file"
            )
        
        with gr.Column(scale=5):
            gr.Markdown("### ❓ 待判断问题")
            question = gr.Textbox(
                label="输入需要基于事实判断的问题",
                placeholder="示例：当前服务器内存使用率是否触发告警？",
                lines=4
            )
            submit_btn = gr.Button("🚀 基于事实判断", variant="primary")
    
    # 第二行：核心输出区
    with gr.Row():
        with gr.Column(scale=10):
            gr.Markdown("### ✅ 约束后LLM回答")
            answer_output = gr.Textbox(
                label="LLM仅基于事实的判断结果",
                lines=6,
                interactive=False
            )
    
    # 展开区：事实包 + Prompt（调试用）
    with gr.Accordion("🔍 调试信息（事实包+约束Prompt）", open=False):
        fact_json_output = gr.JSON(label="相关事实包（JSON）")
        prompt_output = gr.Textbox(
            label="生成的约束Prompt",
            lines=10,
            interactive=False
        )
    
    # 绑定事件
    submit_btn.click(
        fn=process_constrained_query,
        inputs=[question, fact_text, fact_file],
        outputs=[answer_output, fact_json_output, prompt_output]
    )
    
    # 运行说明
    gr.Markdown("""
    ---
    ### ⚙️ 使用说明
    1. 事实输入：手动输入（每行一条）或上传.txt/.md文件（UTF-8编码）
    2. 问题输入：提出需要基于事实判断的具体问题
    3. LLM部署：推荐启动本地Ollama（模型建议：qwen2.5/llama3），否则使用模拟回复
    4. 依赖安装：`pip install gradio sentence-transformers numpy requests`
    """)

# ========== 5. 启动插件 ==========
if __name__ == "__main__":
    # 本地启动，仅本机访问
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True
    )
