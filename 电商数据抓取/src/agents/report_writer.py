from src.state import AgentState
from src.prompts import REPORT_WRITER_PROMPT
from src.config import get_llm, clean_text
from langchain_core.prompts import ChatPromptTemplate
from src.tools.pdf_generator import generate_pdf_report
import json
import os
from datetime import datetime

def report_writer_node(state: AgentState) -> dict:
    """报告撰写员节点：生成最终PDF报告"""

    print("[report_writer] 开始生成报告...")

    llm = get_llm()
    analysis_results = state["analysis_results"]
    research_data = state["research_data"]

    clean_prompt = clean_text(REPORT_WRITER_PROMPT)
    prompt = ChatPromptTemplate.from_messages([
        ("system", clean_prompt),
        ("human", """原始研究数据：
{research_data}

分析结果：
{analysis_results}

请按照要求结构撰写完整的选品报告。""")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "research_data": json.dumps(research_data, ensure_ascii=False, indent=2),
        "analysis_results": json.dumps(analysis_results, ensure_ascii=False, indent=2)
    })

    report_content = response.content

    # 生成PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"reports/output/{timestamp}_amazon_product_report.pdf"

    try:
        pdf_path = generate_pdf_report(report_content, output_path)
        print(f"[report_writer] PDF报告已生成: {pdf_path}")
    except Exception as e:
        print(f"[report_writer] PDF生成失败: {e}")
        pdf_path = ""

    # 保存文本版本
    try:
        txt_path = f"reports/output/{timestamp}_amazon_product_report.md"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"[report_writer] Markdown报告已保存: {txt_path}")
    except Exception as e:
        print(f"[report_writer] 保存Markdown报告失败: {e}")

    print("[report_writer] 报告撰写完成")

    return {
        "final_report": report_content,
        "final_report_pdf": pdf_path,
        "messages": [response]
    }
