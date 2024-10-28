import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean, DateTime
)
from sqlalchemy.orm import relationship

from database.engine import Base
from users.models import User


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    content = Column(String(10000))
    user_id = Column(Integer, ForeignKey("users.id"))
    auto_replay_enabled = Column(Boolean, default=False)
    auto_replay_delay = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC), nullable=False)
    comments = relationship("Comment", back_populates="post")

    user = relationship("User", back_populates="posts")
