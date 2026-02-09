from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict

class MessageData(BaseModel):
    """标准化的消息数据模型"""
    model_config = ConfigDict(frozen=False)

    message_id: int
    time: str
    sender: str
    title: Optional[str] = ""
    url: Optional[str] = ""
    content: str
    source_group: str
    source_id: str
    reply_to: Optional[int] = None
    
    # 元数据，方便后续扩展
    metadata: dict = Field(default_factory=dict)

    @classmethod
    def get_csv_headers(cls) -> List[str]:
        return ['message_id', 'time', 'sender', 'title', 'url', 'content', 'source_group', 'source_id', 'reply_to']
