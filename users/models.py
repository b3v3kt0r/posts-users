from passlib.context import CryptContext
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from database.engine import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String, nullable=False)

    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    def hase_password(self, password):
        self.password = pwd_context.hash(password)
