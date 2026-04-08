from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.agents.researcher import researcher_node
from src.agents.analyst import analyst_node
from src.agents.report_writer import report_writer_node
from src.prompts import SUPERVISOR_PROMPT
from src.config import get_llm, clean_text
from langchain_core.prompts import ChatPromptTemplate

def supervisor_node(state: AgentState) -> dict:
    """Supervisor节点：决定下一步该哪个Agent工作"""

    llm = get_llm()

    clean_prompt = clean_text(SUPERVISOR_PROMPT)
    prompt = ChatPromptTemplate.from_messages([
        ("system", clean_prompt),
        ("human", "当前已完成工作：\n- 研究员数据: {has_research}\n- 分析师分析: {has_analysis}\n- 报告撰写: {has_report}\n\n请决定下一步，只输出一个关键词。")
    ])

    has_research = "已完成" if state["research_data"] and state["research_data"].get("products_found", []) else "未完成"
    has_analysis = "已完成" if state["analysis_results"] and state["analysis_results"].get("recommended_products", []) else "未完成"
    has_report = "已完成" if state["final_report"] else "未完成"

    chain = prompt | llm
    response = chain.invoke({
        "has_research": has_research,
        "has_analysis": has_analysis,
        "has_report": has_report,
        "messages": state["messages"]
    })
    content = response.content.strip().lower()

    # 解析输出
    if "finish" in content:
        next_agent = END
    elif "researcher" in content:
        next_agent = "researcher"
    elif "analyst" in content:
        next_agent = "analyst"
    elif "report_writer" in content:
        next_agent = "report_writer"
    else:
        # 默认顺序执行
        if not state["research_data"] or not state["research_data"].get("products_found", []):
            next_agent = "researcher"
        elif not state["analysis_results"] or not state["analysis_results"].get("recommended_products", []):
            next_agent = "analyst"
        elif not state["final_report"]:
            next_agent = "report_writer"
        else:
            next_agent = END

    try:
        print(f"[Supervisor] 下一步: {next_agent if next_agent != END else 'FINISH'}")
    except:
        pass

    return {"next_agent": next_agent}

def build_supervisor_graph() -> StateGraph:
    """构建Supervisor协调的多Agent图"""

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("report_writer", report_writer_node)

    # 设置入口
    workflow.set_entry_point("supervisor")

    # 添加条件边
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_agent"]
    )

    # 每个Agent完成后回到Supervisor
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("analyst", "supervisor")
    workflow.add_edge("report_writer", "supervisor")

    # 编译
    return workflow.compile()
