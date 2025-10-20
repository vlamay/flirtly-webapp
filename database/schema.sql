-- database/schema.sql - Полная схема базы данных для Flirtly

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- ===================================
-- USERS TABLE
-- ===================================
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    
    -- Profile data
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 18 AND age <= 100),
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    looking_for VARCHAR(10) NOT NULL CHECK (looking_for IN ('male', 'female', 'both')),
    bio TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    location GEOGRAPHY(POINT, 4326), -- PostGIS для геолокации
    
    -- Preferences
    age_min INTEGER DEFAULT 18 CHECK (age_min >= 18),
    age_max INTEGER DEFAULT 99 CHECK (age_max <= 99),
    max_distance INTEGER DEFAULT 50 CHECK (max_distance > 0 AND max_distance <= 1000),
    
    -- Stats
    matches_count INTEGER DEFAULT 0,
    likes_given INTEGER DEFAULT 0,
    likes_received INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    response_rate DECIMAL(3,2) DEFAULT 0.0, -- процент ответов на сообщения
    
    -- Premium
    is_premium BOOLEAN DEFAULT false,
    premium_type VARCHAR(20) DEFAULT 'free',
    premium_until TIMESTAMP,
    
    -- Verification
    is_verified BOOLEAN DEFAULT false,
    verification_photo_url TEXT,
    
    -- Activity
    last_active TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Flags
    is_active BOOLEAN DEFAULT true,
    is_banned BOOLEAN DEFAULT false,
    ban_reason TEXT
);

-- Indexes для производительности
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX idx_users_location ON users USING GIST(location);
CREATE INDEX idx_users_age_gender ON users(age, gender) WHERE is_active = true;
CREATE INDEX idx_users_premium ON users(is_premium, premium_until) WHERE is_active = true;
CREATE INDEX idx_users_last_active ON users(last_active) WHERE is_active = true;

-- ===================================
-- PHOTOS TABLE
-- ===================================
CREATE TABLE photos (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- Photo data
    original_url TEXT NOT NULL,
    thumbnail_url TEXT,
    medium_url TEXT,
    cdn_url TEXT, -- CloudFlare R2/Cloudinary
    
    -- Metadata
    position INTEGER DEFAULT 0, -- порядок фото в профиле
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    
    -- Moderation
    moderation_status VARCHAR(20) DEFAULT 'pending' CHECK (moderation_status IN ('pending', 'approved', 'rejected', 'flagged')),
    moderation_score DECIMAL(3,2),
    moderation_notes TEXT,
    
    -- AI Analysis
    ai_tags TEXT[], -- теги от ML анализа
    face_detection_score DECIMAL(3,2),
    quality_score DECIMAL(3,2),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    moderated_at TIMESTAMP
);

CREATE INDEX idx_photos_user ON photos(user_id);
CREATE INDEX idx_photos_moderation ON photos(moderation_status);
CREATE INDEX idx_photos_position ON photos(user_id, position);

-- ===================================
-- INTERESTS TABLES
-- ===================================
CREATE TABLE interests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50), -- 'hobby', 'sport', 'music', etc.
    emoji VARCHAR(10),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE user_interests (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    interest_id INTEGER REFERENCES interests(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, interest_id)
);

-- Populate interests
INSERT INTO interests (name, category, emoji) VALUES
-- Hobbies
('Путешествия', 'hobby', '✈️'),
('Фотография', 'hobby', '📸'),
('Чтение', 'hobby', '📚'),
('Кино', 'hobby', '🎬'),
('Искусство', 'hobby', '🎨'),
('Кулинария', 'hobby', '🍳'),

-- Sports
('Фитнес', 'sport', '💪'),
('Йога', 'sport', '🧘'),
('Бег', 'sport', '🏃'),
('Плавание', 'sport', '🏊'),
('Велоспорт', 'sport', '🚴'),
('Танцы', 'sport', '💃'),

-- Music
('Поп', 'music', '🎵'),
('Рок', 'music', '🎸'),
('Классика', 'music', '🎼'),
('Джаз', 'music', '🎺'),
('Электроника', 'music', '🎧'),

-- Lifestyle
('Здоровое питание', 'lifestyle', '🥗'),
('Медитация', 'lifestyle', '🧘‍♀️'),
('Экология', 'lifestyle', '🌱'),
('Карьера', 'lifestyle', '💼'),
('Семья', 'lifestyle', '👨‍👩‍👧‍👦');

-- ===================================
-- LIKES TABLE (interactions)
-- ===================================
CREATE TABLE likes (
    id BIGSERIAL PRIMARY KEY,
    from_user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    to_user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(10) NOT NULL CHECK (action IN ('like', 'dislike', 'superlike')),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(from_user_id, to_user_id)
);

CREATE INDEX idx_likes_from ON likes(from_user_id);
CREATE INDEX idx_likes_to ON likes(to_user_id);
CREATE INDEX idx_likes_mutual ON likes(from_user_id, to_user_id);
CREATE INDEX idx_likes_created ON likes(created_at);

-- ===================================
-- MATCHES TABLE
-- ===================================
CREATE TABLE matches (
    id BIGSERIAL PRIMARY KEY,
    user1_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    user2_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- Match data
    match_score DECIMAL(5,4), -- алгоритм совместимости
    match_reason TEXT, -- объяснение совпадения
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_message_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user1_id, user2_id),
    CHECK (user1_id < user2_id) -- избегаем дубликатов (1,2) и (2,1)
);

CREATE INDEX idx_matches_user1 ON matches(user1_id);
CREATE INDEX idx_matches_user2 ON matches(user2_id);
CREATE INDEX idx_matches_active ON matches(is_active) WHERE is_active = true;
CREATE INDEX idx_matches_created ON matches(created_at);

-- ===================================
-- MESSAGES TABLE
-- ===================================
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT REFERENCES matches(id) ON DELETE CASCADE,
    sender_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- Message content
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text' CHECK (message_type IN ('text', 'photo', 'sticker', 'gif')),
    media_url TEXT, -- для фото/стикеров
    
    -- Status
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_match ON messages(match_id, created_at);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_unread ON messages(match_id, is_read) WHERE is_read = false;

-- ===================================
-- REFERRALS TABLE
-- ===================================
CREATE TABLE referrals (
    id BIGSERIAL PRIMARY KEY,
    referrer_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    referred_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- Referral data
    referral_code VARCHAR(50) UNIQUE NOT NULL,
    bonus_given BOOLEAN DEFAULT false,
    bonus_amount INTEGER DEFAULT 10, -- лайков
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX idx_referrals_referred ON referrals(referred_id);
CREATE INDEX idx_referrals_code ON referrals(referral_code);

-- ===================================
-- PAYMENTS TABLE
-- ===================================
CREATE TABLE payments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- Payment data
    amount_stars INTEGER NOT NULL,
    amount_usd DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Subscription
    subscription_type VARCHAR(20) NOT NULL,
    subscription_duration INTEGER, -- дни
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    telegram_payment_charge_id VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_created ON payments(created_at);

-- ===================================
-- ANALYTICS TABLES
-- ===================================
CREATE TABLE user_analytics (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- Daily stats
    date DATE NOT NULL,
    likes_sent INTEGER DEFAULT 0,
    likes_received INTEGER DEFAULT 0,
    matches_created INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    profile_views INTEGER DEFAULT 0,
    
    -- Engagement
    time_spent_minutes INTEGER DEFAULT 0,
    sessions_count INTEGER DEFAULT 0,
    
    UNIQUE(user_id, date)
);

CREATE INDEX idx_analytics_user_date ON user_analytics(user_id, date);
CREATE INDEX idx_analytics_date ON user_analytics(date);

-- ===================================
-- MODERATION TABLES
-- ===================================
CREATE TABLE moderation_reports (
    id BIGSERIAL PRIMARY KEY,
    reported_user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    reporter_user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- Report data
    reason VARCHAR(50) NOT NULL,
    description TEXT,
    evidence_urls TEXT[], -- скриншоты
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'resolved', 'dismissed')),
    moderator_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

CREATE INDEX idx_reports_reported ON moderation_reports(reported_user_id);
CREATE INDEX idx_reports_reporter ON moderation_reports(reporter_user_id);
CREATE INDEX idx_reports_status ON moderation_reports(status);

-- ===================================
-- TRIGGERS AND FUNCTIONS
-- ===================================

-- Автоматическое обновление updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Обновление статистики при создании матча
CREATE OR REPLACE FUNCTION update_match_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users SET matches_count = matches_count + 1 WHERE id IN (NEW.user1_id, NEW.user2_id);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_match_stats_trigger AFTER INSERT ON matches
    FOR EACH ROW EXECUTE FUNCTION update_match_stats();

-- Обновление статистики лайков
CREATE OR REPLACE FUNCTION update_like_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.action = 'like' OR NEW.action = 'superlike' THEN
        UPDATE users SET likes_given = likes_given + 1 WHERE id = NEW.from_user_id;
        UPDATE users SET likes_received = likes_received + 1 WHERE id = NEW.to_user_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_like_stats_trigger AFTER INSERT ON likes
    FOR EACH ROW EXECUTE FUNCTION update_like_stats();

-- ===================================
-- VIEWS FOR ANALYTICS
-- ===================================

-- View для активных пользователей
CREATE VIEW active_users AS
SELECT 
    id,
    name,
    age,
    gender,
    city,
    is_premium,
    last_active,
    matches_count,
    likes_received,
    CASE 
        WHEN last_active > NOW() - INTERVAL '1 hour' THEN 'online'
        WHEN last_active > NOW() - INTERVAL '1 day' THEN 'recent'
        ELSE 'inactive'
    END as activity_status
FROM users 
WHERE is_active = true;

-- View для популярных профилей
CREATE VIEW popular_profiles AS
SELECT 
    u.id,
    u.name,
    u.age,
    u.city,
    u.matches_count,
    u.likes_received,
    u.views_count,
    CASE 
        WHEN u.likes_received > 0 THEN 
            ROUND((u.matches_count::decimal / u.likes_received) * 100, 2)
        ELSE 0
    END as match_rate
FROM users u
WHERE u.is_active = true
ORDER BY u.likes_received DESC, u.matches_count DESC;

-- ===================================
-- SAMPLE DATA (для тестирования)
-- ===================================

-- Создаем тестовых пользователей
INSERT INTO users (telegram_id, name, age, gender, looking_for, city, bio) VALUES
(123456789, 'Анна', 25, 'female', 'male', 'Москва', 'Люблю путешествия и фотографию'),
(987654321, 'Михаил', 28, 'male', 'female', 'Санкт-Петербург', 'Занимаюсь спортом, увлекаюсь музыкой'),
(555666777, 'Елена', 23, 'female', 'male', 'Москва', 'Студентка, люблю читать и смотреть фильмы'),
(111222333, 'Дмитрий', 30, 'male', 'female', 'Казань', 'Программист, играю в футбол');

-- Добавляем интересы пользователям
INSERT INTO user_interests (user_id, interest_id) VALUES
(1, 1), (1, 2), (1, 4), -- Анна: путешествия, фотография, кино
(2, 7), (2, 15), (2, 17), -- Михаил: фитнес, поп, карьера
(3, 3), (3, 4), (3, 6), -- Елена: чтение, кино, кулинария
(4, 8), (4, 12), (4, 20); -- Дмитрий: йога, танцы, семья
