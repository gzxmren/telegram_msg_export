# X/Twitter Article 与 Video URL 差异参考

在 X (Twitter) 平台上，**Article (长文章)** 和 **Video (视频/普通推文)** 的 URL 主要在路径结构上有所区别。结合本项目（TG-Link-Dispatcher）的实现逻辑，差异如下：

### 1. URL 路径结构差异
*   **普通推文 / 视频推文 (Status):** 
    *   标准格式：`https://x.com/[用户名]/status/[ID]`
    *   媒体视图格式：`https://x.com/i/status/[ID]`（常用于直接分享视频或直播，不带用户名）。
    *   *注意：X 上的视频通常是嵌入在普通推文中的，因此大部分视频链接在结构上与普通推文一致。*
*   **X Articles (长文章):**
    *   标准格式：`https://x.com/i/articles/[ID]`
    *   这是 X 专门为长内容（原 Notes 功能）设计的路径，与普通 Status 链接有明显区分。

### 2. 参数干扰 (Tracking Parameters)
无论是文章还是视频，从客户端分享出的链接通常带有大量的追踪参数（如 `?s=20`, `?t=...`, `?utm_source=...`），这些参数会导致同一内容产生多个不同的 URL。

### 3. 本项目中的处理方式
根据代码库（`app/cleaner.py` 和 `rules.yaml`）的实现：
*   **统一归一化：** 项目将 `x.com`, `twitter.com`, `vxtwitter.com`, `fxtwitter.com` 全部识别为 `twitter` 平台。
*   **强清洗策略 (`strip_all`)：** 程序会自动移除 `?` 之后的所有参数。
    *   `https://x.com/user/status/123?s=20` -> `https://x.com/user/status/123`
    *   `https://x.com/i/status/1888...456?s=46` -> `https://x.com/i/status/1888...456`
*   **去重逻辑：** 清洗后的规范化链接（Canonical URL）被用作唯一标识符（Unique Key），确保同一条视频或文章在 CSV 中只会被记录一次，无论分享来源如何。

### 总结对比表

| 类型 | 典型 URL 路径 | 项目处理策略 |
| :--- | :--- | :--- |
| **视频/普通推文** | `/status/[ID]` 或 `/i/status/[ID]` | 移除所有参数，保留 ID 路径 |
| **长文章 (Article)**| `/i/articles/[ID]` | 移除所有参数，保留 ID 路径 |
