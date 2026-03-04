from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False)
    last_joke_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class CommonJoke(Base):
    __tablename__ = "common"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Text, nullable=False)
    user_id = Column(Integer, nullable=True)


class BlackJoke(Base):
    __tablename__ = "black"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Text, nullable=False)
    user_id = Column(Integer, nullable=True)


class AttemptJoke(Base):
    __tablename__ = "attempt"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Text, nullable=False)
    user_id = Column(Integer, nullable=True)


class Rating(Base):
    __tablename__ = "rating"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False)
    rate = Column(Integer, default=0, nullable=False)
    accepted_count = Column(Integer, default=0, nullable=False)
