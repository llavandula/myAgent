"""
Agent 核心模块 —— 负责创建 LLM、组装 Agent、管理对话。

对外暴露两个核心接口：
- get_agent()  → 获取可复用的 agent 实例
- chat()       → 单轮 / 多轮对话（自动管理对话历史）
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config.settings import settings
from agent.tools import ALL_TOOLS
from agent.memory.buffer import BufferMemory
from agent.strategist.pipeline import ContextPipeline


def _build_llm() -> ChatOpenAI:
    """根据配置构建 LLM 实例。"""

    return ChatOpenAI(
        model=settings.MODEL_NAME,
        temperature=settings.TEMPERATURE,
        api_key=settings.api_key,
        base_url=settings.base_url,
        streaming=True,
    )


def get_agent():
    """
    获取一个配置好的 Agent 实例（无内置 checkpointer，由 pipeline 管理记忆）。

    返回:
        agent_graph: 编译好的 LangGraph agent

    用法:
        agent = get_agent()
        result = agent.invoke({"messages": [...]})
    """
    llm = _build_llm()

    agent_graph = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
    )

    return agent_graph


def create_pipeline() -> ContextPipeline:
    """创建上下文编排流水线，注册默认记忆策略。"""
    from config.settings import settings

    buffer = BufferMemory(
        max_turns=settings.MEMORY_MAX_TURNS,
        max_tokens=settings.MEMORY_MAX_TOKENS,
    )

    pipeline = ContextPipeline(strategies=[buffer])
    return pipeline


def chat(user_input: str, agent_graph=None) -> str:
    """
    发起一轮对话，返回 Agent 的最终回复。

    参数:
        user_input:   用户输入文本
        agent_graph:  (可选) 已创建的 agent graph，留空自动创建

    返回:
        Agent 的最终回复字符串
    """
    if agent_graph is None:
        agent_graph = get_agent()

    result = agent_graph.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
    )

    # 提取最后一条 AI 消息
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.type == "ai" and msg.content:
            return msg.content

    return "（Agent 没有返回内容）"
