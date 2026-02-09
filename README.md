# TG-Link-Dispatcher (原 TG-Exporter)

![Version](https://img.shields.io/badge/version-v0.6.0-blue) ![Python](https://img.shields.io/badge/python-3.10+-blue)

一个工程化、高扩展性的 Telegram 消息分拣与分发系统。采用 Python 面向对象设计，支持多源采集、智能路由、URL 清洗及长连接守护运行。

## 📋 核心功能 (Current Features)

- **工程化架构 (New)**: 采用工厂模式与抽象基类重构，逻辑高度解耦，支持轻松扩展导出格式（如 Markdown, SQL）。
- **智能 URL 清洗 (New)**: 基于 `rules.yaml` 自动剔除 X (Twitter) 及微信链接中的追踪参数，还原规范化链接 (Canonical URL)。
- **智能去重 (New)**: 基于清洗后的链接实现文件级自动去重，确保采集到的信息流“干净无水”。
- **多源路由分拣**: 自由定义任务规则，根据来源与关键词将消息自动导向不同目录。
- **增强型断点记忆**: 使用独立的 `CheckpointManager` 记录每个群组的抓取偏移量。
- **长连接守护模式**: 仅需单次登录，维持稳定长连接进行高频率轮询。

---

## 🛠️ 安装与配置

### 1. 环境准备
```bash
git clone <your-repo-url>
cd telegram_msg_export
# 推荐使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 凭证配置 (.env)
复制模板 `cp .env.example .env` 并填入从 [my.telegram.org](https://my.telegram.org) 获取的 API ID/Hash。

### 3. 任务分发配置 (config.yaml)
在根目录下配置您的分发任务：
```yaml
tasks:
  - name: "Twitter_Article"
    enable: true
    sources: [-100123456789] # 目标群组 ID
    keywords: ["twitter.com", "x.com"]
    output:
      path: "./data/x/x_url.csv"
      format: "csv"

  - name: "WeChat_Links"
    enable: true
    sources: ["all"]         # 监听所有加入的群
    keywords: ["mp.weixin.qq.com"]
    output:
      path: "./data/wechat/articles.csv"
      format: "csv"
```

---

## 🚀 使用指南

### 获取群组 ID
运行工具脚本查看您账号下的群组列表及对应 ID：
```bash
python3 list_chats.py
```

### 运行分发器 (单次同步)
```bash
python3 main_dispatcher.py
```

### 运行守护模式 (后台自动轮询)
```bash
# 每 10 分钟自动检查一次更新
python3 main_dispatcher.py --daemon --interval 600
```

---

## 📂 目录结构
- `app/dispatcher.py`: 核心编排引擎 (Orchestrator)。
- `app/exporter.py`: 抽象导出层 (Factory Pattern)。
- `app/checkpoint.py`: 增量进度管理器。
- `app/cleaner.py`: 链接提取与规则清洗器。
- `data/checkpoint.json`: 存储所有群组的抓取偏移量。
- `rules.yaml`: 平台 URL 清洗规则。
- `config.yaml`: 任务分发配置。

---

## 📅 开发计划 (Roadmap)
- [x] **v0.5**: 增量断点管理与 Daemon 模式。
- [x] **v0.6**: 架构解耦重构、URL 标准化清洗、文件级智能去重。
- [ ] **v1.0**: Linux Systemd 生产级部署方案、Markdown 格式支持。

---

## ⚠️ 免责声明
本项目仅供学习交流使用。请遵守 Telegram 的 [ToS](https://telegram.org/tos)。
