# src/db_utils.py - Database utilities and helpers

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from src.database import User, Like, Match, Referral, Skip, ProfileView, async_session_maker


class DatabaseManager:
    """Centralized database operations manager"""
    
    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
        """Get user by telegram_id"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(telegram_id: int, username: str = None) -> User:
        """Create new user"""
        async with async_session_maker() as session:
            user = User(telegram_id=telegram_id, username=username)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    
    @staticmethod
    async def get_or_create_user(telegram_id: int, username: str = None) -> User:
        """Get existing user or create new one"""
        user = await DatabaseManager.get_user_by_telegram_id(telegram_id)
        if not user:
            user = await DatabaseManager.create_user(telegram_id, username)
        return user
    
    @staticmethod
    async def update_user_profile(telegram_id: int, **kwargs) -> bool:
        """Update user profile with given data"""
        async with async_session_maker() as session:
            user = await DatabaseManager.get_user_by_telegram_id(telegram_id)
            if not user:
                return False
            
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            user.last_active = datetime.utcnow()
            await session.commit()
            return True
    
    @staticmethod
    async def create_like(from_user_id: int, to_user_id: int, is_super_like: bool = False) -> Like:
        """Create like and update statistics"""
        async with async_session_maker() as session:
            # Check if already liked
            existing = await session.execute(
                select(Like).where(
                    Like.from_user_id == from_user_id,
                    Like.to_user_id == to_user_id
                )
            )
            if existing.scalar_one_or_none():
                return None  # Already liked
            
            like = Like(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                is_super_like=is_super_like
            )
            session.add(like)
            
            # Update user stats
            from_user = await session.get(User, from_user_id)
            to_user = await session.get(User, to_user_id)
            
            if from_user:
                from_user.likes_sent += 1
                from_user.last_active = datetime.utcnow()
            if to_user:
                to_user.likes_received += 1
            
            await session.commit()
            await session.refresh(like)
            return like
    
    @staticmethod
    async def create_skip(from_user_id: int, to_user_id: int) -> Skip:
        """Create skip record"""
        async with async_session_maker() as session:
            skip = Skip(
                from_user_id=from_user_id,
                to_user_id=to_user_id
            )
            session.add(skip)
            
            # Update last active
            user = await session.get(User, from_user_id)
            if user:
                user.last_active = datetime.utcnow()
            
            await session.commit()
            await session.refresh(skip)
            return skip
    
    @staticmethod
    async def check_mutual_like(user1_id: int, user2_id: int) -> bool:
        """Check if both users liked each other"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Like).where(
                    Like.from_user_id == user2_id,
                    Like.to_user_id == user1_id
                )
            )
            return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def create_match(user1_id: int, user2_id: int) -> Match:
        """Create match between two users"""
        async with async_session_maker() as session:
            # Check if match already exists
            existing = await session.execute(
                select(Match).where(
                    or_(
                        and_(Match.user1_id == user1_id, Match.user2_id == user2_id),
                        and_(Match.user1_id == user2_id, Match.user2_id == user1_id)
                    )
                )
            )
            if existing.scalar_one_or_none():
                return None  # Match already exists
            
            match = Match(
                user1_id=min(user1_id, user2_id),
                user2_id=max(user1_id, user2_id)
            )
            session.add(match)
            
            # Update match counts
            user1 = await session.get(User, user1_id)
            user2 = await session.get(User, user2_id)
            
            if user1:
                user1.matches_count += 1
            if user2:
                user2.matches_count += 1
            
            await session.commit()
            await session.refresh(match)
            return match
    
    @staticmethod
    async def get_potential_matches(user_id: int, limit: int = 10) -> List[User]:
        """Get potential matches for user with smart filtering"""
        async with async_session_maker() as session:
            user = await session.get(User, user_id)
            if not user:
                return []
            
            # Build query with filters
            query = select(User).where(
                User.id != user_id,
                User.is_active == True,
                User.is_banned == False,
                User.name.isnot(None),
                User.photos.isnot(None),
                User.age.isnot(None)
            )
            
            # Gender preference filter
            if user.looking_for and user.looking_for != 'both':
                query = query.where(User.gender == user.looking_for)
            
            # Age range filter (±5 years)
            if user.age:
                min_age = max(18, user.age - 5)
                max_age = min(99, user.age + 5)
                query = query.where(
                    and_(User.age >= min_age, User.age <= max_age)
                )
            
            # Exclude already interacted profiles
            liked_subquery = select(Like.to_user_id).where(Like.from_user_id == user_id)
            skipped_subquery = select(Skip.to_user_id).where(Skip.from_user_id == user_id)
            matched_subquery1 = select(Match.user2_id).where(Match.user1_id == user_id)
            matched_subquery2 = select(Match.user1_id).where(Match.user2_id == user_id)
            
            query = query.where(
                User.id.notin_(liked_subquery),
                User.id.notin_(skipped_subquery),
                User.id.notin_(matched_subquery1),
                User.id.notin_(matched_subquery2)
            )
            
            # Order by activity
            query = query.order_by(User.last_active.desc())
            query = query.limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def get_user_matches(user_id: int) -> List[Dict]:
        """Get all matches for user with user info"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Match).where(
                    or_(
                        Match.user1_id == user_id,
                        Match.user2_id == user_id
                    ),
                    Match.is_active == True
                ).order_by(Match.created_at.desc())
            )
            matches = result.scalars().all()
            
            match_data = []
            for match in matches:
                matched_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
                matched_user = await session.get(User, matched_user_id)
                
                if matched_user:
                    match_data.append({
                        'match_id': match.id,
                        'user': matched_user,
                        'created_at': match.created_at
                    })
            
            return match_data
    
    @staticmethod
    async def record_profile_view(viewer_id: int, viewed_id: int):
        """Record profile view for analytics"""
        async with async_session_maker() as session:
            view = ProfileView(
                viewer_id=viewer_id,
                viewed_id=viewed_id
            )
            session.add(view)
            
            # Update view count
            viewed_user = await session.get(User, viewed_id)
            if viewed_user:
                viewed_user.views_count += 1
            
            await session.commit()
    
    @staticmethod
    async def get_user_stats(user_id: int) -> Dict:
        """Get comprehensive user statistics"""
        async with async_session_maker() as session:
            user = await session.get(User, user_id)
            if not user:
                return {}
            
            # Get weekly stats
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            likes_week = await session.execute(
                select(func.count(Like.id)).where(
                    and_(
                        Like.from_user_id == user_id,
                        Like.created_at >= week_ago
                    )
                )
            )
            
            matches_week = await session.execute(
                select(func.count(Match.id)).where(
                    and_(
                        or_(Match.user1_id == user_id, Match.user2_id == user_id),
                        Match.created_at >= week_ago
                    )
                )
            )
            
            views_week = await session.execute(
                select(func.count(ProfileView.id)).where(
                    and_(
                        ProfileView.viewed_id == user_id,
                        ProfileView.created_at >= week_ago
                    )
                )
            )
            
            return {
                'user': user,
                'likes_this_week': likes_week.scalar() or 0,
                'matches_this_week': matches_week.scalar() or 0,
                'views_this_week': views_week.scalar() or 0,
                'daily_likes_remaining': user.daily_likes_remaining,
                'is_premium': user.is_premium
            }
    
    @staticmethod
    async def process_referral(referrer_telegram_id: int, new_user_id: int) -> Dict:
        """Process referral and give bonuses"""
        async with async_session_maker() as session:
            referrer = await DatabaseManager.get_user_by_telegram_id(referrer_telegram_id)
            new_user = await session.get(User, new_user_id)
            
            if not referrer or not new_user:
                return {'success': False, 'message': 'User not found'}
            
            # Check if already referred
            existing = await session.execute(
                select(Referral).where(Referral.new_user_id == new_user_id)
            )
            if existing.scalar_one_or_none():
                return {'success': False, 'message': 'Already referred'}
            
            # Create referral
            referral = Referral(
                referrer_id=referrer.id,
                new_user_id=new_user_id
            )
            session.add(referral)
            
            # Give bonuses
            referrer_bonus = 10
            new_user_bonus = 5
            
            referrer.bonus_likes += referrer_bonus
            new_user.bonus_likes += new_user_bonus
            
            await session.commit()
            
            return {
                'success': True,
                'referrer_bonus': referrer_bonus,
                'new_user_bonus': new_user_bonus
            }
    
    @staticmethod
    async def get_referral_stats(user_id: int) -> Dict:
        """Get referral statistics for user"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Referral).where(Referral.referrer_id == user_id)
            )
            referrals = result.scalars().all()
            
            return {
                'total_referrals': len(referrals),
                'referrals': referrals
            }
