import os
from tavily import TavilyClient
from langchain_core.tools import tool
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# 初始化Tavily客户端
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

@tool
def amazon_product_search(keyword: str, country: str = "us", num_results: int = 10) -> Dict:
    """
    在Amazon上搜索产品，返回产品列表信息。使用Tavily搜索Amazon结果。

    Args:
        keyword: 搜索关键词
        country: 国家代码，默认us（美国）
        num_results: 返回结果数量，默认10

    Returns:
        产品列表，包含ASIN、标题、价格、评论数、评分等信息
    """
    print(f"[工具调用] Tavily搜索Amazon产品: {keyword} (国家: {country})")

    if not TAVILY_API_KEY or not tavily_client:
        return {"error": "TAVILY_API_KEY not configured"}

    # 构造搜索query
    domain = "amazon.com" if country == "us" else f"amazon.{country}"
    search_query = f"site:{domain} {keyword} buy price reviews"

    try:
        # 调用Tavily搜索
        response = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            max_results=num_results
        )

        products = []
        results = response.get("results", [])

        # 从搜索结果提取产品信息
        for result in results:
            url = result.get("url", "")
            content = result.get("content", "")
            title = result.get("title", "")

            # 尝试从URL提取ASIN
            # Amazon URL格式: /dp/ASIN 或者 /gp/product/ASIN
            asin = ""
            if "/dp/" in url:
                asin = url.split("/dp/")[1].split("/")[0]
            elif "/gp/product/" in url:
                asin = url.split("/gp/product/")[1].split("/")[0]

            # 尝试从内容提取价格和评论
            import re
            price_match = re.search(r'\$?\s*(\d+\.\d+|\d+)', content)
            price = price_match.group(1) if price_match else ""

            # 多种模式匹配评论数 - 支持k/K千单位格式 (14.3k = 14300)
            reviews = 0
            reviews_patterns = [
                # 带千单位格式: 14.3k reviews, 2.5K ratings
                r'([\d\.]+)\s*([kK])\s+(reviews|review|ratings?)',
                r'([\d\.]+[kK])\s+(reviews|review|ratings?)',
                # 纯数字格式: 14300 reviews
                r'(\d+[,]*\d*)\s+(reviews|review)',
                r'(\d+[,]*\d*)\s+customer\s+reviews',
                r'(\d+[,]*\d*)\s+ratings?',
                r'(\d+[,]*\d*)\s+global ratings',
                r'(\d+[,]*\d*)\s+product ratings',
            ]
            for pattern in reviews_patterns:
                reviews_match = re.search(pattern, content.lower())
                if reviews_match:
                    if len(reviews_match.groups()) >= 2 and reviews_match.group(2) in ['k', 'K']:
                        num = float(reviews_match.group(1))
                        reviews = int(num * 1000)
                    elif reviews_match.group(1).lower().endswith('k'):
                        num = float(reviews_match.group(1)[:-1])
                        reviews = int(num * 1000)
                    else:
                        reviews_str = reviews_match.group(1).replace(",", "")
                        reviews = int(float(reviews_str))
                    break

            # 多种模式匹配评分
            rating = 0.0
            rating_patterns = [
                r'(\d\.\d+)\s*(out of|stars?)',
                r'(\d\.\d+)\s+out of 5',
                r'(\d\.\d+)\s+stars?',
                r'rating\s+is\s+(\d\.\d+)',
                r'rated\s+(\d\.\d+)\s+out',
            ]
            for pattern in rating_patterns:
                rating_match = re.search(pattern, content.lower())
                if rating_match:
                    rating = float(rating_match.group(1))
                    break

            product = {
                "title": title,
                "asin": asin,
                "price": price,
                "reviews": reviews,
                "rating": rating,
                "link": url,
                "content": content[:200]
            }
            products.append(product)

        # 过滤掉没有ASIN的结果
        products = [p for p in products if p["asin"]]
        print(f"[工具完成] 找到 {len(products)} 个带ASIN的产品")

        return {
            "keyword": keyword,
            "country": country,
            "products": products,
            "search_metadata": {"total_results": len(results)}
        }

    except Exception as e:
        print(f"[工具错误] {str(e)}")
        return {"error": str(e)}

@tool
def search_trends(keyword: str) -> Dict:
    """
    查询关键词的搜索趋势，判断需求稳定性。使用Tavily搜索趋势信息。

    Args:
        keyword: 关键词

    Returns:
        趋势数据，包含搜索热度变化和季节性分析
    """
    print(f"[工具调用] 查询搜索趋势: {keyword}")

    if not TAVILY_API_KEY or not tavily_client:
        return {"error": "TAVILY_API_KEY not configured"}

    search_query = f"{keyword} google trends search volume popularity analysis 2024 2025"

    try:
        response = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            max_results=5
        )

        results = response.get("results", [])
        trend_summary = []
        for res in results:
            trend_summary.append({
                "title": res.get("title"),
                "summary": res.get("content")[:300],
                "url": res.get("url")
            })

        print(f"[工具完成] 获取趋势数据成功，{len(trend_summary)} 条结果")
        return {
            "keyword": keyword,
            "trend_summary": trend_summary
        }
    except Exception as e:
        print(f"[工具错误] {str(e)}")
        return {"error": str(e)}

@tool
def get_competitor_analysis(asin: str, country: str = "us") -> Dict:
    """
    获取特定ASIN的竞争对手分析数据。通过Tavily搜索该ASIN的页面信息。

    Args:
        asin: Amazon ASIN码
        country: 国家代码

    Returns:
        竞争对手信息，包含卖家数量、价格分布等
    """
    print(f"[工具调用] 分析ASIN竞争对手: {asin}")

    if not TAVILY_API_KEY or not tavily_client:
        return {"error": "TAVILY_API_KEY not configured"}

    domain = "amazon.com" if country == "us" else f"amazon.{country}"
    url = f"https://www.{domain}/dp/{asin}"

    try:
        # 尝试使用Tavily提取页面内容
        response = tavily_client.extract(
            urls=[url]
        )

        # 修复：处理空results情况，避免index out of range
        results = response.get("results", [])
        content = ""
        if len(results) > 0:
            extracted = results[0]
            content = extracted.get("raw_content", "")

        # 如果extract失败（Amazon反爬），降级使用搜索获取信息
        if not content or content.strip() == "":
            print(f"[工具提示] Extract失败，降级使用搜索: {asin}")
            search_query = f"amazon {asin} price reviews rating"
            search_response = tavily_client.search(
                query=search_query,
                search_depth="advanced",
                max_results=3
            )
            # 合并所有搜索结果内容
            search_results = search_response.get("results", [])
            for res in search_results:
                content += " " + res.get("content", "")

        # 分析内容提取关键信息
        import re

        # 调试：保存提取到的内容方便排查问题
        if content:
            os.makedirs("data", exist_ok=True)
            with open(f"data/extracted_{asin}.txt", "w", encoding="utf-8") as f:
                f.write(content[:2000])

        # 找价格
        price_match = re.search(r'\$?\s*(\d+\.\d+|\d+)', content)
        current_price = price_match.group(1) if price_match else ""

        # 找评论数 - 支持k/K千单位格式 (14.3k = 14300)
        reviews = 0
        reviews_patterns = [
            # 带千单位格式: 14.3k reviews, 2.5K ratings
            r'([\d\.]+)\s*([kK])\s+(reviews|review|ratings?)',
            r'([\d\.]+[kK])\s+(reviews|review|ratings?)',
            # 纯数字格式: 14300 reviews
            r'(\d+[,]*\d*)\s+(reviews|review)',
            r'(\d+[,]*\d*)\s+customer\s+reviews',
            r'(\d+[,]*\d*)\s+ratings?',
            r'(\d+[,]*\d*)\s+global ratings',
        ]
        for pattern in reviews_patterns:
            reviews_match = re.search(pattern, content.lower())
            if reviews_match:
                if len(reviews_match.groups()) >= 2 and reviews_match.group(2) in ['k', 'K']:
                    # 14.3k -> 14300
                    num = float(reviews_match.group(1))
                    reviews = int(num * 1000)
                elif reviews_match.group(1).lower().endswith('k'):
                    # 14.3k -> 14300
                    num = float(reviews_match.group(1)[:-1])
                    reviews = int(num * 1000)
                else:
                    # 纯数字
                    reviews_str = reviews_match.group(1).replace(",", "")
                    reviews = int(float(reviews_str))
                break

        # 找评分 - 多种模式匹配
        rating = 0.0
        rating_patterns = [
            r'(\d\.\d+)\s+(out of 5|stars)',
            r'(\d\.\d+)\s+out of 5 stars',
            r'rated\s+(\d\.\d+)\s+out',
            r'rating:\s+(\d\.\d+)',
        ]
        for pattern in rating_patterns:
            rating_match = re.search(pattern, content.lower())
            if rating_match:
                rating = float(rating_match.group(1))
                break

        # 判断是否是Amazon自营
        is_amazon = "amazon.com" in content.lower() and "ships from and sold by amazon" in content.lower()

        print(f"[工具完成] 获取产品 {asin} 数据成功")
        return {
            "asin": asin,
            "url": url,
            "current_price": current_price,
            "reviews": reviews,
            "rating": rating,
            "is_amazon_sold": is_amazon,
            "page_content_summary": content[:500]
        }

    except Exception as e:
        print(f"[工具错误] {str(e)}")
        return {"error": str(e)}
