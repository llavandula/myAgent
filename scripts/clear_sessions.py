"""
清理过期会话脚本。

用法：
    python scripts/clear_sessions.py --days 30   # 删除 30 天前的会话
    python scripts/clear_sessions.py --all        # 清空所有会话
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="清理过期会话")
    parser.add_argument("--days", type=int, default=30, help="保留最近 N 天的会话")
    parser.add_argument("--all", action="store_true", help="清空所有会话")
    args = parser.parse_args()

    # TODO: 调用 storage/db 实现
    print(f"[clear_sessions] 待实现: days={args.days}, all={args.all}")


if __name__ == "__main__":
    main()
