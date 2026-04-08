from src.state import AgentState
from src.prompts import RESEARCHER_PROMPT
from src.tools.search import search_trends, amazon_product_search, get_competitor_analysis
from src.config import get_llm, clean_text
from langgraph.prebuilt import create_react_agent
import json

# 研究员可用工具
researcher_tools = [
    amazon_product_search,
    search_trends,
    get_competitor_analysis
]

def researcher_node(state: AgentState) -> dict:
    """研究员节点：搜索收集Amazon产品数据"""

    print("[researcher] 开始收集数据...")

    llm = get_llm()

    # 创建ReAct Agent，清理prompt解决编码问题
    clean_prompt = clean_text(RESEARCHER_PROMPT)
    agent = create_react_agent(llm, researcher_tools, prompt=clean_prompt)

    # 执行
    result = agent.invoke(state)

    # 提取最后一条消息作为研究结果
    last_message = result["messages"][-1]

    # 尝试解析JSON数据
    try:
        # 尝试从输出中提取JSON
        import re
        json_match = re.search(r'```json\n(.*?)\n```', last_message.content, re.DOTALL)
        if json_match:
            research_data = json.loads(json_match.group(1))
        else:
            research_data = {
                "raw_data": last_message.content,
                "products_found": []
            }
    except Exception as e:
        research_data = {
            "raw_data": last_message.content,
            "products_found": [],
            "error": str(e)
        }

    print(f"[researcher] 完成数据收集，找到 {len(research_data.get('products_found', []))} 个产品")

    # 保存原始数据到data目录
    try:
        with open("data/research_data.json", "w", encoding="utf-8") as f:
            json.dump(research_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[researcher] 保存数据失败: {e}")

    return {
        "research_data": research_data,
        "messages": result["messages"]
    }
