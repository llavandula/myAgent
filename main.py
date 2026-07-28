"""
Agent 对话入口 —— 启动后即可在终端与 Agent 进行多轮对话。

使用方法:
    python main.py

命令:
  exit / quit  → 退出
  reset        → 开始新对话
  tools        → 查看可用工具
"""

from colorama import init, Fore, Style

from agent.core import get_agent

init(autoreset=True)InMemorySaver


def print_banner():
    """打印欢迎横幅。"""
    print()
    print(Fore.CYAN + "=" * 56)
    print(Fore.CYAN + "  🧠  LangChain Agent 对话系统")
    print(Fore.CYAN + "=" * 56)
    print(Fore.WHITE + "  输入内容即可对话")
    print(Fore.WHITE + "  exit / quit  → 退出")
    print(Fore.WHITE + "  reset       → 开始新对话")
    print(Fore.WHITE + "  tools       → 查看可用工具")
    print(Fore.CYAN + "=" * 56)
    print()


def show_tools():
    """显示当前已注册的工具列表。"""
    from agent.tools import ALL_TOOLS

    print(Fore.YELLOW + f"\n📦 已注册 {len(ALL_TOOLS)} 个工具:")
    for t in ALL_TOOLS:
        desc = t.description.split("\n")[0][:60]
        print(Fore.WHITE + f"   • {t.name}: {desc}")
    print()


def reload_agent():
    """重新创建 agent（重置对话记忆）。"""
    agent, checkpointer, thread_id = get_agent()
    return agent, thread_id


def main():
    print_banner()
    agent, thread_id = reload_agent()

    while True:
        try:
            user_input = input(Fore.GREEN + "\n你: " + Style.RESET_ALL).strip()
        except (EOFError, KeyboardInterrupt):
            print(Fore.YELLOW + "\n\n👋 再见！")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print(Fore.YELLOW + "\n👋 再见！")
            break

        if user_input.lower() == "reset":
            agent, thread_id = reload_agent()
            print(Fore.YELLOW + "\n🔄 对话已重置，开始新会话！")
            continue

        if user_input.lower() == "tools":
            show_tools()
            continue

        # --- 调用 Agent（stream 模式，展示工具调用过程）---
        config = {"configurable": {"thread_id": thread_id}}
        try:
            stream_input = {"messages": [{"role": "user", "content": user_input}]}

            for event in agent.stream(stream_input, config=config, stream_mode="messages"):
                if not event:
                    continue

                message, metadata = event
                node = metadata.get("langgraph_node", "")

                if node == "agent":
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            tool_name = tc.get("name") or ""
                            # 跳过流式增量 chunk 中没有名字的空壳 tool_call
                            if not tool_name:
                                continue
                            tool_args = tc.get("args", {})
                            print(Fore.BLUE + f"\n  🔧 调用工具: {tool_name}")
                            if tool_args:
                                args_str = ", ".join(
                                    f"{k}={repr(v)}" for k, v in tool_args.items()
                                )
                                print(Fore.BLUE + f"     参数: {args_str}")

                elif node == "tools":
                    tool_name = message.name if hasattr(message, "name") else "unknown"
                    content = message.content if hasattr(message, "content") else str(message)
                    content_preview = content[:200] + "..." if len(str(content)) > 200 else content
                    print(Fore.YELLOW + f"  📋 {tool_name} 返回: {content_preview}")

            # --- 提取 AI 最终回复 ---
            final_state = agent.get_state(config)
            if final_state and final_state.values:
                messages = final_state.values.get("messages", [])
                for msg in reversed(messages):
                    if (hasattr(msg, "content") and msg.content
                            and msg.type == "ai"
                            and not (hasattr(msg, "tool_calls") and msg.tool_calls)):
                        print(Fore.WHITE + "\nAgent: " + msg.content)
                        break

            print()

        except Exception as e:
            print(Fore.RED + f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
