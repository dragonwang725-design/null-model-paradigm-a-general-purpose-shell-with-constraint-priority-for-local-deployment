#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信息提取机 
"""

import os
import re
import json
import platform
import subprocess
import datetime
from pathlib import Path
from typing import List, Dict, Any

import psutil
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, DATETIME
from whoosh.qparser import QueryParser
from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter

# 尝试导入 ollama，如果失败则设置标志
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("警告: ollama 未启动，增强模式不可用。")

# ========== 配置 ==========
DATA_ROOT = Path("./data")          # 数据根目录
SYSTEM_INFO_ENABLED = True          # 是否允许采集系统信息（实际采集与否由问题关键词决定）
OLLAMA_MODEL = "qwen2.5:1.5b"       # 小模型名称
MAX_MATCHES_FOR_SUMMARY = 15        # 摘要中最多使用的匹配片段数
CONTEXT_LINES = 1                   # 匹配行的上下文行数（用于读取原文，但摘要中不显示）

# 停用词
STOP_WORDS = set('的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 自己 这 那 什么 为什么 怎么 如何 哪个 多少 可以 能 请 帮 一下 吗 呢 吧 啊 哦 嗯'.split())

# 隐私脱敏正则（简单版）
PRIVACY_PATTERNS = [
    (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[IP]'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    (r'\b1[3-9]\d{9}\b', '[PHONE]'),
    (r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*[:=]\s*\S+', lambda m: m.group(0).split('=')[0] + '=[REDACTED]'),
]

def redact_text(text: str) -> str:
    for pattern, repl in PRIVACY_PATTERNS:
        if callable(repl):
            text = re.sub(pattern, repl, text)
        else:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:user|admin|root|administrator)\b', '[USER]', text, flags=re.IGNORECASE)
    return text

def simple_keywords(question: str) -> List[str]:
    words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9_]+', question)
    keywords = [w for w in words if w.lower() not in STOP_WORDS and len(w) > 1]
    return keywords

def llm_extract_keywords(question: str) -> List[str]:
    if not OLLAMA_AVAILABLE:
        return simple_keywords(question)
    prompt = f"""你是一个关键词提取助手。请从用户问题中提取出最重要的搜索关键词（人名、地名、术语、数字、代码等），每个关键词用空格分隔。只输出关键词列表，不要有其他内容。

用户问题：{question}
关键词："""
    try:
        # 设置连接地址（解决常见连接问题）
        client = ollama.Client(host='http://127.0.0.1:11434')
        response = client.generate(model=OLLAMA_MODEL, prompt=prompt)
        text = response['response'].strip()
        keywords = text.split()
        keywords = [k for k in keywords if len(k) > 1 and k.lower() not in STOP_WORDS]
        return keywords if keywords else simple_keywords(question)
    except Exception as e:
        print(f"小模型关键词提取失败: {e}，回退到简单分词")
        return simple_keywords(question)

# ========== 索引管理（支持自动检测编码）==========
class DocIndex:
    def __init__(self, folder_path: Path, index_dir: Path):
        self.folder_path = folder_path.resolve()
        self.index_dir = index_dir.resolve()
        self.schema = Schema(
            path=ID(stored=True, unique=True),
            filename=TEXT(stored=False),
            content=TEXT(stored=False, analyzer=RegexTokenizer() | LowercaseFilter() | StopFilter(stoplist=STOP_WORDS)),
            modified=DATETIME(stored=True)
        )
        if not exists_in(self.index_dir):
            self.index_dir.mkdir(parents=True, exist_ok=True)
            self.ix = create_in(self.index_dir, self.schema)
            self._build_index()
        else:
            self.ix = open_dir(self.index_dir)

    def _build_index(self):
        import chardet
        writer = self.ix.writer()
        for file_path in self.folder_path.rglob('*'):
            if file_path.suffix.lower() not in ('.txt', '.md'):
                continue
            with open(file_path, 'rb') as f:
                raw = f.read()
            if not raw:
                continue
            detected = chardet.detect(raw)
            encoding = detected.get('encoding', 'utf-8')
            try:
                content = raw.decode(encoding, errors='replace')
            except:
                continue
            try:
                stat = file_path.stat()
                writer.add_document(
                    path=str(file_path),
                    filename=file_path.name,
                    content=content,
                    modified=datetime.datetime.fromtimestamp(stat.st_mtime)
                )
            except Exception as e:
                print(f"索引文件失败 {file_path}: {e}")
        writer.commit()
        print(f"已为 {self.folder_path} 建立索引，共 {self.ix.doc_count()} 个文档")

    def search(self, keywords: List[str], limit: int = 50) -> List[Dict]:
        if not keywords:
            return []
        query_str = ' OR '.join([f'content:{kw}' for kw in keywords])
        with self.ix.searcher() as searcher:
            query = QueryParser("content", self.schema).parse(query_str)
            results = searcher.search(query, limit=limit)
            matches = []
            for res in results:
                file_path = Path(res['path'])
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except:
                    continue
                # 收集所有匹配行的上下文（用于摘要）
                contexts = []
                for i, line in enumerate(lines):
                    if any(kw.lower() in line.lower() for kw in keywords):
                        start = max(0, i - CONTEXT_LINES)
                        end = min(len(lines), i + CONTEXT_LINES + 1)
                        context = ''.join(lines[start:end]).strip()
                        contexts.append(context)
                if contexts:
                    matches.append({
                        'file': str(file_path),
                        'first_match': contexts[0],   # 只用第一个匹配作为摘要素材
                        'all_matches': contexts       # 保留全部（用于JSON）
                    })
            return matches

# ========== 系统信息采集（按需）==========
def collect_system_info(question: str = "") -> Dict:
    info = {}
    q_lower = question.lower()
    if any(w in q_lower for w in ['进程', 'cpu', '占用', 'process', '程序', '运行']):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'memory': proc.info['memory_percent']
                })
            except:
                pass
        info['top_processes'] = sorted(processes, key=lambda x: x['cpu'] or 0, reverse=True)[:10]
    if any(w in q_lower for w in ['内存', 'memory', 'ram']):
        mem = psutil.virtual_memory()
        info['memory'] = {
            'total_gb': round(mem.total / 1e9, 2),
            'available_gb': round(mem.available / 1e9, 2),
            'used_percent': mem.percent
        }
    if any(w in q_lower for w in ['崩溃', '错误', '日志', 'crash', 'error', 'log']):
        try:
            cmd = 'wevtutil qe System /c:10 /rd:true /f:text /q:"*[System[(Level=1 or Level=2)]]"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            events = result.stdout.split('\n\n')[:5]
            info['event_logs'] = [redact_text(e.strip()) for e in events if e.strip()]
        except Exception as e:
            info['event_logs'] = [f"获取日志失败: {e}"]
    return info

# ========== 摘要生成（无详情，只有多要点）==========
def simple_summary(question: str, matches: List[Dict]) -> str:
    """标准模式：从匹配片段中提取多个要点（去重后最多15条）"""
    if not matches:
        return "未找到任何匹配的真实信息。"
    # 收集所有第一个匹配的文本，去重（保持顺序）
    seen = set()
    points = []
    for m in matches:
        text = m['first_match']
        if text and text not in seen:
            seen.add(text)
            points.append(text)
            if len(points) >= MAX_MATCHES_FOR_SUMMARY:
                break
    if not points:
        return "未找到有效内容。"
    summary = f"根据检索，关于“{question}”的要点如下：\n"
    for i, p in enumerate(points, 1):
        # 截断过长内容（保留200字符）
        p_short = p[:200] + ('...' if len(p) > 200 else '')
        summary += f"{i}. {p_short}\n"
    return summary

def llm_summary(question: str, matches: List[Dict]) -> str:
    """增强模式：使用小模型生成多要点摘要"""
    if not OLLAMA_AVAILABLE:
        return simple_summary(question, matches)
    # 准备上下文（最多10个片段）
    contexts = []
    for m in matches[:10]:
        contexts.append(m['first_match'][:500])
    if not contexts:
        return "未找到相关内容。"
    prompt = f"""你是一个信息提炼助手。用户问题：{question}

以下是从本地文档中检索到的真实片段（每个片段可能不完整）：
{chr(10).join(contexts)}

请根据以上信息，生成一个多要点的回答。每个要点以短横线开头，总要点数量不限但尽量覆盖重要信息。不要添加任何虚构内容。回答："""
    try:
        client = ollama.Client(host='http://127.0.0.1:11434')
        response = client.generate(model=OLLAMA_MODEL, prompt=prompt, options={'num_predict': 400})
        summary = response['response'].strip()
        # 如果模型没有生成以短横线开头的要点，手动添加前缀
        if not summary.startswith('-'):
            summary = "要点如下：\n" + summary
        return summary
    except Exception as e:
        print(f"AI摘要生成失败: {e}，回退到标准模式")
        return simple_summary(question, matches)

# ========== 报告保存（只保存摘要，不保存匹配详情）==========
def save_report(report: dict, output_dir: str = "F:/reports"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    keywords_prefix = "_".join(report['keywords'][:3]) if report['keywords'] else "no_keyword"
    safe_prefix = re.sub(r'[\\/*?:"<>|]', '_', keywords_prefix)[:30]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{timestamp}_{safe_prefix}"
    # 文本报告：只包含摘要和简略系统信息
    txt_path = out_path / f"{base_name}.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"问题: {report['question']}\n")
        f.write(f"关键词: {', '.join(report['keywords'])}\n")
        f.write(f"模式: {'增强模式' if report['mode']=='enhanced' else '标准模式'}\n")
        f.write(f"检索知识库: {', '.join(report['selected_categories'])}\n")
        f.write(f"生成时间: {report['timestamp']}\n")
        f.write("\n" + "="*60 + "\n")
        f.write("【摘要】\n")
        f.write(report['summary'] + "\n")
        if report.get('system_info'):
            f.write("\n【系统信息】\n")
            if 'memory' in report['system_info']:
                mem = report['system_info']['memory']
                f.write(f"内存使用: {mem['used_percent']}% (可用 {mem['available_gb']}GB / 总计 {mem['total_gb']}GB)\n")
            if 'event_logs' in report['system_info']:
                f.write("最近系统错误:\n")
                for evt in report['system_info']['event_logs'][:2]:
                    f.write(f"  {evt[:150]}...\n")
    # JSON报告：完整摘要，供其他程序使用
    json_path = out_path / f"{base_name}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 报告已保存至: {txt_path}")
    print(f"📄 JSON 数据: {json_path}")

# ========== 主程序 ==========
def main():
    if not DATA_ROOT.exists():
        print(f"请创建数据根目录 {DATA_ROOT}，并在其下建立子文件夹，放入 .txt/.md 文件。")
        return

    categories = [d for d in DATA_ROOT.iterdir() if d.is_dir()]
    if not categories:
        print("数据根目录下没有任何子文件夹。")
        return

    print("=== 信息提取机 ===")
    print("可用知识库：")
    for i, cat in enumerate(categories, 1):
        print(f"{i}. {cat.name}")
    print("0. 全部")
    print("（也可以直接输入文件夹名称，如 '5' 或 'code'）")

    choice = input("请选择要检索的知识库编号/名称: ").strip()
    if choice == '0':
        selected_cats = categories
    else:
        parts = [p.strip() for p in choice.split(',')]
        selected_cats = []
        for part in parts:
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(categories):
                    selected_cats.append(categories[idx])
                else:
                    print(f"无效编号: {part}")
            else:
                matched = [cat for cat in categories if cat.name == part]
                if matched:
                    selected_cats.extend(matched)
                else:
                    print(f"未找到名为 {part} 的文件夹")
        if not selected_cats:
            print("未选择有效知识库。")
            return

    print("检索模式：")
    print("1. 标准模式（快速，无AI）")
    print("2. 增强模式（使用AI提取关键词+生成摘要）")
    mode = input("请选择模式（1/2）: ").strip()
    use_llm = (mode == '2')

    question = input("请输入您的问题: ").strip()
    if not question:
        print("问题不能为空。")
        return

    # 关键词提取
    if use_llm:
        print("正在使用AI提取关键词...")
        keywords = llm_extract_keywords(question)
    else:
        keywords = simple_keywords(question)
    print(f"关键词: {keywords}")

    # 检索文档
    all_matches = []
    for cat in selected_cats:
        index_dir = DATA_ROOT / f"{cat.name}_index"
        try:
            index = DocIndex(cat, index_dir)
            print(f"  索引 {cat.name} 中包含 {index.ix.doc_count()} 个文档")
            matches = index.search(keywords, limit=100)
            all_matches.extend(matches)
        except Exception as e:
            print(f"检索 {cat.name} 失败: {e}")

    # 系统信息（按需）
    system_info = collect_system_info(question) if SYSTEM_INFO_ENABLED else {}

    # 生成摘要
    print("生成摘要...")
    if use_llm:
        summary = llm_summary(question, all_matches)
    else:
        summary = simple_summary(question, all_matches)
    redacted_summary = redact_text(summary)

    # 构建报告（JSON中包含完整匹配数据，但TXT中不会出现）
    report = {
        "question": question,
        "keywords": keywords,
        "mode": "enhanced" if use_llm else "standard",
        "selected_categories": [str(cat) for cat in selected_cats],
        "summary": redacted_summary,
        "matches": all_matches,   # 完整数据，供后续程序使用
        "system_info": system_info,
        "timestamp": datetime.datetime.now().isoformat()
    }

    output_dir = input("请输入报告保存目录（直接回车默认 F:/reports）: ").strip()
    if not output_dir:
        output_dir = "F:/reports"
    save_report(report, output_dir)

    # 控制台只输出摘要，不输出任何匹配详情
    print("\n" + "="*50)
    print("【摘要】")
    print(redacted_summary)

if __name__ == "__main__":
    main()