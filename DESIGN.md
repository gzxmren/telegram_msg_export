# Telegram 群消息导出工具 (TG-Exporter) 设计文档

## 1. 项目概述
本项目旨在开发一个轻量级、模块化的 Python 工具，用于批量导出 Telegram 群组的历史消息。
**v0.3.1 更新**: 引入增量更新机制与命令行参数支持。

## 2. 技术栈选型
*   **核心协议**: Telethon (MTProto)
*   **配置**: python-dotenv + **argparse**
*   **存储**: Native CSV (UTF-8-SIG, Append Mode)

## 3. 核心架构设计

### 逻辑数据流
```mermaid
[CLI Args] --覆盖--> [配置加载 (.env)] 
       ↓
[客户端连接 (Telethon)]
       ↓
[增量检查 (Exporter)] ---> (读取现有 CSV max_id)
       ↓
[消息迭代器] <--- (reverse=True, min_id=max_id)
       ↓
[解析器] ---> [导出器 (Append Mode)]
```

### 关键策略变更 (v0.3.1)

#### 1. 存储策略 (Storage Strategy)
*   **以前 (v0.2)**: 覆盖写模式 (`w`)，顺序为“从新到旧”。
*   **现在 (v0.3.1)**: 追加写模式 (`a`)，顺序为**“从旧到新” (Chronological)**。
    *   *理由*: 追加模式对于日志型数据（聊天记录）最高效，且能无缝支持增量更新。

#### 2. 配置优先级
1.  命令行参数 (Highest Priority)
2.  环境变量 (`.env`)
3.  代码默认值

---

## 4. 模块职责更新

*   **`main.py`**: 集成 `argparse`，处理“全量 vs 增量”的决策逻辑。
*   **`app/exporter.py`**: 新增 `get_last_id()` 扫描文件断点；支持 `mode='a'` 追加写入。
*   **`app/config.py`**: 新增 `FORCE_FULL_FETCH` 开关。

---

## 5. 版本迭代历史
*   **v0.1 MVP**: 连通性验证。
*   **v0.2 Core**: 基础 CSV 导出。
*   **v0.3 Stable**: 流式写入与抗限流。
*   **v0.3.1 Advanced**: 增量更新与 CLI 支持。