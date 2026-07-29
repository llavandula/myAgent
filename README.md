## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key

# 3. 启动
python server.py
```

浏览器打开 **http://localhost:8000**

---

## 项目架构

### 完整目录结构

```
├── agent/                          # Agent 核心包
│   ├── __init__.py
│   ├── core.py                     # LLM 构建、Agent 实例化
│   ├── graph.py                    # LangGraph 图定义（节点、边、条件路由）
│   ├── state.py                    # Agent 的 State 定义 (TypedDict / Pydantic)
│   ├── tools.py                    # 工具定义
│   │
│   ├── memory/                     # ── 记忆层 ──
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseMemory 抽象接口
│   │   ├── buffer.py               # 滑动窗口 / TokenBudget 策略
│   │   ├── summary.py              # 摘要记忆策略
│   │   ├── entity.py               # 实体记忆提取
│   │   └── hybrid.py               # 混合记忆（组合以上策略）
│   │
│   ├── retrieval/                  # ── 检索层（RAG） ──
│   │   ├── __init__.py
│   │   ├── vectorstore.py          # 向量库封装 (Chroma / FAISS)
│   │   ├── embedder.py             # Embedding 模型（文本 → 向量）
│   │   ├── retriever.py            # 检索器（query → top-K 文档）
│   │   └── indexer.py              # 索引构建 / 更新
│   │
│   ├── knowledge/                  # ── 知识库层（文档加载） ──
│   │   ├── __init__.py
│   │   ├── loader.py               # 文档加载 (PDF / MD / TXT / Web)
│   │   ├── splitter.py             # 文本分割 (RecursiveCharacterTextSplitter)
│   │   └── store.py                # 知识库管理（CRUD）
│   │
│   ├── strategist/                 # ── 策略编排层 ──
│   │   ├── __init__.py
│   │   ├── base.py                 # ContextStrategy 抽象接口
│   │   ├── selector.py             # 上下文选择器（含 Token Budget 预算裁剪）
│   │   ├── compressor.py           # 上下文压缩器
│   │   └── pipeline.py             # 编排流水线（组合多种策略）
│   │
│   └── schemas.py                  # 共享 Pydantic 模型
│
├── api/                            # ── API 层 ──
│   ├── __init__.py
│   ├── routes.py                   # FastAPI 路由
│   ├── schemas.py                  # 请求 / 响应 DTO
│   └── dependencies.py             # 依赖注入（获取 session agent）
│
├── storage/                        # ── 持久化层 ──
│   ├── __init__.py
│   ├── db.py                       # 数据库连接 (SQLite / Postgres)
│   ├── models.py                   # SQLAlchemy ORM 模型
│   └── migrations/                 # Alembic 数据库迁移
│       ├── alembic.ini
│       └── versions/
│
├── config/
│   ├── __init__.py
│   └── settings.py                 # 全局配置（包含 memory / rag / vector 等新增配置项）
│
├── scripts/                        # 工具脚本
│   ├── seed_knowledge.py           # 初始化 / 更新知识库
│   └── clear_sessions.py           # 清理过期会话
│
├── static/
│   └── index.html                  # 前端聊天界面
│
├── main.py                         # CLI 入口
├── server.py                       # Server 入口
├── requirements.txt
├── .env
├── .env.example
└── README.md
```

---

### 各层职责拆分明细

| 层 | 目录 | 职责 | 依赖 |
|---|---|---|---|
| **核心层** | `agent/` | LLM 构建、工具注册、LangGraph 图定义与状态管理 | LangChain, LangGraph |
| **记忆层** | `agent/memory/` | 各种记忆策略（滑动窗口、摘要记忆、实体记忆、混合记忆） | `agent/state.py`, `storage/` |
| **检索层** | `agent/retrieval/` | 文本向量化、索引构建、语义检索 | 向量库 (Chroma/FAISS), Embedding 模型 |
| **知识层** | `agent/knowledge/` | 文档加载、文本分割、知识入库管理 | `agent/retrieval/` |
| **策略层** | `agent/strategist/` | 上下文构建与编排：选择、压缩、Token 预算管理 | 上述所有子模块 |
| **API 层** | `api/` | HTTP 路由、请求校验、Session 管理、SSE 流式组装 | `agent/`, FastAPI |
| **持久化层** | `storage/` | 数据落盘（消息、摘要、向量、会话状态） | SQLite / Postgres |
| **配置层** | `config/` | 全局参数（模型、记忆策略、向量库连接等） | `python-dotenv` |

---

### 模块间数据流

```
用户输入（Web / CLI）
       │
       ▼
┌─────────────────────────────────────┐
│          api/routes.py              │  ← 接收请求、校验参数、管理 Session
│    Server-Sent Events (SSE) 流式     │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   agent/strategist/pipeline.py      │  ← 上下文编排流水线
│                                     │
│   1. memory/buffer.py               │  取最近 N 轮全文
│   2. memory/summary.py              │  取摘要（如已生成）
│   3. retrieval/retriever.py         │  语义检索相关历史
│   4. selector.py                    │  Token Budget 裁剪与合并
│                                     │
│   ──→ 输出: 组装好的 Context 包 ──→  │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│        agent/graph.py               │  ← LangGraph 图执行
│                                     │
│   ┌──────────┐   ┌──────────┐       │
│   │prep_ctxt │   │  agent   │       │  注：prep_ctxt 注入上下文
│   │  node    │──→│  node    │──┐    │  到 messages，agent 调用 LLM
│   └──────────┘   └──────────┘  │    │
│                                │    │
│                  ┌──────────┐  │    │
│                  │  tools   │←─┘    │  tool_call 时路由到工具节点
│                  │  node    │──┐    │
│                  └──────────┘  │    │
│                                ▼    │
│                  ┌──────────┐       │
│                  │memorize  │       │  归档本轮、更新摘要/Embedding
│                  │  node    │       │
│                  └──────────┘       │
└─────────────┬───────────────────────┘
              │
              ├──→ SSE 事件流 → 前端渲染
              │
              ▼
┌─────────────────────────────────────┐
│         storage/db.py               │  ← 数据落地
│                                     │
│   ┌──────────┐  ┌──────────┐        │
│   │ messages │  │summaries │        │  全量消息
│   │  (消息)   │  │ (摘要)   │        │  对话摘要
│   └──────────┘  └──────────┘        │
│   ┌──────────┐  ┌──────────┐        │
│   │ vectors  │  │knowledge │        │  Embedding 向量
│   │ (向量)   │  │ (知识库)  │        │  上传的文档知识
│   └──────────┘  └──────────┘        │
└─────────────────────────────────────┘
```

### 数据流分步说明

| 步骤 | 模块 | 做什么 |
|------|------|--------|
| ① | `api/routes.py` | 收到用户消息，解析 Session ID，从 `storage/db.py` 加载历史状态 |
| ② | `strategist/pipeline.py` | 编排各策略源（Buffer / Summary / Retriever），产出一个 **Context 包**，并执行 Token Budget 控制 |
| ③ | `graph.py` — `prep_ctxt` node | 将 Context 包注入到 Agent State 的 messages 中 |
| ④ | `graph.py` — `agent` node | LLM 根据完整上下文生成回复（可能触发 tool_call） |
| ⑤ | `graph.py` — `tools` node | 执行工具调用，将结果写回 State |
| ⑥ | `graph.py` — `memorize` node | 将本轮对话写入 `storage/db.py`，更新摘要（如触发阈值），更新向量索引 |
| ⑦ | `api/routes.py` | 将 LLM 输出以 SSE 流式推送到前端 |

---






