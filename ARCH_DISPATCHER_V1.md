# TG-Link-Dispatcher 体系架构与数据流设计 (v1.2)

**日期**: 2026-02-10
**状态**: 已实现 (Implemented - v0.8)
**核心目标**: 实现高可靠的消息处理流水线、Web 化运维及自动化测试保障。

---

## 1. 逻辑架构 (Logical Architecture)

系统采用分层架构设计，确保每一层职责单一，易于扩展及测试。

```mermaid
graph TD
    subgraph "管理层 (Management)"
        Web[FastAPI Web Panel] <--> JWT[JWT Auth]
        Web <--> Config[Pydantic Config Manager]
        Web <--> Monitor[Shared Monitor Service]
        Web <--> CLI[External Tools Integration (IPC)]
    end

    subgraph "采集层 (Ingestion)"
        TG[Telegram Server] -->|API| Client[Telethon Client]
        Dispatcher[Dispatcher Engine] -->|Sync Loop| Client
    end

    subgraph "处理层 (Processing Pipeline)"
        Dispatcher -->|Raw Message| Parser[Parser Service]
        Parser -->|Standard Model| Processor[Message Processor]
        Processor -->|Active Discovery| Metadata[Metadata Provider]
        Processor -->|Rule Cleaning| Cleaner[URL Cleaner]
    end

    subgraph "存储层 (Storage)"
        Processor -->|Validated Data| Exporter[Exporter Factory]
        Exporter -->|Write| CSV[CSV File with Header Protection]
    end
```

---

## 2. 数据处理流水线 (v1.2 Pipeline)

### 2.1 初始化与发现
1.  **动态配置加载**: 通过 Pydantic V2 校验 `config.yaml`，支持环境变量覆盖。
2.  **源自动发现**: `Dispatcher` 根据 `all` 标志或显式 ID 列表，动态获取扫描实体。

### 2.2 消息增强流程
1.  **标准化**: 原始消息通过 `app/parser.py` 转换为 `MessageData` 模型。
2. **元数据增强 (Active Metadata)**: 若 URL 存在，`MetadataProvider` 执行受控的异步抓取（3s 超时/缓存），同时完成：
    *   **标题补全**: 获取网页 `<title>`。
    *   **链接展开**: 解析短链（如 v.douyin.com）获取最终长链接，并再次通过 `Cleaner` 清洗追踪参数。
3.  **清洗**: `URLCleaner` 应用正则与规则集，剔除 X/Twitter/WeChat 的追踪参数。

### 2.3 智能路由与查重
1.  **关键词匹配**: 支持分任务进行内容过滤。
2.  **文件级查重**: `Exporter` 在写入前检查目标文件内是否已存在该 URL。
3.  **表头保护**: 自动识别现有 CSV 文件的列顺序，确保新旧数据完美对齐。

---

## 3. 系统职责矩阵

| 模块 | 职责 | 实现技术 |
| :--- | :--- | :--- |
| `app/models.py` | 全局数据骨架 (SSOT) | Pydantic V2 |
| `app/processor.py`| 业务逻辑流、插件化扩展 | Python class |
| `app/web.py` | 管理后台、API、JWT 安全 | FastAPI / jose |
| `app/metadata.py` | 异步网页元数据抓取 | aiohttp / BeautifulSoup4 |
| `app/exporter.py` | 安全的文件持久化 | Python standard CSV |
| `tests/` | 全栈自动化校验 | Pytest / Pytest-asyncio |

---

## 4. 关键设计哲学
- **Fail-Fast**: 启动时严格校验环境与配置。
- **Non-blocking**: 所有外部网络请求（Telegram, HTTP 抓取）均采用异步模式。
- **Visibility**: 任何查重跳过、配置重载操作均有实时日志可查。
