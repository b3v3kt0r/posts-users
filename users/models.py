from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from database.engine import Base
from comments.models import Comment


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String, nullable=False)

    posts = relationship("Post", back_populates="user")
    comments = relationship("Comment", back_populates="user")
