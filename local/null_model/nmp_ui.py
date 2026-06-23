#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMP 事实约束助手 —— 完整版
功能：向量检索元事实库 → 构建约束Prompt → 调用LLM → 展示结果
UI：基于 Gradio
"""

import os
import re
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import gradio as gr
from sentence_transformers import SentenceTransformer

# ========== 配置 ==========
DATA_ROOT = Path("./data")          # 知识库目录
TOP_K = 8                           # 检索事实数量
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# ========== 1. 向量检索模块（复用你的代码） ==========
class VectorRetriever:
    def __init__(self, folder_path: Path):
        self.folder_path = folder_path.resolve()
        self.model = None
        self.paragraphs = []
        self.embeddings = None
        
    def load_or_build(self):
        print(f"📂 加载知识库: {self.folder_path}")
        if self.model is None:
            self.model = SentenceTransformer(EMBEDDING_MODEL)
        
        all_paragraphs = []
        for file_path in self.folder_path.rglob('*'):
            if file_path.suffix.lower() not in ('.txt', '.md'):
                continue
            try:
                for encoding in ['utf-8', 'gbk', 'gb2312']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except:
                        continue
                else:
                    continue
            except Exception as e:
                continue
            
            paras = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 20]
            all_paragraphs.extend(paras)
        
        self.paragraphs = all_paragraphs
        if all_paragraphs:
            self.embeddings = self.model.encode(all_paragraphs, show_progress_bar=False)
        return self
    
    def search(self, question: str, top_k: int = TOP_K) -> List[Dict]:
        if not self.paragraphs or self.embeddings is None:
            return []
        q_embedding = self.model.encode([question])[0]
        similarities = np.dot(self.embeddings, q_embedding) / (np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(q_embedding) + 1e-8)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score < 0.15:
                break
            results.append({"content": self.paragraphs[idx], "score": round(score, 4)})
        return results

# ========== 2. LLM 调用模块（支持本地 Ollama / Mock） ==========
def call_llm(prompt: str) -> str:
    """尝试调用本地 Ollama，如果不可用则返回模拟响应"""
    import requests
    try:
        # 尝试连接 Ollama
        payload = {
            "model": "qwen2.5:1.5b",  # 你可以改成 qwen2.5:3b 或 llama3
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.3}
        }
        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()["message"]["content"]
        else:
            raise Exception("Ollama 服务异常")
    except Exception as e:
        # 如果 Ollama 没开，使用 Mock 模式（仅用于演示）
        print(f"⚠️ LLM 调用失败 ({e})，使用模拟模式")
        return f"[模拟回复] 基于检索到的事实，我建议您参考上述信息。\n(提示：请启动 Ollama 服务以获得真实回答)"

# ========== 3. 核心处理逻辑 ==========
def process_query(question: str, knowledge_dir: str) -> Tuple[str, str, str]:
    if not question:
        return "请输入问题", "", ""

    # 1. 确定检索路径
    root = Path(knowledge_dir) if knowledge_dir else DATA_ROOT
    if not root.exists():
        return f"❌ 路径不存在: {root}", "", ""

    # 2. 检索事实
    retriever = VectorRetriever(root).load_or_build()
    facts = retriever.search(question)
    
    if not facts:
        return "⚠️ 未找到相关事实，无法约束LLM。", "", ""

    # 3. 构建事实包（供显示）
    fact_package = {
        "question": question,
        "retrieved_facts": facts,
        "total": len(facts)
    }
    fact_json = json.dumps(fact_package, indent=2, ensure_ascii=False)

    # 4. 构建约束 Prompt（核心：注入事实，压制幻觉）
    facts_text = "\n".join([f"- {f['content']}" for f in facts])
    prompt = f"""你是一个严谨的助手。你**必须**基于下列“已知事实”来回答用户的问题。

【已知事实】
{facts_text}

【用户问题】
{question}

【回答要求】
1. 如果事实足够支撑，请基于事实给出简明回答。
2. 如果事实不足，请明确回答“根据现有事实无法判断”。
3. 禁止编造事实。

【你的回答】"""

    # 5. 调用 LLM
    answer = call_llm(prompt)

    return answer, fact_json, prompt

# ========== 4. Gradio UI ==========
with gr.Blocks(title="NMP 事实约束助手", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🧠 NMP 事实约束助手
    ### 基于本地知识库检索，压制 LLM 逻辑脑补与幻觉
    *空模型提取事实 → 元事实库约束 → LLM 仅作推理*
    """)
    
    with gr.Row():
        with gr.Column(scale=4):
            question_input = gr.Textbox(
                label="💬 你的问题", 
                placeholder="例如：我的服务器内存使用率一直很高，可能是什么原因？",
                lines=3
            )
            dir_input = gr.Textbox(
                label="📂 知识库路径", 
                value=str(DATA_ROOT),
                placeholder="留空则默认使用 ./data"
            )
            submit_btn = gr.Button("🚀 提交查询", variant="primary")
        
        with gr.Column(scale=6):
            answer_output = gr.Textbox(
                label="✅ LLM 约束回答", 
                lines=8,
                interactive=False
            )
    
    with gr.Accordion("📦 查看提取的事实包 (JSON) 与 Prompt", open=False):
        fact_json_output = gr.JSON(label="事实包数据")
        prompt_output = gr.Textbox(label="生成的约束 Prompt", lines=6, interactive=False)
    
    # 绑定事件
    submit_btn.click(
        fn=process_query,
        inputs=[question_input, dir_input],
        outputs=[answer_output, fact_json_output, prompt_output]
    )
    
    gr.Markdown("""
    ---
    **⚙️ 运行要求**：
    1. 将你的文档（.txt/.md）放入 `./data` 文件夹。
    2. 安装依赖：`pip install gradio sentence-transformers numpy requests`
    3. （可选）启动本地 Ollama 以获得高质量回答。
    """)

# ========== 5. 启动 ==========
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)