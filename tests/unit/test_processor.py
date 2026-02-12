import pytest
from app.processor import MessageProcessor
from app.models import MessageData
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_processor_enhancement():
    msg = MessageData(
        message_id=1, time="now", sender="user", 
        content="test", url="https://example.com",
        source_group="g", source_id="1"
    )
    
    with patch("app.metadata.metadata_provider.fetch_metadata", new_callable=AsyncMock) as mock_fetch:
        # 返回 (title, final_url)
        mock_fetch.return_value = ("Mock Title", "https://example.com")
        processed = await MessageProcessor.process(msg)
        assert processed.title == "Mock Title"
        assert processed.url == "https://example.com"

def test_processor_match():
    from pydantic import BaseModel
    class MockTask(BaseModel):
        keywords: list
        
    task = MockTask(keywords=["apple", "banana"])
    
    msg1 = MessageData(
        message_id=1, time="now", sender="u", content="I like Apple", 
        source_group="g", source_id="1"
    )
    msg2 = MessageData(
        message_id=2, time="now", sender="u", content="I like Orange", 
        source_group="g", source_id="1"
    )
    
    assert MessageProcessor.is_match(task, msg1) is True
    assert MessageProcessor.is_match(task, msg2) is False
