from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Float, Boolean,
    DateTime, JSON, func
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_message_id = Column(BigInteger, nullable=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(20), nullable=False)  # text_only, drake, distracted_bf, etc.
    template_used = Column(String(50), nullable=True)
    trend_topic = Column(String(200), nullable=True)
    image_path = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=func.now())
    published_at = Column(DateTime, nullable=True)

    # Metrics
    views = Column(Integer, default=0)
    forwards = Column(Integer, default=0)
    reactions = Column(JSON, default=dict)
    comments = Column(Integer, default=0)

    # Scores
    quality_score = Column(Float, nullable=True)
    humor_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)
    engagement_rate = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Post id={self.id} type={self.content_type} score={self.performance_score}>"


class Trend(Base):
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(200), nullable=False)
    keywords = Column(JSON, default=list)
    context = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    source = Column(String(50), nullable=False)  # groq, reddit, google_trends, news
    relevance_score = Column(Float, default=0.5)
    collected_at = Column(DateTime, default=func.now())
    used_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<Trend topic='{self.topic}' source={self.source}>"


class ContentQueue(Base):
    __tablename__ = "content_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meme_data = Column(JSON, nullable=False)
    priority = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    scheduled_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")  # pending, published, rejected, expired

    def __repr__(self):
        return f"<ContentQueue id={self.id} status={self.status} priority={self.priority}>"


class StrategyConfig(Base):
    __tablename__ = "strategy_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_data = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<StrategyConfig id={self.id} active={self.is_active}>"


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False)
    module = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<SystemLog level={self.level} module={self.module}>"


class ApiUsage(Base):
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service = Column(String(50), nullable=False)  # groq, huggingface, reddit, etc.
    endpoint = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<ApiUsage service={self.service} tokens={self.tokens_used}>"
