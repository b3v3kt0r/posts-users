from datetime import datetime

from pydantic import BaseModel


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    is_blocked: bool = False


class Comment(CommentBase):
    id: int
    user_id: int
    post_id: int
    is_blocked: bool
    created_at: datetime
