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

    # Test new i/status format
    url_v = "https://x.com/i/status/1888463515811123456?s=46"
    assert cleaner.normalize(url_v) == "https://x.com/i/status/1888463515811123456"

    # Test enhanced domains (vxtwitter)
    url_vx = "https://vxtwitter.com/user/status/123?tracking=xyz"
    assert cleaner.normalize(url_vx) == "https://vxtwitter.com/user/status/123"

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

def test_normalize_youtube():
    cleaner = URLCleaner()
    cleaner.rules = {
        "platforms": [
            {"domains": ["youtube.com", "youtu.be"], "strategy": "whitelist", "keep": ["v", "t"]}
        ]
    }
    # Test youtube.com
    url1 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&si=tracking_id&feature=emb_rel_end"
    norm1 = cleaner.normalize(url1)
    assert "v=dQw4w9WgXcQ" in norm1
    assert "si=" not in norm1
    assert "feature=" not in norm1

    # Test youtu.be
    url2 = "https://youtu.be/dQw4w9WgXcQ?si=another_id&t=10"
    norm2 = cleaner.normalize(url2)
    assert "dQw4w9WgXcQ" in norm2
    assert "t=10" in norm2
    assert "si=" not in norm2
