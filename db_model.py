from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
import sqlalchemy
import uuid

Base = declarative_base()

class Users_info(Base):
    __tablename__ = 'Users_info'

    id = Column(Integer, primary_key=True, autoincrement=True)  # 内部主键
    user_uuid = Column(String(11), unique=True, nullable=False) # 外部标识
    name = Column(String(100), nullable=False)
    password = Column(String(300), nullable=False)
    email = Column(String(100), nullable=False)
    address = Column(String(100), nullable=True)

    # 关联聊天记录
    chat_history = relationship("ChatHistory", back_populates="user")

# 定义对话历史表
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 聊天记录主键
    user_uuid = Column(String(11), ForeignKey("Users_info.user_uuid"), nullable=False)  # 外键关联 user_uuid
    topic_id = Column(String(36), nullable=False)  # 话题 UUID
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # 关联用户
    user = relationship("Users_info", back_populates="chat_history")

# 定义管理者表
class Admin_info(Base):
    __tablename__ = "Admin_info"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 记录主键
    name = Column(String(100), nullable=False)
    password = Column(String(300), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
