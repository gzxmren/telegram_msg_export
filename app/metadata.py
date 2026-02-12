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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate"
        }

    def _is_safe_url(self, url: str) -> bool:
        """检查 URL 是否安全，防止 SSRF 攻击 (禁止内网/本地请求)"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname.lower() if parsed.hostname else ""
            
            # 禁止空主机名或常见的本地/内网模式
            if not hostname: return False
            if hostname in ["localhost", "127.0.0.1", "0.0.0.0", "::1"]: return False
            
            # 禁止私有 IP 段 (KISS 原则：正则匹配常见内网段)
            if re.match(r'^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)', hostname):
                return False
                
            return True
        except:
            return False

    async def fetch_metadata(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """抓取网页元数据 (标题 + 最终 URL)，带缓存和严格超时"""
        if not url: return None, None
        if not self._is_safe_url(url):
            logger.warning(f"🛡️ 拦截潜在的 SSRF 请求: {url}")
            return None, None
            
        if url in self.cache: return self.cache[url]

        # 针对特定平台的 Headers 调整
        request_headers = self.headers.copy()
        if "douyin.com" in url or "iesdouyin.com" in url:
            # 抖音通常对移动端 UA 更友好，且重定向逻辑更直接
            request_headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"

        try:
            # 10秒超时，防止阻塞主流程
            async with aiohttp.ClientSession(headers=request_headers) as session:
                async with session.get(url, timeout=10, allow_redirects=True) as response:
                    if response.status != 200:
                        return None, None
                    
                    final_url = str(response.url)

                    # 仅读取前 64KB，足以包含 <title> 标签，节省流量
                    content = await response.content.read(65536)
                    
                    # 尝试猜测编码，避免乱码
                    charset = response.charset or 'utf-8'
                    html = content.decode(charset, errors='replace')
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    title = soup.title.string if soup.title else None
                    
                    if title:
                        title = title.strip().replace('\n', ' ').replace('\r', '')
                        # 截断过长的标题
                        if len(title) > 200: title = title[:197] + "..."
                        
                        self.cache[url] = (title, final_url)
                        return title, final_url
                    
                    # 即使没有标题，也返回 final_url
                    return None, final_url

        except Exception as e:
            # 记录警告但不抛错，确保稳定性
            logger.warning(f"抓取元数据失败 {url}: {e}")
            pass
            
        return None, None

metadata_provider = MetadataProvider()
