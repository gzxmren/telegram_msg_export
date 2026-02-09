# TG-Link-Dispatcher 设计文档

## 1. 项目概述
本项目已从简单的 CSV 导出工具演进为**智能消息分拣系统**。最新的 v0.6 版本引入了深度重构的工程化架构，增强了系统的可维护性与扩展性。

## 2. 核心架构 (v0.6)

### 模块化协作流 (Orchestrator Pattern)
```mermaid
[main_dispatcher.py] (入口)
       │
       ▼
[Dispatcher] (总指挥) 
       │
       ├─> [CheckpointManager] (进度持久化)
       ├─> [ExporterFactory] (导出器生成器)
       │         └─> [CSVExporter / TXTExporter] (策略模式)
       │
       └─> [Message Processing Pipeline]
                 ├─> [Parser] (协议解析)
                 └─> [Cleaner] (URL提取与标准化)
```

## 3. 关键机制实现

### 3.1 抽象导出层
利用 **Abstract Base Class (ABC)** 定义导出器接口，强制实现 `write()` 和 `is_duplicate()`。通过 `ExporterFactory` 实现导出格式的动态决定，方便未来增加存储后端（如数据库）。

### 3.2 智能去重策略
1.  **加载阶段**: `Exporter` 在 `open()` 时自动加载文件中的现有 URL。
2.  **验证阶段**: `Dispatcher` 在写入前调用 `exporter.is_duplicate()`。
3.  **结果**: 确保即使跨账号、跨群组采集，同一个清洗后的规范化 URL 只会存储一次。

## 4. 版本迭代历史
*   **v0.4**: 重构 Dispatcher，支持多源采集与关键词路由。
*   **v0.5**: 引入 JSON 检查点增量机制与 Daemon 守护模式。
*   **v0.6**: **深度架构重构**。引入设计模式（Factory, Strategy, ABC），实现 URL 标准化清洗与智能去重。