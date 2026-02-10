# TG-Link-Dispatcher 设计文档

## 1. 项目概述
本项目已从简单的 CSV 导出工具演进为**生产级智能消息分拣系统**。最新的 v0.8 版本引入了模块化领域驱动设计 (DDD 启发)，并集成了可视化控制面板与自动化测试框架。

## 2. 核心架构 (v0.8)

### 模块化协作流 (Layered Architecture)
```mermaid
[main_dispatcher.py] (入口)
       │
       ▼
 [Web Panel] (FastAPI) <───> [Monitor] (状态中心)
       │                        ▲
       ▼                        │
 [Dispatcher] (总指挥/编排) ──────┘
       │
       ├─> [CheckpointManager] (进度持久化)
       ├─> [ExporterFactory] (导出器生成器)
       │
       └─> [Message Processor Pipeline] (处理流水线)
                 ├─> [Parser] (基础协议解析)
                 ├─> [Metadata Provider] (标题发现增强)
                 └─> [Cleaner] (URL提取与标准化)
```

## 3. 关键机制实现

### 3.1 领域模型 (Models)
引入 `MessageData` Pydantic 模型作为系统的“单一事实来源”。所有层（解析、处理、导出）均基于此模型交互，确保了字段的一致性，彻底解决了旧版本中 CSV 列位移的问题。

### 3.2 消息增强流 (Enhancement Pipeline)
在 `app/processor.py` 中实现了独立的处理流。目前的阶段包括：
1.  **解析**: 将原始 Telegram 对象转换为模型。
2.  **增强**: `MetadataProvider` 介入，通过分级策略（原生预览 -> 异步抓取）填充网页标题。
3.  **匹配**: 基于关键词进行任务分发。
4.  **路由**: 导向对应文件的 `Exporter`。

### 3.3 可视化监控与热重载
基于 FastAPI 与 JWT 实现了安全管理后台：
- **实时监控**: 通过单例 `Monitor` 收集全局指标。
- **配置编辑**: 在线修改 `config.yaml` 后，`Dispatcher` 会在下个周期通过 `Config.load()` 自动检测并动态重载，无需重启程序。

### 3.4 工具链集成 (Tooling & CLI)
为了解决 SQLite 单一写锁 (`database is locked`) 的问题，v0.8.1引入了 **混合架构 (Hybrid Architecture)**：
- **CLI 工具 (如 `list_chats.py`)** 优先尝试连接本地 Web API (`/api/chats`) 获取数据。
- 仅当主程序未运行时，工具才降级为直接读取 Session 文件模式。
- 这种设计确保了运维操作（如查询群组列表）**无需停止核心采集服务**。

## 4. 版本迭代历史
*   **v0.6**: 架构解耦重构，引入设计模式（Factory, Strategy, ABC）。
*   **v0.7**: 引入 Pydantic 模型、智能网页标题发现 (Title Discovery)。
*   **v0.8**: **全面重构与 Web 发布**。引入领域模型、Web 控制面板、自动化测试框架、修复 Pydantic V2 兼容性。

## 5. 质量保障 (QA)
- **单元测试**: 对 Cleaner、Config、Metadata 等模块进行全覆盖测试。
- **集成测试**: 模拟 Web API 交互，确保安全逻辑。
- **性能优化**: 标题抓取带 3s 超时与 LRU 缓存，避免阻塞主循环。