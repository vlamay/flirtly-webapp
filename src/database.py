# src/database.py - Complete database models

from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import String, Integer, DateTime, Boolean, Float, Text, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Database URL
DATABASE_URL = "sqlite+aiosqlite:///./flirtly.db"

# Engine
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


# Base
class Base(AsyncAttrs, DeclarativeBase):
    pass


# Enums
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class LookingFor(str, Enum):
    MALE = "male"
    FEMALE = "female"
    BOTH = "both"


class SubscriptionType(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    PLATINUM = "platinum"


# Models
class User(Base):
    __tablename__ = "users"
    
    # Primary
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Profile
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(String(20), nullable=True)
    looking_for: Mapped[Optional[LookingFor]] = mapped_column(String(20), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Photos (comma-separated file_ids)
    photos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Location
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Stats
    likes_sent: Mapped[int] = mapped_column(Integer, default=0)
    likes_received: Mapped[int] = mapped_column(Integer, default=0)
    matches_count: Mapped[int] = mapped_column(Integer, default=0)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Premium
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        String(20), 
        default=SubscriptionType.FREE
    )
    premium_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    bonus_likes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Activity
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    @property
    def is_premium(self) -> bool:
        """Check if user has active premium"""
        if not self.premium_until:
            return False
        return datetime.utcnow() < self.premium_until
    
    @property
    def daily_likes_remaining(self) -> int:
        """Calculate remaining daily likes"""
        if self.is_premium:
            return 999  # Unlimited
        
        # Check if it's a new day
        today = datetime.utcnow().date()
        last_active_date = self.last_active.date() if self.last_active else today
        
        if last_active_date < today:
            return 10  # Reset to 10 for new day
        
        return max(0, 10 - self.likes_sent + self.bonus_likes)
    
    def __repr__(self):
        return f"<User {self.id} @{self.username}>"


class Like(Base):
    __tablename__ = "likes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    to_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    
    is_super_like: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Like {self.from_user_id} -> {self.to_user_id}>"


class Match(Base):
    __tablename__ = "matches"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user1_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    user2_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Match {self.user1_id} <-> {self.user2_id}>"


class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), index=True)
    from_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Message {self.id} in Match {self.match_id}>"


class Referral(Base):
    __tablename__ = "referrals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    new_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True)
    
    bonus_likes: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Referral {self.referrer_id} -> {self.new_user_id}>"


class Skip(Base):
    """Track skipped profiles to avoid showing them again"""
    __tablename__ = "skips"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    to_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Skip {self.from_user_id} -X-> {self.to_user_id}>"


class ProfileView(Base):
    """Track profile views for analytics"""
    __tablename__ = "profile_views"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    viewer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    viewed_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<View {self.viewer_id} -> {self.viewed_id}>"


# Database initialization
async def init_db():
    """Initialize database - create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized successfully!")


async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session_maker() as session:
        yield session


# Helper functions
async def get_user_by_telegram_id(telegram_id: int, session: AsyncSession) -> Optional[User]:
    """Get user by telegram_id"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(telegram_id: int, username: Optional[str], session: AsyncSession) -> User:
    """Create new user"""
    user = User(telegram_id=telegram_id, username=username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user(telegram_id: int, username: Optional[str], session: AsyncSession) -> User:
    """Get existing user or create new one"""
    user = await get_user_by_telegram_id(telegram_id, session)
    if not user:
        user = await create_user(telegram_id, username, session)
    return user
