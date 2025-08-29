"""
Chat models - store sessions and messages
"""

from datetime import datetime
from app.models.database import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship("ChatMessage", backref="session", lazy=True)


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(20), default="user")  # user or bot
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
