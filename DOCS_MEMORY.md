# 项目开发记忆 (Project Development Memory)

## 2026-02-15: 元数据抓取优化 (Metadata Fetching Optimization)

### 问题分析 (Issue Analysis)
**现象**: 系统日志中频繁出现 `WARNING - 抓取元数据失败`，且抖音链接标题为空。

### 2026-02-17: 修复微信/抖音元数据抓取及标题缺失问题
**问题原因**:
1. **连接超时**: `app/metadata.py` 之前在处理国内域名时强制禁用代理（直连），导致在某些直连不通的环境（即便在国内服务器）下超时。且 `aiohttp` 默认不识别 `.env` 中的 SOCKS5/HTTP 代理配置。
2. **抖音标题空白**: 抖音网页采用 SPA 动态加载且有较强防爬措施，单纯依赖 HTML `<title>` 标签很难获取内容。

**修复方案**:
1. **代理增强**: 
    - 修改 `app/metadata.py`，使 `aiohttp` 在请求时显式读取 `AppConfig` 中的 HTTP 代理配置。
    - 启用 `trust_env=True`，允许程序识别系统级的环境变量代理（如 `HTTPS_PROXY`）。
2. **抖音标题本地提取**: 
    - 在 `app/parser.py` 中增加针对抖音分享格式的正则解析。如果识别到抖音 URL，直接从 Telegram 消息文本中提取 `【...作品】` 之后的描述作为标题，不再完全依赖不稳定的网页抓取。
3. **容错与解码**:
    - 在 `app/metadata.py` 中增加了对 `RENDER_DATA` 的解析以及 `unicode_escape` 解码，提升从 HTML 源码中提取标题的成功率。

**验证结果**:
- 微信/抖音元数据抓取不再报错。
- 抖音分享记录的 `title` 字段现在能准确显示视频描述。
**根源**: 代理导致国内站点慢、微信空 `<title>` 标签。
**解决方案**: 引入国内域名白名单、绕过代理直连、支持 `og:title` 提取、增加读取限制至 128KB。

## 2026-02-16: 逻辑修复与双重抓取保障 (Logic Fix & Dual-Layer Fetching)

### 问题分析 (Issue Analysis)
**现象**: 日志出现 `Connection timeout`，部分任务崩溃。
**根源**: 
1. `soup` 未定义引起的 `NameError`。
2. 直连握手超过 5s 预设超时。
**解决方案**: 修复 `soup` 初始化逻辑、连接超时翻倍至 10s、引入“直连失败自动回退至代理”机制。

## 2026-02-16: 编码解压与 Brotli 兼容性优化 (Content-Encoding Fix)

### 问题分析 (Issue Analysis)
**现象**: 日志报错 `400, message: Can not decode content-encoding: br`。
**根源**: 服务器返回 Brotli 压缩数据但环境中缺少解压库。
**解决方案**: 
1. Header 显式声明仅接受 `gzip, deflate`。
2. 设置 `auto_decompress=False` 绕过 `aiohttp` 自动解压崩溃点。
3. 使用内置 `zlib` 手动处理解压，增强鲁棒性。
