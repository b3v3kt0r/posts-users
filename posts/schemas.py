from datetime import datetime

from pydantic import BaseModel


class PostBase(BaseModel):
    title: str
    content: str
    auto_replay_enabled: bool
    auto_replay_delay: int


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
