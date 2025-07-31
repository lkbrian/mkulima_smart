from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Float,
)
from sqlalchemy.orm import relationship

metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)
db = SQLAlchemy(metadata=metadata)


class User(db.Model):
    """User to store users for premuim services."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    phone_number = Column(String(20), nullable=True)
    is_premuim = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chat_sessions = relationship("ChatSession", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


class ChatSession(db.Model):
    """Chat session model to store LLM conversation sessions."""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship(
        "ChatMessage", backref="session", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChatSession {self.session_id}>"


class ChatMessage(db.Model):
    """Chat message model to store individual messages in conversations."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    chat_metadata = Column(Text, nullable=True)  # JSON string for additional data
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatMessage {self.message_type}: {self.content[:50]}...>"


class KnowledgeBase(db.Model):
    """Knowledge base model to store agricultural knowledge and FAQs."""

    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # crops, livestock, weather, etc.
    tags = Column(String(500), nullable=True)  # comma-separated tags
    language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<KnowledgeBase {self.title}>"


class WeatherData(db.Model):
    """Weather data model to store weather information."""

    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True)
    location = Column(String(200), nullable=False)
    date = Column(DateTime, nullable=False)
    temperature_max = Column(Float, nullable=True)
    temperature_min = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    rainfall = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    weather_condition = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WeatherData {self.location} - {self.date}>"
