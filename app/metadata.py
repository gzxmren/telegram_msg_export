import asyncio
import aiohttp
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
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

    async def fetch_title(self, url: str) -> Optional[str]:
        """抓取网页标题，带缓存和严格超时"""
        if not url: return None
        if url in self.cache: return self.cache[url]

        try:
            # 3秒硬超时，防止阻塞主流程
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=3, allow_redirects=True) as response:
                    if response.status != 200:
                        return None
                    
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
                        self.cache[url] = title
                        return title
        except Exception as e:
            # 记录警告但不抛错，确保稳定性
            # logger.debug(f"抓取标题失败 {url}: {e}")
            pass
            
        return None

metadata_provider = MetadataProvider()
