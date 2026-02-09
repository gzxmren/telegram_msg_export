# TG-Link-Dispatcher 设计文档 (v2.0)

**日期**: 2026-02-01
**状态**: 草案 (Draft)
**原项目**: TG-Exporter

---

## 1. 项目愿景 (Vision)
本项目将从单一的“消息归档工具”转型为**智能消息调度系统 (TG-Link-Dispatcher)**。
**核心目标**: 自动化监听多个 Telegram 群组，精准提取特定平台（Twitter/X, WeChat, Douyin 等）的内容链接，并根据预设的路由规则，将清洗后的链接与元数据分发到本地不同目录下的 CSV/TXT 文件中。

---

## 2. 核心架构 (Architecture)

系统采用**任务驱动 (Task-Driven)** 模型，核心流程如下：

```mermaid
[Telegram Sources] 
       ↓
[Input Listener] (轮询/增量读取)
       ↓
[URL Extractor] (提取原始链接)
       ↓
[URL Normalizer] (基于 rules.yaml 动态清洗/标准化)
       ↓
[Deduplicator] (基于 Canonical URL 的文件级去重)
       ↓
[Dispatcher] (路由分发)
       ↓
[Storage Adapters] (写入 CSV/TXT)
```

---

## 3. 功能需求详细说明

### 3.1 运行模式 (Running Modes)
系统需支持两种运行模式，通过命令行参数切换：
1.  **后台守护模式 (Daemon)**:
    *   参数: `--daemon`
    *   行为: 长期驻留，按 `loop_interval` 设定的间隔（如 10 分钟）无限循环轮询。
2.  **手动触发模式 (Run-Once)**:
    *   参数: `--run-once` (默认)
    *   行为: 执行一次全量任务检查后退出，适合 Crontab 调度或调试。

### 3.2 链接清洗与标准化 (URL Normalization)
**痛点**: 不同平台链接包含大量追踪参数（如 `utm_source`, `?s=20`），导致重复和数据冗余。微信等平台则需要保留特定参数。
**方案**: **基于规则配置引擎**。
*   不硬编码清洗逻辑。
*   通过 `rules.yaml` 定义不同域名的清洗策略（白名单/黑名单参数）。

### 3.3 智能去重 (Smart Deduplication)
*   **标准**: 使用清洗后的 **Canonical URL** (规范化链接) 作为唯一指纹。
*   **范围**: **文件级去重**。
*   **逻辑**: 在写入目标文件前，程序加载该文件已有的 URL 列表。若新抓取的 URL 已存在，则自动丢弃，保留最早的一条。

### 3.4 历史消息处理
*   **增量更新**: 默认行为。读取 CSV 中最后一条 `message_id`，只拉取更新的消息。
*   **历史回溯**: 支持首次运行自动拉取历史消息，或通过参数强制回溯。

---

## 4. 配置文件设计

系统配置将拆分为两个文件，以实现“任务逻辑”与“清洗规则”的解耦。

### 4.1 主配置 (`config.yaml`)
定义“做什么” (Tasks)。

```yaml
settings:
  session_name: "my_dispatcher"
  loop_interval: 600       # 轮询间隔(秒)
  
tasks:
  - name: "Twitter_Focus"
    enable: true
    sources: [-100111, -100222]   # 监听群组
    platforms: ["twitter"]        # 只提取推特
    output: "./data/twitter_subs.csv"

  - name: "WeChat_Articles"
    enable: true
    sources: [-100333]
    platforms: ["wechat"]
    output: "./data/read_later/wechat.csv"
```

### 4.2 规则配置 (`rules.yaml`)
定义“怎么做” (Normalization Rules)。

```yaml
platforms:
  twitter:
    domains: ["x.com", "twitter.com"]
    normalization:
      mode: "whitelist_params"
      params: []  # 移除所有参数，只留路径

  wechat:
    domains: ["mp.weixin.qq.com"]
    normalization:
      mode: "whitelist_params"
      params: ["__biz", "mid", "idx", "sn"] # 仅保留核心参数
      
  default:
    normalization:
      mode: "blacklist_params"
      params: ["utm_source", "share_id"] # 移除通用垃圾参数
```

---

## 5. 数据存储格式

### CSV 格式 (推荐)
保留完整元数据，便于溯源。
**Columns**:
*   `fetched_at`: 抓取时间
*   `msg_date`: 消息发送时间
*   `chat_id`: 来源群组
*   `sender`: 发送者
*   `platform`: 平台标签 (twitter/wechat...)
*   **`url`**: 清洗后的规范化链接
*   `raw_text`: 消息原始文本片段

---

## 6. 开发路线图 (Roadmap)

*   **Phase 1: 基础架构重构**
    *   引入 `PyYAML`。
    *   建立 `config.yaml` 和 `rules.yaml`。
    *   定义 Task 数据结构。
*   **Phase 2: 核心解析引擎**
    *   实现 `URLCleaner` 类：加载 YAML 规则，执行正则匹配与参数清洗。
    *   更新 `Parser` 模块：集成 URL 提取功能。
*   **Phase 3: 调度与存储**
    *   实现 `Dispatcher`：遍历 Task，拉取消息，调用清洗，分发数据。
    *   实现 `SmartExporter`：支持去重写入。
    *   实现 Daemon/Run-once 循环逻辑。
