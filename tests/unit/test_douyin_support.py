import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.metadata import MetadataProvider
from app.processor import MessageProcessor
from app.models import MessageData

@pytest.mark.asyncio
async def test_metadata_douyin_ua():
    """测试 MetadataProvider 是否针对抖音使用了特定的 User-Agent"""
    provider = MetadataProvider()
    url = "https://v.douyin.com/iYsCx2/"
    
    # 1. 构造 Mock Response
    mock_response = MagicMock() # Use MagicMock for structural attributes
    mock_response.status = 200
    mock_response.url = "https://www.douyin.com/video/733456789012345?utm_source=copy"
    mock_response.charset = "utf-8"
    
    # content.read must be an AsyncMock
    mock_response.content = MagicMock()
    mock_response.content.read = AsyncMock(return_value=b"<html><title>Douyin Video</title></html>")
    
    # 2. 构造 Mock Session
    mock_session = MagicMock()
    
    # session.get returns an async context manager
    mock_get_ctx = MagicMock()
    mock_get_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_session.get.return_value = mock_get_ctx
    
    # ClientSession() returns an async context manager
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)
    
    # 3. 执行测试
    with patch("aiohttp.ClientSession", return_value=mock_session_ctx) as MockSession:
        title, final_url = await provider.fetch_metadata(url)
        
        # 验证返回结果
        assert title == "Douyin Video"
        assert final_url == str(mock_response.url)
        
        # 验证 ClientSession 初始化时是否传入了 headers
        init_kwargs = MockSession.call_args[1]
        headers = init_kwargs.get("headers", {})
        
        assert "User-Agent" in headers
        assert "Android" in headers["User-Agent"]
        assert headers.get("Accept-Encoding") == "gzip, deflate"

@pytest.mark.asyncio
async def test_processor_url_expansion():
    """测试 Processor 是否正确处理短链展开和清洗"""
    
    # 模拟输入消息
    msg = MessageData(
        message_id=1,
        time="2023-01-01 12:00:00",
        sender="test",
        url="https://v.douyin.com/short/",
        content="Check this out",
        source_group="Test Group",
        source_id="1001"
    )
    
    # 模拟 MetadataProvider 的返回
    expanded_url = "https://www.douyin.com/video/123456?utm_source=ios&share_token=abc"
    clean_url = "https://www.douyin.com/video/123456"
    
    with patch("app.metadata.metadata_provider.fetch_metadata", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = ("Awesome Video", expanded_url)
        
        # 执行处理
        processed_msg = await MessageProcessor.process(msg)
        
        # 验证
        assert processed_msg.title == "Awesome Video"
        assert processed_msg.url == clean_url
