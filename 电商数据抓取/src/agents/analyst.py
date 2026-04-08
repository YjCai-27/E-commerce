from src.state import AgentState
from src.prompts import ANALYST_PROMPT
from src.config import get_llm, clean_text
from langchain_core.prompts import ChatPromptTemplate
import json

def analyst_node(state: AgentState) -> dict:
    """分析师节点：分析研究员收集的数据，筛选优质产品"""

    print("[analyst] 开始分析数据...")

    llm = get_llm()
    research_data = state["research_data"]

    clean_prompt = clean_text(ANALYST_PROMPT)
    prompt = ChatPromptTemplate.from_messages([
        ("system", clean_prompt),
        ("human", "以下是研究员收集的原始数据，请按照给定公式进行分析：\n\n{research_data}")
    ])

    chain = prompt | llm
    response = chain.invoke({"research_data": json.dumps(research_data, ensure_ascii=False, indent=2)})

    # 尝试解析结果
    try:
        import re
        json_match = re.search(r'```json\n(.*?)\n```', response.content, re.DOTALL)
        if json_match:
            analysis_results = json.loads(json_match.group(1))
        else:
            analysis_results = {
                "analysis": response.content,
                "recommended_products": []
            }
    except Exception as e:
        analysis_results = {
            "analysis": response.content,
            "recommended_products": [],
            "error": str(e)
        }

    # 按总分排序
    if "recommended_products" in analysis_results and analysis_results["recommended_products"]:
        analysis_results["recommended_products"].sort(
            key=lambda x: x.get("total_score", 0),
            reverse=True
        )
        # 重新排名次
        for i, prod in enumerate(analysis_results["recommended_products"]):
            prod["rank"] = i + 1

    # 统计推荐数量
    rec_count = len(analysis_results.get("recommended_products", []))
    print(f"[analyst] 完成分析，推荐 {rec_count} 个产品")

    # 保存分析结果
    try:
        with open("data/analysis_results.json", "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[analyst] 保存分析结果失败: {e}")

    return {
        "analysis_results": analysis_results,
        "messages": [response]
    }
