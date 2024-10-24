from datetime import datetime

from pydantic import BaseModel


class PostBase(BaseModel):
    title: str
    content: str
    user_id: int
    auto_replay_enabled: bool
    auto_replay_delay: int
    created_at: datetime


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int

    class Config:
        from_attributes = True
