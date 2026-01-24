# Telegram Group Message Exporter (TG-Exporter)

![Version](https://img.shields.io/badge/version-v0.3.1-green) ![Python](https://img.shields.io/badge/python-3.10+-blue)

一个轻量级、模块化的 Python 工具，用于通过 MTProto 协议批量导出 Telegram 群组历史消息。

## 📋 功能特性 (Features)

### ✅ 核心功能 (已上线)
- **智能增量更新 (New)**: 默认采用“增量追加”模式。程序会自动检测 CSV 中已存在的最大 `message_id`，仅拉取更新的消息并追加到文件末尾，极大节省时间和流量。
- **命令行支持 (New)**: 支持 `--help`, `--chat-id`, `--force` 等参数，方便脚本调用和临时任务。
- **历史消息全量导出**: 基于用户视角（User-Bot），可导出加入群组后的所有可见历史消息。
- **Excel 完美兼容**: 导出格式采用 `UTF-8-SIG` 编码，Windows 下 Excel 打开无乱码。
- **内容清洗**: 自动提取文本，将多媒体转换为标签 (`[图片]`, `[文件]`)，时间转为本地时区。
- **流式写入**: 实时 Flush 写入磁盘，内存占用极低，支持 10万+ 级数据导出。
- **可视化与日志**: 集成 `tqdm` 进度条与 `logging` 日志记录。
- **抗限流**: 自动处理 `FloodWaitError`。

### 📅 开发计划 (Roadmap)
- [x] **v0.1 MVP**: 基础连通性验证
- [x] **v0.2 Core**: 核心导出与解析功能
- [x] **v0.3 Stable**: 流式写入、进度条、抗限流
- [x] **v0.3.1 Advanced**: 增量更新策略、CLI 参数支持 (当前版本)
- [ ] **v1.0 Release**: 类型注解、代码精简、打包发布

---

## 🛠️ 安装与配置

### 1. 环境准备
```bash
git clone <your-repo-url>
cd tg_exporter
pip install -r requirements.txt
```

### 2. 配置文件 (.env)
复制模版 `cp .env.example .env` 并填入：
```ini
API_ID=123456
API_HASH=abcdef...
PHONE=+86138...
CHAT_ID=-100...        # 目标群组 ID
EXPORT_PATH=output/messages.csv
```

---

## 🚀 使用指南 (CLI)

### 基础用法
直接运行，默认读取 `.env` 配置并执行**增量更新**：
```bash
python main.py
```

### 常用命令
查看所有可用参数：
```bash
python main.py --help
```

**强制全量重新导出 (覆盖旧文件)**:
```bash
python main.py --force
```

**临时导出另一个群 (不修改配置)**:
```bash
python main.py --chat-id -100987654321 --output output/temp.csv
```

**仅测试拉取前 50 条**:
```bash
python main.py --limit 50 --force
```

### 参数说明
| 参数 | 缩写 | 说明 |
| :--- | :--- | :--- |
| `--help` | `-h` | 显示帮助信息 |
| `--chat-id` | `-c` | 覆盖目标群组 ID |
| `--output` | `-o` | 覆盖导出文件路径 |
| `--force` | `-f` | 强制全量拉取 (忽略历史断点) |
| `--limit` | `-l` | 限制拉取数量 (用于测试) |

---

## 📂 增量更新机制说明
- **默认行为**: 程序启动时检查 CSV 文件。如果存在，读取最后一条消息 ID (`min_id`)，只拉取比它新的消息。
- **数据顺序**: 导出数据按 **时间正序 (Oldest -> Newest)** 排列，以便追加写入。
- **初次运行**: 如果没有 CSV 文件，会自动进行全量拉取。

---

## ⚠️ 免责声明
本项目仅供学习交流使用。请遵守 Telegram 的 [ToS](https://telegram.org/tos)。
