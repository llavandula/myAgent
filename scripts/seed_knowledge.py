"""
知识库初始化脚本 —— 将本地文档批量加载到向量库。

用法：
    python scripts/seed_knowledge.py --dir ./docs
    python scripts/seed_knowledge.py --file ./readme.md
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="加载文档到知识库")
    parser.add_argument("--dir", help="目录路径，批量加载该目录下所有文档")
    parser.add_argument("--file", help="单个文件路径")
    args = parser.parse_args()

    # TODO: 调用 knowledge/loader + indexer 实现
    print(f"[seed_knowledge] 待实现: dir={args.dir}, file={args.file}")


if __name__ == "__main__":
    main()
