"""
工具模块 —— 所有 Agent 可用的工具都在这里定义。

新增工具只需要：
1. 写一个函数
2. 加上 @tool 装饰器
3. 把函数加入 ALL_TOOLS 列表即可
"""

import datetime
from langchain_core.tools import tool


# ============================================================
# 内置工具
# ============================================================

@tool
def get_current_time() -> str:
    """获取当前日期和时间，格式为 YYYY-MM-DD HH:MM:SS。当需要知道当前时刻时使用。"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculator(expression: str) -> str:
    """执行数学计算。输入一个数学表达式字符串（如 '2+3*4' 或 'sqrt(16)'），返回计算结果。"""
    import math

    allowed = {
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
        "pow": math.pow, "abs": abs, "round": round,
        "pi": math.pi, "e": math.e,
    }
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算出错: {e}"


# ============================================================
# ⬇ 在这里添加你的自定义工具 ⬇
# ============================================================

# 示例：一个联网搜索工具（需要后续安装 tavily 等插件）
# @tool
# def web_search(query: str) -> str:
#     """在互联网上搜索信息。"""
#     # TODO: 接入搜索 API
#     return f"搜索结果（示例）: {query}"


# 示例：一个文件读取工具
# @tool
# def read_file(filepath: str) -> str:
#     """读取本地文件内容。"""
#     try:
#         with open(filepath, "r", encoding="utf-8") as f:
#             return f.read()
#     except Exception as e:
#         return f"读取失败: {e}"


# ============================================================
# 工具注册表 —— 新增工具后在这里加入即可
# ============================================================

ALL_TOOLS = [
    get_current_time,
    calculator,
    # web_search,      # 取消注释以启用
    # read_file,       # 取消注释以启用
]
