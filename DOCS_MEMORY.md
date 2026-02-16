# 项目开发记忆 (Project Development Memory)

## 2026-02-15: 元数据抓取优化 (Metadata Fetching Optimization)

### 问题分析 (Issue Analysis)
**现象**: 系统日志中频繁出现 `WARNING - 抓取元数据失败`。
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
