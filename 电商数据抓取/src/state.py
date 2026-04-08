from typing import TypedDict, Annotated, Sequence, Dict
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """多智能体系统的状态定义"""
    # 消息历史
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # 下一个要执行的Agent
    next_agent: str
    # 研究员收集的原始数据
    research_data: Dict
    # 分析师的分析结果
    analysis_results: Dict
    # 最终报告内容
    final_report: str
