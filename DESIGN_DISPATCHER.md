# TG-Link-Dispatcher 设计文档 (v1.0)

**日期**: 2026-02-12
**状态**: 正式设计 (Approved)
**目标**: 构建一个基于配置驱动的、多源多目标的 Telegram 消息路由引擎。

---

## 1. 项目概述 (Overview)
TG-Link-Dispatcher 是一个多源、多规则的消息路由系统。它监听指定的 Telegram 群组，根据用户定义的规则（关键词/域名）对消息进行筛选，并将命中的消息分发到不同的本地文件中。

**核心哲学**:
*   **配置驱动**: 一切路由逻辑通过 `config.yaml` 定义，无需修改代码。
*   **任务导向**: 系统由多个独立的 Task 组成，每个 Task 负责特定的“来源 -> 筛选 -> 存储”流程。
*   **热插拔**: 支持灵活地插入或移除路由规则。

---

## 2. 逻辑架构 (Logical Architecture)

系统划分为四个核心层级：

```mermaid
graph TD
    subgraph "配置层 (Configuration)"
        Config[config.yaml] -->|加载| TaskManager[任务管理器]
    end

    subgraph "采集层 (Ingestion)"
        TG[Telegram Server] -->|API| Client[Telegram Client]
        TaskManager -->|订阅源列表| Client
    end

    subgraph "路由层 (Routing Core)"
        Client -->|原始消息| Router[路由分发器]
        TaskManager -->|分发规则| Router
        Router -->|匹配成功| Handler[消息处理器]
    end

    subgraph "存储层 (Storage)"
        Handler -->|写入| AdapterA[CSV Adapter (Topic A)]
        Handler -->|写入| AdapterB[CSV Adapter (Topic B)]
        Handler -->|写入| AdapterC[TXT Adapter (Topic C)]
    end
```

---

## 3. 数据流程 (Data Flow)

1.  **配置加载 (Load Phase)**:
    *   程序启动，读取 `config.yaml`。
    *   解析 Task 列表，提取所有需要监听的 Source Channel IDs。

2.  **消息采集 (Ingestion Phase)**:
    *   Client 遍历目标 Channel。
    *   基于 `min_id` 进行增量拉取。

3.  **路由匹配 (Routing Phase)**:
    *   对每一条消息，遍历所有启用的 Task。
    *   **匹配逻辑**:
        1.  `Source Check`: 消息来源是否在 Task 的 `sources` 列表中？
        2.  `Keyword Check`: 消息文本是否包含 Task 定义的 `keywords`？
    *   支持 **1:N 分发**: 一条消息可同时命中多个 Task。

4.  **持久化 (Persistence Phase)**:
    *   将命中的消息路由至 Task 指定的 `output_file`。
    *   支持 CSV (完整元数据) 和 TXT (纯链接) 格式。
    *   更新 Checkpoint。

---

## 4. 配置文件设计 (Configuration)

这是系统的核心控制面。

```yaml
# config.yaml

settings:
  session_name: "tg_dispatcher"
  loop_interval: 300   # 轮询间隔(秒)
  log_level: "INFO"

# 任务列表：定义从哪里抓(sources)，匹配什么(keywords)，存到哪里(output)
tasks:
  # 任务 1: 推特链接收集
  - name: "Twitter_Feed"
    enable: true
    sources: [-10012345678, -10087654321]  # 监听群组 ID
    keywords: ["twitter.com", "x.com"]     # 关键词匹配
    output:
      path: "./data/social/twitter_links.csv"
      format: "csv"

  # 任务 2: 微信文章存档
  - name: "WeChat_Articles"
    enable: true
    sources: [-10055566677]
    keywords: ["mp.weixin.qq.com"]
    output:
      path: "./data/read_later/wechat.txt"
      format: "txt"

  # 任务 3: 全局抖音视频监控 (监听所有群)
  - name: "Douyin_Videos"
    enable: true
    sources: ["all"]  # 特殊标识，监听所有已加入群组
    keywords: ["douyin.com", "v.douyin.com"]
    output:
      path: "./data/videos/douyin.csv"
      format: "csv"
```

---

## 5. 关键功能实现方案

### A. 运行模式
通过命令行参数控制：
*   **手动模式 (默认)**: `python main.py --run-once`
    *   执行一次全量轮询后退出。
*   **后台守护模式**: `python main.py --daemon`
    *   启动无限循环，每隔 `loop_interval` 秒执行一次轮询。

### B. 存储适配器
*   **CSV 模式**:
    *   表头: `fetched_at`, `msg_date`, `chat_id`, `sender`, `url`, `content`
    *   编码: UTF-8-SIG (Excel 友好)
*   **TXT 模式**:
    *   格式: 仅存储提取到的 URL，或 `[时间] URL`。

### C. 下一步计划 (Phases)
1.  **Phase 1**: 配置加载与 Task 模型定义。
2.  **Phase 2**: 核心 Router 逻辑与 YAML 驱动的 Dispatcher。
3.  **Phase 3**: 多文件存储 Exporter 的实现。
