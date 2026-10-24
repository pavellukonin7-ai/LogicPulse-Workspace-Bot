"""
Модели базы данных
"""
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Task(Base):
    """Модель задачи"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    title = Column(String, nullable=False)
    city = Column(String, nullable=False)
    date = Column(String, nullable=False)  # Формат: 12.10.2025
    time = Column(String, nullable=False)  # Формат: 10:15
    datetime_obj = Column(DateTime, nullable=False)  # Для сортировки и напоминаний
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', city='{self.city}')>"


class TeamTask(Base):
    """Общая задача, доступная всем участникам командного пространства."""

    __tablename__ = "team_tasks"
    __table_args__ = (
        UniqueConstraint("source", "legacy_id", name="uq_team_tasks_source_legacy"),
    )

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    author_name = Column(String, nullable=False)
    author_id = Column(BigInteger, nullable=True, index=True)
    status = Column(String, default="open", nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    source = Column(String, default="logicpulse", nullable=False)
    legacy_id = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<TeamTask(id={self.id}, status='{self.status}')>"

