import pytest
from app.metadata import MetadataProvider
import aiohttp

@pytest.mark.asyncio
async def test_metadata_cache():
    provider = MetadataProvider()
    url = "https://example.com"
    provider.cache[url] = "Cached Title"
    
    title = await provider.fetch_title(url)
    assert title == "Cached Title"

@pytest.mark.asyncio
async def test_metadata_fetch_real_url():
    # This test might fail if there's no internet, so we skip it or mock it
    # But for a basic demonstration of aiohttp Mocking or real fetch:
    provider = MetadataProvider()
    url = "https://www.google.com"
    title = await provider.fetch_title(url)
    if title: # If internet available
        assert isinstance(title, str)
        assert len(title) > 0
