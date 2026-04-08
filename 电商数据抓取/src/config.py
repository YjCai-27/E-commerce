import os
import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

# 全局过滤：移除所有会导致编码错误的surrogate字符
def clean_text(text):
    return text.encode('utf-8', 'ignore').decode('utf-8')

# 预清理环境变量
load_dotenv()

# 火山方舟Anthropic配置
ANTHROPIC_API_KEY = clean_text(os.getenv("OPENAI_API_KEY", ""))
ANTHROPIC_BASE_URL = clean_text(os.getenv("OPENAI_BASE_URL", ""))
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MODEL_NAME = clean_text(os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022"))

# 全局LLM实例 - 火山方舟Claude
llm = ChatAnthropic(
    model=MODEL_NAME,
    temperature=0,
    base_url=ANTHROPIC_BASE_URL,
    api_key=ANTHROPIC_API_KEY
)

def get_llm():
    """获取全局LLM实例"""
    return llm
