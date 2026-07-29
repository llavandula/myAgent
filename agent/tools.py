"""
工具模块 —— 所有 Agent 可用的工具都在这里定义。

新增工具只需要：
1. 写一个函数
2. 加上 @tool 装饰器
3. 把函数加入 ALL_TOOLS 列表即可
"""

import datetime
import locale
import re
import subprocess
import sys
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


# shell 命令执行工具（带白名单 + 黑名单）
# ---------- 白名单：只允许这些主命令执行 ----------
WHITELIST_COMMANDS = {
    # 文件浏览
    "dir", "ls", "type", "cat", "find", "where", "which",
    "echo", "cd", "pwd",
    # 网络
    "ping", "ipconfig", "ifconfig", "netstat", "curl", "wget",
    # 开发工具
    "git", "pip", "pip3", "npm", "npx", "yarn",
    "python", "python3", "node",
    # 系统信息
    "date", "time", "whoami", "hostname", "systeminfo", "uname",
    "df", "du", "free", "ps", "tasklist",
    # 进程
    "kill", "taskkill",
}

# ---------- 黑名单：参数中出现这些模式即拒绝 ----------
BLACKLIST_PATTERNS = [
    # 危险命令（PowerShell 与 CMD 混合）
    r'\brm\b\s*[-/][rf].+[/\\]',           # rm -rf /
    r'\bRemove-Item\b',                     # PowerShell 删除
    r'\brmdir\b\s+[/\\]?\s*s',              # rmdir /s
    r'\bdel\b\s+[/\\]?[fqs]',               # del /f /s /q
    r'\bformat\b',                           # 格式化
    r'\bshutdown\b',                         # 关机
    r'\brestart-computer\b',                 # PowerShell 重启
    r'\breg\s+delete\b',                     # 注册表删除
    r'\bdiskpart\b',                         # 磁盘分区
    r'\bdel\s+/f',                           # 删除只读文件

    # 危险的 shell 特性
    r'>\s*/dev/',                            # linux 重定向到设备
    r':\s*rm\b',                             # 冒号后的 rm
    r'\bexec\b',                             # exec 替换进程

    # 危险的标志位
    r'--no-verify',                          # git 跳过 hook
    r'--force',                              # 强制操作（部分保留 git push --force 的检查）
]


def _is_safe_command(command: str) -> tuple[bool, str]:
    """
    检查命令是否安全。
    返回: (is_safe, reason)
    """
    stripped = command.strip()
    if not stripped:
        return False, "命令为空"

    # 1. 提取主命令（第一个非空 token）
    #    考虑 Windows 下路径可能有空格（如 "C:\Program Files\..."），用 shlex 过于严格
    #    这里简单取第一个空格/制表符前的 token
    main_cmd = stripped.split()[0].lower()

    # 2. 白名单检查
    if main_cmd not in WHITELIST_COMMANDS:
        return False, f"命令 '{main_cmd}' 不在白名单中，拒绝执行"

    # 3. 黑名单检查
    for pattern in BLACKLIST_PATTERNS:
        if re.search(pattern, stripped, re.IGNORECASE):
            return False, f"命令包含危险操作（匹配: {pattern}），已拦截"

    return True, ""


def _get_system_encoding() -> str:
    """
    获取子进程输出的正确编码。
    - Windows: cmd.exe 使用 OEM 代码页（如 cp936 = GBK 简体中文）
    - Linux/macOS: 通常是 UTF-8
    """
    if sys.platform == "win32":
        try:
            import ctypes
            cp = ctypes.windll.kernel32.GetOEMCP()
            return f"cp{cp}"
        except Exception:
            return locale.getpreferredencoding() or "gbk"
    return locale.getpreferredencoding() or "utf-8"


@tool
def run_command(command: str) -> str:
    """在系统终端中执行一条命令，返回标准输出和错误输出。
    只能执行白名单中的安全命令（如 dir, ls, cd, type, git, ping 等），
    危险操作（如 rm -rf, shutdown, del /f 等）会被自动拦截。"""
    safe, reason = _is_safe_command(command)
    if not safe:
        return f"[拒绝执行] {reason}\n命令: {command}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding=_get_system_encoding(),
            errors='replace',
            timeout=60,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"[stderr]\n{result.stderr}"
        if not output:
            output = f"(命令执行完毕，无输出，返回码: {result.returncode})"
        return output.rstrip()
    except subprocess.TimeoutExpired:
        return f"[超时] 命令执行超过 60 秒，已终止: {command}"
    except Exception as e:
        return f"[执行出错] {e}"


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
    run_command,
    # web_search,      # 取消注释以启用
    # read_file,       # 取消注释以启用
]
