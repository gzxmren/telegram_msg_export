# TG-Link-Dispatcher (原 TG-Exporter)

![Version](https://img.shields.io/badge/version-v0.8.0-blue) ![Python](https://img.shields.io/badge/python-3.12+-blue) ![Tests](https://img.shields.io/badge/tests-passing-green)

一个生产级、高可维护性的 Telegram 消息分拣与分发系统。采用 Python 模块化设计，支持多源采集、智能路由、网页标题抓取及 Web 控制面板管理。

## 📋 核心功能 (Current Features)

- **模块化生产架构 (New)**: 逻辑高度解耦，划分为模型层、处理流水线、协议解析层，支持轻松扩展业务逻辑。
- **Web 控制面板 (New)**: 内置基于 FastAPI 的管理后台，支持实时状态监控、系统日志流、以及在线修改配置文件（支持热重载）。
- **智能网页标题抓取 (New)**: 自动发现网页标题，优先使用 Telegram 原生预览数据，兜底采用异步非阻塞 HTTP 抓取（带 3s 超时与缓存）。
- **自动化测试保障 (New)**: 完善的测试套件（Unit & Integration），覆盖率监控，确保大规模数据同步的稳定性。
- **智能 URL 清洗与去重**: 自动剔除追踪参数并实现文件级去重。
- **增强型断点记忆**: 独立管理每个群组的抓取偏移量，支持掉线重启后自动续传。

---

## 🛠️ 安装与配置

### 1. 环境准备
```bash
git clone <your-repo-url>
cd telegram_msg_export
# 推荐使用 Python 3.12+
pip install -r requirements.txt
```

### 2. 凭证配置 (.env)
填入从 [my.telegram.org](https://my.telegram.org) 获取的 API 凭证：
```env
API_ID=your_id
API_HASH=your_hash
PHONE=+your_phone
WEB_PASSWORD=admin  # Web 后端登录密码
```

---

## 🚀 运维管理 (System Management)

本项目提供了统一的管理脚本 `manage.sh`，封装了 Systemd 服务配置与日常操作，彻底解决进程锁冲突问题。

### 1. 首次安装 (Install)
生成并注册 Systemd 服务文件（需 sudo 权限）：
```bash
./manage.sh install
```

### 2. 服务控制
```bash
./manage.sh start    # 启动后台服务
./manage.sh stop     # 停止服务
./manage.sh restart  # 重启服务
./manage.sh status   # 查看运行状态
./manage.sh logs     # 实时查看日志 (Ctrl+C 退出)
```
> Web 控制台地址：`http://localhost:8000`

### 3. 调试模式 (Debug)
如果你需要修改代码并查看实时输出，可以使用调试模式。脚本会自动暂停后台服务以释放文件锁：
```bash
./manage.sh run
```

### 4. 获取群组 ID (Listing Chats)
为了配置监控任务，你需要获取目标群组的 ID。
```bash
python3 list_chats.py
```
**✨ 新特性 (v0.8.1)**: 该脚本支持 **混合模式 (Hybrid Mode)**。
- 如果主程序 (`main_dispatcher.py`) 正在运行，它会自动通过 API 获取列表，**无需停止服务**，彻底解决 `database is locked` 问题。
- 如果主程序未运行，它会自动降级为直接连接模式（需登录）。

### 运行测试
确保任何改动后代码依然稳健：
```bash
pytest
```

---

## 📂 模块化目录结构
- `app/models.py`: 核心数据模型 (MessageData)，定义单一事实来源。
- `app/processor.py`: 处理流水线，负责数据增强（标题发现）与匹配规则。
- `app/dispatcher.py`: 任务编排引擎，协调 Telegram 客户端与导出器。
- `app/metadata.py`: 网页元数据异步抓取服务。
- `app/web.py`: FastAPI 后端服务。
- `app/static/`: Web 控制面板前端资源。
- `tests/`: 自动化测试用例 (Unit/Integration)。

---

## 📅 路线图 (Roadmap)
- [x] **v0.5**: 增量断点管理与 Daemon 模式。
- [x] **v0.6**: 架构解耦重构、URL 标准化清洗、文件级智能去重。
- [x] **v0.7**: 配置管理 Pydantic 化、智能网页标题发现 (Title Discovery)。
- [x] **v0.8**: **Web 控制面板发布**、自动化测试框架集成、配置热重载。
- [ ] **v0.9 (Cloud Ready)**: Docker 容器化支持、Prometheus 监控指标支持。
- [ ] **v1.0 (LTS)**: 长期支持版本、多数据库后端 (SQLite/PostgreSQL) 选配。

---

## ⚠️ 免责声明
本项目仅供学习交流使用。请遵守 Telegram 的 [ToS](https://telegram.org/tos)。
