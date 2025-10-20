# src/features.py - Additional features

from datetime import datetime
from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import User, Referral


class ReferralSystem:
    """Referral system for user acquisition"""
    
    @staticmethod
    def generate_referral_link(telegram_id: int) -> str:
        """Generate referral link for user"""
        return f"https://t.me/FFlirtly_bot?start=ref_{telegram_id}"
    
    @staticmethod
    async def process_referral(
        referrer_telegram_id: int,
        new_user_id: int,
        session: AsyncSession
    ) -> Dict:
        """
        Process referral when new user joins
        
        Returns:
        {
            'success': bool,
            'referrer_bonus': int,
            'new_user_bonus': int,
            'message': str
        }
        """
        
        try:
            # Get referrer user
            referrer_result = await session.execute(
                select(User).where(User.telegram_id == referrer_telegram_id)
            )
            referrer = referrer_result.scalar_one_or_none()
            
            if not referrer:
                return {
                    'success': False,
                    'referrer_bonus': 0,
                    'new_user_bonus': 0,
                    'message': 'Referrer not found'
                }
            
            # Get new user
            new_user = await session.get(User, new_user_id)
            if not new_user:
                return {
                    'success': False,
                    'referrer_bonus': 0,
                    'new_user_bonus': 0,
                    'message': 'New user not found'
                }
            
            # Check if already referred
            existing_referral = await session.execute(
                select(Referral).where(Referral.new_user_id == new_user_id)
            )
            if existing_referral.scalar_one_or_none():
                return {
                    'success': False,
                    'referrer_bonus': 0,
                    'new_user_bonus': 0,
                    'message': 'Already referred'
                }
            
            # Create referral record
            referral = Referral(
                referrer_id=referrer.id,
                new_user_id=new_user_id,
                bonus_likes=5
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
                'new_user_bonus': new_user_bonus,
                'message': 'Referral processed successfully'
            }
            
        except Exception as e:
            await session.rollback()
            return {
                'success': False,
                'referrer_bonus': 0,
                'new_user_bonus': 0,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    async def get_referral_stats(user_id: int, session: AsyncSession) -> Dict:
        """Get referral statistics for user"""
        
        # Count referrals
        referrals_result = await session.execute(
            select(Referral).where(Referral.referrer_id == user_id)
        )
        referrals = referrals_result.scalars().all()
        
        total_referrals = len(referrals)
        total_bonus_likes = sum(r.bonus_likes for r in referrals)
        
        return {
            'total_referrals': total_referrals,
            'total_bonus_likes': total_bonus_likes,
            'referrals': referrals
        }


class Analytics:
    """Analytics and statistics"""
    
    @staticmethod
    async def get_user_stats(user_id: int, session: AsyncSession) -> Dict:
        """Get comprehensive user statistics"""
        
        user = await session.get(User, user_id)
        if not user:
            return {}
        
        # Get recent activity
        from sqlalchemy import func, and_
        from src.database import Like, Match, ProfileView
        
        # Likes sent in last 7 days
        week_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = week_ago.replace(day=week_ago.day - 7)
        
        likes_week = await session.execute(
            select(func.count(Like.id)).where(
                and_(
                    Like.from_user_id == user_id,
                    Like.created_at >= week_ago
                )
            )
        )
        likes_this_week = likes_week.scalar() or 0
        
        # Matches this week
        matches_week = await session.execute(
            select(func.count(Match.id)).where(
                and_(
                    or_(Match.user1_id == user_id, Match.user2_id == user_id),
                    Match.created_at >= week_ago
                )
            )
        )
        matches_this_week = matches_week.scalar() or 0
        
        # Profile views this week
        views_week = await session.execute(
            select(func.count(ProfileView.id)).where(
                and_(
                    ProfileView.viewed_id == user_id,
                    ProfileView.created_at >= week_ago
                )
            )
        )
        views_this_week = views_week.scalar() or 0
        
        return {
            'user': user,
            'likes_this_week': likes_this_week,
            'matches_this_week': matches_this_week,
            'views_this_week': views_this_week,
            'daily_likes_remaining': user.daily_likes_remaining,
            'is_premium': user.is_premium
        }
