import asyncio
import aiohttp
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from app.logger import logger
from typing import Optional
import re

class MetadataProvider:
    """网页元数据抓取器 - 重点关注稳定性和效率"""
    
    def __init__(self):
        self.cache = {} # 简单的内存缓存: {url: title}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }

    def _is_safe_url(self, url: str) -> bool:
        """检查 URL 是否安全，防止 SSRF 攻击 (禁止内网/本地请求)"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname.lower() if parsed.hostname else ""
            if not hostname: return False
            if hostname in ["localhost", "127.0.0.1", "0.0.0.0", "::1"]: return False
            if re.match(r'^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)', hostname):
                return False
            return True
        except:
            return False

    async def fetch_metadata(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """抓取网页元数据 (标题 + 最终 URL)，带缓存和自动代理回退机制"""
        if not url: return None, None
        if not self._is_safe_url(url):
            logger.warning(f"🛡️ 拦截潜在的 SSRF 请求: {url}")
            return None, None
            
        if url in self.cache: return self.cache[url]

        domestic_patterns = [
            r"douyin\.com", r"iesdouyin\.com", r"weixin\.qq\.com", 
            r"zhihu\.com", r"bilibili\.com", r"weibo\.com", r"qq\.com"
        ]
        is_domestic = any(re.search(p, url) for p in domestic_patterns)
        
        async def try_fetch(use_proxy: bool):
            request_headers = self.headers.copy()
            if "douyin.com" in url or "iesdouyin.com" in url:
                request_headers.update({
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                })
            elif "mp.weixin.qq.com" in url:
                request_headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Referer": "https://mp.weixin.qq.com/",
                })

            timeout = aiohttp.ClientTimeout(total=15, connect=10)
            async with aiohttp.ClientSession(
                headers=request_headers,
                max_line_size=16384,
                max_field_size=16384,
                trust_env=use_proxy
            ) as session:
                async with session.get(url, timeout=timeout, allow_redirects=True) as response:
                    final_url = str(response.url)
                    if response.status != 200:
                        return None, final_url
                    
                    try:
                        # 对于巨大的页面（如微信），我们只读取前 256KB 原始数据
                        # aiohttp 的 read(n) 会处理解压后的数据（如果 auto_decompress=True）
                        # 256KB 对元数据抓取绰绰有余
                        content_bytes = await response.content.read(262144)
                        html = content_bytes.decode(response.charset or 'utf-8', errors='replace')
                        logger.debug(f"HTML Prefix for {url}: {html[:200]}...")
                    except Exception as e:
                        if "Can not decode content-encoding: br" in str(e):
                             # 如果是 br 错误，且我们还没装 brotli，这是一个降级点
                             logger.debug(f"Brotli 编码无法解析，尝试降级读取原始流: {url}")
                             # 这种情况下直接读二进制流（未解压的）尝试正则匹配
                             # 因为元数据通常是 ASCII/UTF-8 字符，在压缩流中也有一定概率被正则匹配到（如果是 identity）
                        return None, final_url
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    title = soup.title.string if soup.title else None
                    
                    if not title or not title.strip():
                        meta_og_title = soup.find("meta", attrs={"property": "og:title"})
                        if meta_og_title:
                            title = meta_og_title.get("content")
                        
                        if not title:
                            meta_tw_title = soup.find("meta", attrs={"property": "twitter:title"}) or soup.find("meta", attrs={"name": "twitter:title"})
                            if meta_tw_title:
                                title = meta_tw_title.get("content")
                    
                    if not title:
                        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                        if match:
                            title = match.group(1)
                        else:
                            match_og = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE)
                            if match_og:
                                title = match_og.group(1)
                            else:
                                # 微信特有变量提取
                                js_title_match = re.search(r'var msg_title = ["\'](.*?)["\'];', html)
                                if js_title_match:
                                    title = js_title_match.group(1)

                    if title:
                        title = re.sub(r'\s+', ' ', str(title)).strip()
                        if len(title) > 200: title = title[:197] + "..."
                        return title, final_url
                    
                    return None, final_url

        try:
            # 第一轮抓取
            title, final_url = await try_fetch(use_proxy=not is_domestic)
            
            # 如果是国内域名且没拿到标题，或者拿到了 200 但内容是空的，尝试代理重试
            if is_domestic and not title:
                logger.debug(f"🔄 国内域名首轮获取标题为空，尝试代理重试: {url}")
                title, final_url = await try_fetch(use_proxy=True)

            if title:
                self.cache[url] = (title, final_url)
                return title, final_url
            return title, final_url

        except Exception as e:
            error_msg = str(e) or e.__class__.__name__
            if is_domestic:
                try:
                    logger.debug(f"🔄 国内域名异常 ({error_msg})，尝试代理重试: {url}")
                    return await try_fetch(use_proxy=True)
                except Exception as e2:
                    logger.warning(f"抓取元数据失败(重试也失败) {url}: {e2}")
            else:
                logger.warning(f"抓取元数据失败 {url}: {error_msg}")
            
        return None, None

metadata_provider = MetadataProvider()
