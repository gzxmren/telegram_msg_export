import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.dispatcher import Dispatcher
from app.models import MessageData

@pytest.fixture
def mock_checkpoint():
    with patch("app.dispatcher.CheckpointManager") as MockCheckpoint:
        instance = MockCheckpoint.return_value
        instance.get.return_value = 0
        yield instance

@pytest.fixture
def mock_config():
    with patch("app.dispatcher.Config") as MockConfig:
        MockConfig.tasks = []
        yield MockConfig

@pytest.fixture
def mock_processor():
    with patch("app.dispatcher.MessageProcessor") as MockProcessor:
        MockProcessor.process = AsyncMock(side_effect=lambda x: x)
        MockProcessor.is_match.return_value = True
        yield MockProcessor

@pytest.fixture
def mock_parser():
    with patch("app.dispatcher.parse_message", new_callable=AsyncMock) as mock_parse:
        yield mock_parse

@pytest.fixture
def mock_exporter_factory():
    with patch("app.dispatcher.ExporterFactory") as MockFactory:
        yield MockFactory

@pytest.mark.asyncio
async def test_sync_source_saves_checkpoint_on_connection_error(
    mock_checkpoint, mock_config, mock_processor, mock_parser, mock_exporter_factory
):
    # Setup
    dispatcher = Dispatcher()
    
    # Mock task
    mock_task = MagicMock()
    mock_task.sources = ["123"]
    mock_task.output.path = "test.csv"
    mock_task.output.format = "csv"
    mock_config.tasks = [mock_task]
    
    # Mock client and entity
    client = MagicMock()
    entity = MagicMock()
    entity.id = 123
    entity.title = "Test Group"
    
    # Mock utils.get_peer_id
    with patch("app.dispatcher.utils.get_peer_id", return_value=123):
        # Mock iter_messages to yield one message then raise ConnectionError
        message1 = MagicMock()
        message1.id = 10
        
        async def async_iter(*args, **kwargs):
            yield message1
            # Simulate processing delay to ensure execution order if needed, 
            # but for async generator raising in yield flow:
            raise ConnectionError("Simulated connection error")
            
        client.iter_messages.side_effect = lambda *args, **kwargs: async_iter()
        
        # Mock parse_message return value
        mock_msg_data = MagicMock(spec=MessageData)
        mock_msg_data.source_group = "Test Group"
        mock_msg_data.url = "http://example.com"
        mock_msg_data.model_dump.return_value = {}
        mock_parser.return_value = mock_msg_data
        
        # Mock exporter
        mock_exporter = MagicMock()
        mock_exporter.is_duplicate.return_value = False
        dispatcher.exporters["test.csv"] = mock_exporter

        # Execute and Expect Error
        with pytest.raises(ConnectionError):
            await dispatcher._sync_source(client, entity)
            
        # Verify checkpoint was saved
        # The first message had ID 10. Last ID was 0.
        # So it should save 10.
        mock_checkpoint.set.assert_called_with("123", 10)

@pytest.mark.asyncio
async def test_sync_source_saves_checkpoint_on_flood_wait_error(
    mock_checkpoint, mock_config, mock_processor, mock_parser, mock_exporter_factory
):
    # Define a mock exception that mimics FloodWaitError
    class MockFloodWaitError(Exception):
        def __init__(self, seconds):
            self.seconds = seconds

    # Patch the FloodWaitError in app.dispatcher
    with patch("app.dispatcher.FloodWaitError", MockFloodWaitError):
        # Setup
        dispatcher = Dispatcher()
        
        # Mock task
        mock_task = MagicMock()
        mock_task.sources = ["123"]
        mock_config.tasks = [mock_task]
        
        client = MagicMock()
        entity = MagicMock()
        entity.id = 123
        
        with patch("app.dispatcher.utils.get_peer_id", return_value=123):
            message1 = MagicMock()
            message1.id = 20
            
            async def async_iter(*args, **kwargs):
                yield message1
                raise MockFloodWaitError(seconds=1)
                
            client.iter_messages.side_effect = lambda *args, **kwargs: async_iter()
            
            mock_msg_data = MagicMock(spec=MessageData)
            mock_msg_data.source_group = "Test Group"
            mock_msg_data.url = "http://example.com"
            mock_msg_data.model_dump.return_value = {}
            mock_parser.return_value = mock_msg_data
            
            dispatcher.exporters["test.csv"] = MagicMock()

            # Execute - FloodWaitError is caught and swallowed (after sleep)
            # We need to mock asyncio.sleep to avoid waiting
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await dispatcher._sync_source(client, entity)
                
                mock_sleep.assert_called_with(1)
                
            # Verify checkpoint was saved
            mock_checkpoint.set.assert_called_with("123", 20)
