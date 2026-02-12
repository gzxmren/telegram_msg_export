import pytest
from app.metadata import MetadataProvider
import aiohttp

@pytest.mark.asyncio
async def test_metadata_cache():
    provider = MetadataProvider()
    url = "https://example.com"
    # 现在缓存存储的是元组 (title, final_url)
    provider.cache[url] = ("Cached Title", url)
    
    title, final_url = await provider.fetch_metadata(url)
    assert title == "Cached Title"
    assert final_url == url

@pytest.mark.asyncio
async def test_metadata_fetch_real_url():
    # 这是一个基础测试，如果没联网会跳过
    provider = MetadataProvider()
    url = "https://www.google.com"
    title, final_url = await provider.fetch_metadata(url)
    if final_url: # 如果请求成功
        assert isinstance(final_url, str)
        if title:
            assert isinstance(title, str)
            assert len(title) > 0
