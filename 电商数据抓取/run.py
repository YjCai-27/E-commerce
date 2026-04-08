# 必须放在最开头，先修编码问题
import json
import anthropic._utils._json

# 猴子补丁：过滤掉所有不能utf-8编码的字符
original_openapi_dumps = anthropic._utils._json.openapi_dumps

def fixed_openapi_dumps(obj):
    s = json.dumps(obj)
    return s.encode('utf-8', 'ignore').decode('utf-8')

anthropic._utils._json.openapi_dumps = fixed_openapi_dumps

# 现在可以正常导入
import streamlit as st
import asyncio
from src.state import AgentState
from src.supervisor import build_supervisor_graph
import os
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="Amazon选品AI助手",
    page_icon="📊",
    layout="wide"
)

# 标题
st.title("Amazon选品Multi-Agent助手")
st.markdown("由 LangGraph + 火山方舟 + Tavily 驱动的智能选品团队")

# 侧边栏配置检查
with st.sidebar:
    st.header("配置检查")
    from src.config import ANTHROPIC_API_KEY, TAVILY_API_KEY

    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your_openai_api_key_here":
        st.error("❌ API Key 未配置，请编辑 .env 文件")
    else:
        st.success("✅ 火山方舟API已配置")

    if not TAVILY_API_KEY or TAVILY_API_KEY == "your_tavily_api_key_here":
        st.error("❌ TAVILY_API_KEY 未配置，请编辑 .env 文件")
    else:
        st.success("✅ TavilyAPI已配置")

    st.markdown("---")
    st.markdown("**工作流程**")
    st.markdown("1. 研究员搜索Amazon数据")
    st.markdown("2. 分析师计算销量利润")
    st.markdown("3. 撰写PDF选品报告")

# 主内容区
col1, col2 = st.columns([2, 1])

with col1:
    default_query = "帮我找Amazon美国站上价格在20-50美元之间，竞争度低，需求稳定的户外品类利基产品"
    user_query = st.text_area("请输入你的选品需求", value=default_query, height=100)

with col2:
    st.markdown("**选品需求示例：**")
    st.info("""
    - 找20-50美元户外利基产品
    - 找厨房用品低竞争产品
    - 适合新手卖家的小产品
    - 高利润宠物用品推荐
    """)

# 运行按钮
if st.button("开始选品分析", type="primary", disabled=(not ANTHROPIC_API_KEY or not TAVILY_API_KEY)):

    # 创建进度展示区域
    progress_area = st.empty()
    log_area = st.expander("运行日志", expanded=True)
    log_text = []

    def add_log(msg):
        log_text.append(msg)
        log_area.code("\n".join(log_text))

    add_log("系统启动，构建多Agent图...")

    # 构建图
    graph = build_supervisor_graph()

    # 初始状态
    initial_state = AgentState(
        messages=[("user", user_query)],
        next_agent="supervisor",
        research_data={},
        analysis_results={},
        final_report=""
    )

    add_log("多Agent团队开始工作...")

    # 异步运行
    with st.spinner("AI团队正在工作中..."):
        result = asyncio.run(graph.ainvoke(initial_state))

    add_log("分析完成！")

    # 展示结果
    st.markdown("---")
    st.header("分析结果")

    final_report = result["final_report"]
    st.markdown(final_report)

    # 提供下载
    st.markdown("---")
    st.subheader("📥 下载报告")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 下载Markdown
    md_filename = f"{timestamp}_amazon_product_report.md"
    st.download_button(
        label="📄 下载 Markdown",
        data=final_report,
        file_name=md_filename,
        mime="text/markdown"
    )

    # 检查PDF是否存在
    pdf_path = result.get("final_report_pdf", "")
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_filename = os.path.basename(pdf_path)
        st.download_button(
            label="📕 下载 PDF",
            data=pdf_bytes,
            file_name=pdf_filename,
            mime="application/pdf"
        )

    st.success("🎉 选品分析完成！推荐产品已在上方展示，可以下载报告保存。")

# 页脚
st.markdown("---")
st.markdown("Powered by LangGraph + Claude Code")
