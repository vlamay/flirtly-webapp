# src/matching.py - Smart matching algorithm

import math
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import User, Like, Skip, Match, ProfileView, Gender, LookingFor


class MatchingEngine:
    """Smart matching algorithm with filters"""
    
    @staticmethod
    async def get_potential_matches(
        user: User,
        session: AsyncSession,
        limit: int = 10
    ) -> List[User]:
        """
        Get potential matches for user with smart filtering
        
        Filters:
        1. Gender preferences
        2. Age range (±5 years)
        3. Not already liked/skipped
        4. Not already matched
        5. Active users only
        6. Has complete profile
        7. Proximity (if location available)
        """
        
        # Base query
        query = select(User).where(
            User.id != user.id,
            User.is_active == True,
            User.is_banned == False,
            User.name.isnot(None),
            User.photos.isnot(None),
            User.age.isnot(None)
        )
        
        # Filter by gender preference
        if user.looking_for == LookingFor.MALE:
            query = query.where(User.gender == Gender.MALE)
        elif user.looking_for == LookingFor.FEMALE:
            query = query.where(User.gender == Gender.FEMALE)
        # If BOTH, no filter
        
        # Filter by age range
        if user.age:
            min_age = max(18, user.age - 5)
            max_age = min(99, user.age + 5)
            query = query.where(
                User.age >= min_age,
                User.age <= max_age
            )
        
        # Exclude already interacted profiles
        # Get IDs of liked users
        liked_subquery = select(Like.to_user_id).where(
            Like.from_user_id == user.id
        )
        
        # Get IDs of skipped users
        skipped_subquery = select(Skip.to_user_id).where(
            Skip.from_user_id == user.id
        )
        
        # Get IDs of matched users
        matched_subquery1 = select(Match.user2_id).where(
            Match.user1_id == user.id,
            Match.is_active == True
        )
        matched_subquery2 = select(Match.user1_id).where(
            Match.user2_id == user.id,
            Match.is_active == True
        )
        
        query = query.where(
            User.id.notin_(liked_subquery),
            User.id.notin_(skipped_subquery),
            User.id.notin_(matched_subquery1),
            User.id.notin_(matched_subquery2)
        )
        
        # Order by activity and proximity
        query = query.order_by(User.last_active.desc())
        
        # Apply limit
        query = query.limit(limit)
        
        result = await session.execute(query)
        matches = result.scalars().all()
        
        # Sort by distance if location available
        if user.latitude and user.longitude:
            matches = sorted(
                matches,
                key=lambda m: MatchingEngine.calculate_distance(
                    user.latitude, user.longitude,
                    m.latitude or 0, m.longitude or 0
                ) if m.latitude and m.longitude else 999999
            )
        
        return list(matches)
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates in kilometers
        Using Haversine formula
        """
        # Earth radius in km
        R = 6371
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return round(distance, 1)
    
    @staticmethod
    async def process_like(
        from_user: User,
        to_user_id: int,
        is_super_like: bool,
        session: AsyncSession
    ) -> dict:
        """
        Process like action
        
        Returns:
        {
            'success': bool,
            'is_match': bool,
            'match_id': int or None,
            'message': str
        }
        """
        
        # Check if already liked
        existing_like = await session.execute(
            select(Like).where(
                Like.from_user_id == from_user.id,
                Like.to_user_id == to_user_id
            )
        )
        if existing_like.scalar_one_or_none():
            return {
                'success': False,
                'is_match': False,
                'match_id': None,
                'message': 'Already liked'
            }
        
        # Create like
        like = Like(
            from_user_id=from_user.id,
            to_user_id=to_user_id,
            is_super_like=is_super_like
        )
        session.add(like)
        
        # Update stats
        from_user.likes_sent += 1
        from_user.last_active = datetime.utcnow()
        
        to_user = await session.get(User, to_user_id)
        if to_user:
            to_user.likes_received += 1
        
        await session.commit()
        
        # Check for mutual like (match)
        mutual_like = await session.execute(
            select(Like).where(
                Like.from_user_id == to_user_id,
                Like.to_user_id == from_user.id
            )
        )
        
        if mutual_like.scalar_one_or_none():
            # Create match
            match = Match(
                user1_id=min(from_user.id, to_user_id),
                user2_id=max(from_user.id, to_user_id)
            )
            session.add(match)
            
            # Update match counts
            from_user.matches_count += 1
            if to_user:
                to_user.matches_count += 1
            
            await session.commit()
            await session.refresh(match)
            
            return {
                'success': True,
                'is_match': True,
                'match_id': match.id,
                'matched_user': to_user,
                'message': 'Match created!'
            }
        
        return {
            'success': True,
            'is_match': False,
            'match_id': None,
            'message': 'Like sent'
        }
    
    @staticmethod
    async def process_skip(
        from_user: User,
        to_user_id: int,
        session: AsyncSession
    ) -> dict:
        """Process skip action"""
        
        # Create skip record
        skip = Skip(
            from_user_id=from_user.id,
            to_user_id=to_user_id
        )
        session.add(skip)
        
        from_user.last_active = datetime.utcnow()
        
        await session.commit()
        
        return {
            'success': True,
            'message': 'Skipped'
        }
    
    @staticmethod
    async def record_view(
        viewer: User,
        viewed_id: int,
        session: AsyncSession
    ):
        """Record profile view for analytics"""
        
        view = ProfileView(
            viewer_id=viewer.id,
            viewed_id=viewed_id
        )
        session.add(view)
        
        # Update view count
        viewed_user = await session.get(User, viewed_id)
        if viewed_user:
            viewed_user.views_count += 1
        
        await session.commit()
