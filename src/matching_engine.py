# matching_engine.py - Умный алгоритм подбора пар

import asyncio
import math
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

@dataclass
class MatchScore:
    user_id: int
    score: float
    factors: Dict[str, float]
    explanation: str

@dataclass
class UserProfile:
    id: int
    telegram_id: int
    name: str
    age: int
    gender: str
    looking_for: str
    city: str
    location: Optional[Tuple[float, float]]  # (lat, lon)
    bio: str
    interests: List[str]
    photos: List[Dict]
    matches_count: int
    likes_received: int
    views_count: int
    last_active: datetime
    created_at: datetime
    is_premium: bool

class MatchingEngine:
    def __init__(self, db_connection, cache_service=None):
        self.db = db_connection
        self.cache = cache_service
        self.weights = {
            'location': 0.25,      # географическая близость
            'interests': 0.30,     # общие интересы
            'activity': 0.15,      # активность пользователя
            'photo_quality': 0.10, # качество фото
            'popularity': 0.10,    # популярность
            'freshness': 0.10      # новизна аккаунта
        }
    
    async def get_candidates(self, user_id: int, limit: int = 50) -> List[MatchScore]:
        """Основной алгоритм подбора кандидатов"""
        
        try:
            # 1. Получаем профиль пользователя
            user = await self.get_user_profile(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return []
            
            # 2. Проверяем кэш
            cache_key = f"candidates:{user_id}:{limit}"
            if self.cache:
                cached_candidates = await self.cache.get(cache_key)
                if cached_candidates:
                    logger.info(f"Returning cached candidates for user {user_id}")
                    return json.loads(cached_candidates)
            
            # 3. Быстрая предварительная фильтрация
            candidates = await self._pre_filter_candidates(user)
            logger.info(f"Found {len(candidates)} candidates after pre-filtering")
            
            # 4. Детальный расчет совместимости
            scored_candidates = []
            for candidate in candidates[:200]:  # Ограничиваем для производительности
                try:
                    score = await self._calculate_match_score(user, candidate)
                    if score.score > 0.1:  # Минимальный порог
                        scored_candidates.append(score)
                except Exception as e:
                    logger.error(f"Error calculating score for candidate {candidate.id}: {e}")
                    continue
            
            # 5. Сортировка по убыванию score
            scored_candidates.sort(key=lambda x: x.score, reverse=True)
            
            # 6. Ограничиваем результат
            result = scored_candidates[:limit]
            
            # 7. Кэшируем результат
            if self.cache:
                await self.cache.set(cache_key, json.dumps([
                    {
                        'user_id': r.user_id,
                        'score': r.score,
                        'factors': r.factors,
                        'explanation': r.explanation
                    } for r in result
                ]), ttl=300)  # 5 минут
            
            logger.info(f"Returning {len(result)} scored candidates for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_candidates for user {user_id}: {e}")
            return []
    
    async def _pre_filter_candidates(self, user: UserProfile) -> List[UserProfile]:
        """Быстрая предварительная фильтрация кандидатов"""
        
        query = """
            SELECT 
                u.id, u.telegram_id, u.name, u.age, u.gender, u.looking_for,
                u.city, u.location, u.bio, u.matches_count, u.likes_received,
                u.views_count, u.last_active, u.created_at, u.is_premium,
                ARRAY_AGG(i.name) as interests,
                ARRAY_AGG(
                    json_build_object(
                        'url', p.medium_url,
                        'quality_score', p.quality_score
                    )
                ) as photos
            FROM users u
            LEFT JOIN user_interests ui ON u.id = ui.user_id
            LEFT JOIN interests i ON ui.interest_id = i.id
            LEFT JOIN photos p ON u.id = p.user_id AND p.moderation_status = 'approved'
            WHERE u.id != $1  -- не сам пользователь
            AND u.is_active = true
            AND u.gender = $2  -- соответствует предпочтениям по полу
            AND u.age BETWEEN $3 AND $4  -- возраст в диапазоне
            AND NOT EXISTS (  -- не было взаимодействий
                SELECT 1 FROM likes l 
                WHERE l.from_user_id = $1 AND l.to_user_id = u.id
            )
            AND (
                u.location IS NULL OR  -- если нет геолокации
                ST_DWithin(
                    u.location::geography,
                    $5::geography,
                    $6
                )
            )
            GROUP BY u.id, u.telegram_id, u.name, u.age, u.gender, u.looking_for,
                     u.city, u.location, u.bio, u.matches_count, u.likes_received,
                     u.views_count, u.last_active, u.created_at, u.is_premium
            ORDER BY u.last_active DESC
            LIMIT 500
        """
        
        # Определяем возрастной диапазон
        age_range = self._get_age_range(user.age)
        
        # Определяем максимальное расстояние
        max_distance = user.max_distance or 50
        
        # Параметры для геолокации
        location_params = None
        if user.location:
            location_params = f"POINT({user.location[1]} {user.location[0]})"
        
        try:
            rows = await self.db.fetch(
                query,
                user.id,
                user.looking_for,
                age_range['min'],
                age_range['max'],
                location_params,
                max_distance * 1000  # конвертируем в метры
            )
            
            candidates = []
            for row in rows:
                candidate = UserProfile(
                    id=row['id'],
                    telegram_id=row['telegram_id'],
                    name=row['name'],
                    age=row['age'],
                    gender=row['gender'],
                    looking_for=row['looking_for'],
                    city=row['city'],
                    location=self._parse_location(row['location']),
                    bio=row['bio'] or '',
                    interests=[i for i in row['interests'] if i],
                    photos=[p for p in row['photos'] if p['url']],
                    matches_count=row['matches_count'],
                    likes_received=row['likes_received'],
                    views_count=row['views_count'],
                    last_active=row['last_active'],
                    created_at=row['created_at'],
                    is_premium=row['is_premium']
                )
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error in pre_filter_candidates: {e}")
            return []
    
    async def _calculate_match_score(self, user: UserProfile, candidate: UserProfile) -> MatchScore:
        """Детальный расчет совместимости"""
        
        factors = {}
        total_score = 0.0
        
        # 1. Географическая близость
        factors['location'] = self._calculate_location_score(user, candidate)
        total_score += factors['location'] * self.weights['location']
        
        # 2. Совпадение интересов
        factors['interests'] = self._calculate_interests_score(user, candidate)
        total_score += factors['interests'] * self.weights['interests']
        
        # 3. Активность пользователя
        factors['activity'] = self._calculate_activity_score(candidate)
        total_score += factors['activity'] * self.weights['activity']
        
        # 4. Качество фото
        factors['photo_quality'] = self._calculate_photo_quality_score(candidate)
        total_score += factors['photo_quality'] * self.weights['photo_quality']
        
        # 5. Популярность
        factors['popularity'] = self._calculate_popularity_score(candidate)
        total_score += factors['popularity'] * self.weights['popularity']
        
        # 6. Новизна аккаунта
        factors['freshness'] = self._calculate_freshness_score(candidate)
        total_score += factors['freshness'] * self.weights['freshness']
        
        # Генерируем объяснение
        explanation = self._generate_explanation(factors, user, candidate)
        
        return MatchScore(
            user_id=candidate.id,
            score=min(1.0, max(0.0, total_score)),  # Ограничиваем 0-1
            factors=factors,
            explanation=explanation
        )
    
    def _calculate_location_score(self, user: UserProfile, candidate: UserProfile) -> float:
        """Расчет географической близости"""
        
        if not user.location or not candidate.location:
            return 0.5  # Нейтральный score если нет геолокации
        
        distance_km = self._calculate_distance(user.location, candidate.location)
        
        # Ближе = лучше, максимум 50 км
        if distance_km <= 5:
            return 1.0  # Очень близко
        elif distance_km <= 15:
            return 0.8  # Близко
        elif distance_km <= 30:
            return 0.6  # Средне
        elif distance_km <= 50:
            return 0.4  # Далеко
        else:
            return 0.2  # Очень далеко
    
    def _calculate_interests_score(self, user: UserProfile, candidate: UserProfile) -> float:
        """Расчет совместимости интересов (Jaccard similarity)"""
        
        if not user.interests or not candidate.interests:
            return 0.5  # Нейтральный score
        
        user_interests = set(user.interests)
        candidate_interests = set(candidate.interests)
        
        # Jaccard similarity
        intersection = user_interests.intersection(candidate_interests)
        union = user_interests.union(candidate_interests)
        
        if not union:
            return 0.5
        
        jaccard = len(intersection) / len(union)
        
        # Бонус за много общих интересов
        common_bonus = min(0.2, len(intersection) * 0.05)
        
        return min(1.0, jaccard + common_bonus)
    
    def _calculate_activity_score(self, candidate: UserProfile) -> float:
        """Расчет активности пользователя"""
        
        hours_since_active = (datetime.now() - candidate.last_active).total_seconds() / 3600
        
        # Активные пользователи получают больший score
        if hours_since_active <= 1:
            return 1.0  # Онлайн
        elif hours_since_active <= 24:
            return 0.8  # Активен сегодня
        elif hours_since_active <= 168:  # 7 дней
            return 0.6  # Активен на неделе
        elif hours_since_active <= 720:  # 30 дней
            return 0.4  # Активен в месяце
        else:
            return 0.2  # Неактивен
    
    def _calculate_photo_quality_score(self, candidate: UserProfile) -> float:
        """Расчет качества фото"""
        
        if not candidate.photos:
            return 0.3  # Низкий score без фото
        
        # Средний score качества фото
        quality_scores = [p.get('quality_score', 0.5) for p in candidate.photos]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Бонус за количество фото
        photo_bonus = min(0.2, len(candidate.photos) * 0.05)
        
        return min(1.0, avg_quality + photo_bonus)
    
    def _calculate_popularity_score(self, candidate: UserProfile) -> float:
        """Расчет популярности (нормализованный)"""
        
        if candidate.likes_received == 0:
            return 0.5  # Нейтральный score
        
        # Коэффициент матчей (сколько матчей из лайков)
        match_ratio = candidate.matches_count / candidate.likes_received
        
        # Нормализуем (хороший коэффициент ~0.1-0.2)
        popularity = min(1.0, match_ratio * 5)
        
        return popularity
    
    def _calculate_freshness_score(self, candidate: UserProfile) -> float:
        """Расчет новизны аккаунта"""
        
        days_since_joined = (datetime.now() - candidate.created_at).days
        
        # Новые пользователи получают приоритет
        if days_since_joined <= 1:
            return 1.0  # Только что зарегистрировался
        elif days_since_joined <= 7:
            return 0.8  # Неделя
        elif days_since_joined <= 30:
            return 0.6  # Месяц
        elif days_since_joined <= 90:
            return 0.4  # 3 месяца
        else:
            return 0.2  # Старый аккаунт
    
    def _generate_explanation(self, factors: Dict[str, float], user: UserProfile, candidate: UserProfile) -> str:
        """Генерация объяснения совпадения"""
        
        explanations = []
        
        # Географическая близость
        if factors['location'] > 0.8:
            explanations.append("Очень близко к тебе")
        elif factors['location'] > 0.6:
            explanations.append("Рядом с тобой")
        elif factors['location'] > 0.4:
            explanations.append("В твоем районе")
        
        # Интересы
        if factors['interests'] > 0.7:
            explanations.append("Много общих интересов")
        elif factors['interests'] > 0.4:
            explanations.append("Есть общие интересы")
        
        # Активность
        if factors['activity'] > 0.8:
            explanations.append("Очень активный пользователь")
        elif factors['activity'] > 0.6:
            explanations.append("Активный пользователь")
        
        # Популярность
        if factors['popularity'] > 0.8:
            explanations.append("Очень популярный профиль")
        elif factors['popularity'] > 0.6:
            explanations.append("Популярный профиль")
        
        # Новизна
        if factors['freshness'] > 0.8:
            explanations.append("Новый пользователь")
        
        if explanations:
            return ", ".join(explanations)
        else:
            return "Потенциальное совпадение"
    
    def _get_age_range(self, user_age: int) -> Dict[str, int]:
        """Определение возрастного диапазона"""
        
        # Стандартный диапазон ±5 лет
        default_range = 5
        
        # Адаптивный диапазон в зависимости от возраста
        if user_age <= 25:
            range_adjustment = 3  # Молодые пользователи более строгие
        elif user_age <= 35:
            range_adjustment = 5
        else:
            range_adjustment = 7  # Взрослые пользователи более гибкие
        
        return {
            'min': max(18, user_age - range_adjustment),
            'max': min(99, user_age + range_adjustment)
        }
    
    def _calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Расчет расстояния между двумя точками (Haversine formula)"""
        
        lat1, lon1 = loc1
        lat2, lon2 = loc2
        
        # Радиус Земли в км
        R = 6371
        
        # Конвертируем в радианы
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Разности
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _parse_location(self, location_data) -> Optional[Tuple[float, float]]:
        """Парсинг данных геолокации из PostgreSQL"""
        
        if not location_data:
            return None
        
        try:
            # Предполагаем формат POINT(lon lat)
            if hasattr(location_data, 'x') and hasattr(location_data, 'y'):
                return (location_data.y, location_data.x)  # (lat, lon)
            else:
                return None
        except:
            return None
    
    async def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Получение профиля пользователя"""
        
        query = """
            SELECT 
                u.id, u.telegram_id, u.name, u.age, u.gender, u.looking_for,
                u.city, u.location, u.bio, u.matches_count, u.likes_received,
                u.views_count, u.last_active, u.created_at, u.is_premium,
                u.max_distance,
                ARRAY_AGG(i.name) as interests,
                ARRAY_AGG(
                    json_build_object(
                        'url', p.medium_url,
                        'quality_score', p.quality_score
                    )
                ) as photos
            FROM users u
            LEFT JOIN user_interests ui ON u.id = ui.user_id
            LEFT JOIN interests i ON ui.interest_id = i.id
            LEFT JOIN photos p ON u.id = p.user_id AND p.moderation_status = 'approved'
            WHERE u.id = $1 AND u.is_active = true
            GROUP BY u.id, u.telegram_id, u.name, u.age, u.gender, u.looking_for,
                     u.city, u.location, u.bio, u.matches_count, u.likes_received,
                     u.views_count, u.last_active, u.created_at, u.is_premium, u.max_distance
        """
        
        try:
            row = await self.db.fetchrow(query, user_id)
            if not row:
                return None
            
            return UserProfile(
                id=row['id'],
                telegram_id=row['telegram_id'],
                name=row['name'],
                age=row['age'],
                gender=row['gender'],
                looking_for=row['looking_for'],
                city=row['city'],
                location=self._parse_location(row['location']),
                bio=row['bio'] or '',
                interests=[i for i in row['interests'] if i],
                photos=[p for p in row['photos'] if p['url']],
                matches_count=row['matches_count'],
                likes_received=row['likes_received'],
                views_count=row['views_count'],
                last_active=row['last_active'],
                created_at=row['created_at'],
                is_premium=row['is_premium']
            )
            
        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {e}")
            return None

# ELO Rating System для дополнительного ранжирования
class EloRatingSystem:
    """ELO система для ранжирования привлекательности профилей"""
    
    def __init__(self, k_factor: float = 32):
        self.k_factor = k_factor
    
    def calculate_new_ratings(self, winner_rating: float, loser_rating: float):
        """Расчет новых ELO рейтингов после свайпа"""
        
        expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
        expected_loser = 1 / (1 + 10 ** ((winner_rating - loser_rating) / 400))
        
        new_winner_rating = winner_rating + self.k_factor * (1 - expected_winner)
        new_loser_rating = loser_rating + self.k_factor * (0 - expected_loser)
        
        return new_winner_rating, new_loser_rating
    
    async def update_ratings_on_like(self, db, liker_id: int, liked_id: int):
        """Обновление ELO при получении лайка"""
        
        # Получаем текущие рейтинги
        liker_elo = await db.fetchval("SELECT elo_rating FROM users WHERE id = $1", liker_id) or 1200
        liked_elo = await db.fetchval("SELECT elo_rating FROM users WHERE id = $1", liked_id) or 1200
        
        # Рассчитываем новые рейтинги (лайкнутый "выигрывает")
        new_liked_elo, _ = self.calculate_new_ratings(liked_elo, liker_elo)
        
        # Обновляем рейтинг лайкнутого пользователя
        await db.execute("UPDATE users SET elo_rating = $1 WHERE id = $2", new_liked_elo, liked_id)
        
        return new_liked_elo
