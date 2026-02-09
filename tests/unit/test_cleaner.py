import pytest
from app.cleaner import URLCleaner

def test_extract_urls():
    cleaner = URLCleaner()
    text = "Check this out https://google.com and http://test.com/path?a=1"
    urls = cleaner.extract_urls(text)
    assert len(urls) == 2
    assert "https://google.com" in urls
    assert "http://test.com/path?a=1" in urls

def test_normalize_generic_url():
    cleaner = URLCleaner()
    # Mocking rules since rules.yaml might vary
    cleaner.rules = {"global": {"default_strip": ["utm_source", "spm"]}, "platforms": []}
    url = "https://example.com/page?utm_source=news&id=123&spm=1.2.3"
    normalized = cleaner.normalize(url)
    assert "utm_source" not in normalized
    assert "spm" not in normalized
    assert "id=123" in normalized

def test_normalize_platform_strip_all():
    cleaner = URLCleaner()
    cleaner.rules = {
        "platforms": [
            {"domains": ["twitter.com", "x.com"], "strategy": "strip_all"}
        ]
    }
    url = "https://x.com/user/status/123?s=20&t=abc"
    normalized = cleaner.normalize(url)
    assert normalized == "https://x.com/user/status/123"

def test_normalize_platform_whitelist():
    cleaner = URLCleaner()
    cleaner.rules = {
        "platforms": [
            {"domains": ["mp.weixin.qq.com"], "strategy": "whitelist", "keep": ["__biz", "mid"]}
        ]
    }
    url = "https://mp.weixin.qq.com/s?__biz=MzA3&mid=123&sn=xyz&chksm=789"
    normalized = cleaner.normalize(url)
    assert "__biz=MzA3" in normalized
    assert "mid=123" in normalized
    assert "sn=" not in normalized
    assert "chksm=" not in normalized
