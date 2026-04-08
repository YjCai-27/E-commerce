#!/usr/bin/env python3
# THIS MUST BE AT THE VERY BEGINNING, before any other imports
# Patch Anthropic's json serialization to fix UnicodeEncodeError on Windows
import json
import anthropic._utils._json

# Recursively clean all strings to remove surrogate characters
def clean_obj(o):
    if isinstance(o, str):
        return o.encode('utf-8', 'ignore').decode('utf-8')
    elif isinstance(o, dict):
        return {clean_obj(k): clean_obj(v) for k, v in o.items()}
    elif isinstance(o, list):
        return [clean_obj(i) for i in o]
    else:
        return o

original_openapi_dumps = anthropic._utils._json.openapi_dumps

def fixed_openapi_dumps(obj):
    cleaned = clean_obj(obj)
    return json.dumps(cleaned)

anthropic._utils._json.openapi_dumps = fixed_openapi_dumps

# NOW it's safe to import everything else
import asyncio
import os
import sys
from dotenv import load_dotenv
from src.supervisor import build_supervisor_graph
from src.state import AgentState

# 设置输出编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

async def main():
    print("Amazon选品Multi-Agent系统启动中...")

    # 构建图
    graph = build_supervisor_graph()

    # 示例查询
    print("\n请输入您的选品需求（例如：帮我找Amazon上适合中小卖家的利基产品）:")
    user_query = input().strip() or "帮我找Amazon美国站上价格在20-50美元之间，竞争度低，需求稳定的户外品类利基产品"

    # 初始状态
    initial_state = AgentState(
        messages=[
            ("user", user_query.encode('utf-8', 'ignore').decode('utf-8'))
        ],
        next_agent="supervisor",
        research_data={},
        analysis_results={},
        final_report=""
    )

    print("\n多智能体团队开始工作，请稍候...\n")

    # 执行图
    result = await graph.ainvoke(initial_state)

    # 输出最终报告
    print("\n" + "="*80)
    print("最终选品报告")
    print("="*80)
    print(result["final_report"])

    print(f"\n任务完成！报告已保存到 reports/output/ 目录")

if __name__ == "__main__":
    asyncio.run(main())
