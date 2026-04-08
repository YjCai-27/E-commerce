"""
修复Anthropic SDK的UTF-8编码问题
"""
import json
import anthropic._utils._json

original_openapi_dumps = anthropic._utils._json.openapi_dumps

def fixed_openapi_dumps(obj):
    # 先转换为字符串，过滤掉所有不能编码的字符
    s = json.dumps(obj)
    # 重新编码过滤掉surrogate
    return s.encode('utf-8', 'ignore').decode('utf-8')

# 替换
anthropic._utils._json.openapi_dumps = fixed_openapi_dumps
