"""
Agent 核心模块 —— 负责创建 LLM、组装 Agent、管理对话。

对外暴露两个核心接口：
- get_agent()  → 获取可复用的 agent 实例
- chat()       → 单轮 / 多轮对话（自动管理对话历史）
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

from config.settings import settings
from agent.tools import ALL_TOOLS


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
    获取一个配置好的 Agent 实例。

    返回:
        (agent_graph, checkpointer, thread_id)

    - agent_graph: 编译好的 LangGraph agent，调用 .invoke() 或 .stream() 执行
    - checkpointer: InMemorySaver，负责保存对话状态
    - thread_id: 对话线程 ID，同一线程保持上下文

    用法:
        agent, checkpointer, thread_id = get_agent()
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "你好"}]},
            config={"configurable": {"thread_id": thread_id}},
        )
    """
    llm = _build_llm()
    checkpointer = InMemorySaver()

    agent_graph = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        checkpointer=checkpointer,
    )

    thread_id = "default"
    return agent_graph, checkpointer, thread_id


def chat(user_input: str, agent_graph=None, thread_id: str = "default") -> str:
    """
    发起一轮对话，返回 Agent 的最终回复。

    参数:
        user_input:   用户输入文本
        agent_graph:  (可选) 已创建的 agent graph，留空自动创建
        thread_id:    对话线程 ID，同一 ID 保持多轮上下文

    返回:
        Agent 的最终回复字符串
    """
    if agent_graph is None:
        agent_graph, _, _ = get_agent()

    config = {"configurable": {"thread_id": thread_id}}
    result = agent_graph.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config,
    )

    # 提取最后一条 AI 消息
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.type == "ai" and msg.content:
            return msg.content

    return "（Agent 没有返回内容）"
