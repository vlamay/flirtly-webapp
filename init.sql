-- init.sql - PostgreSQL initialization script

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
-- (Will be created by SQLAlchemy, but good to have as backup)

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);
CREATE INDEX IF NOT EXISTS idx_users_gender ON users(gender);
CREATE INDEX IF NOT EXISTS idx_users_age ON users(age);
CREATE INDEX IF NOT EXISTS idx_users_looking_for ON users(looking_for);
CREATE INDEX IF NOT EXISTS idx_users_city ON users(city);
CREATE INDEX IF NOT EXISTS idx_users_latitude_longitude ON users(latitude, longitude);

-- Likes table indexes
CREATE INDEX IF NOT EXISTS idx_likes_from_user ON likes(from_user_id);
CREATE INDEX IF NOT EXISTS idx_likes_to_user ON likes(to_user_id);
CREATE INDEX IF NOT EXISTS idx_likes_created_at ON likes(created_at);
CREATE INDEX IF NOT EXISTS idx_likes_mutual ON likes(from_user_id, to_user_id);

-- Matches table indexes
CREATE INDEX IF NOT EXISTS idx_matches_user1 ON matches(user1_id);
CREATE INDEX IF NOT EXISTS idx_matches_user2 ON matches(user2_id);
CREATE INDEX IF NOT EXISTS idx_matches_created_at ON matches(created_at);

-- Referrals table indexes
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_new_user ON referrals(new_user_id);

-- Skips table indexes
CREATE INDEX IF NOT EXISTS idx_skips_from_user ON skips(from_user_id);
CREATE INDEX IF NOT EXISTS idx_skips_to_user ON skips(to_user_id);

-- Profile views table indexes
CREATE INDEX IF NOT EXISTS idx_profile_views_viewer ON profile_views(viewer_id);
CREATE INDEX IF NOT EXISTS idx_profile_views_viewed ON profile_views(viewed_id);
CREATE INDEX IF NOT EXISTS idx_profile_views_created_at ON profile_views(created_at);

-- Create a function to clean up old data (optional)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete old profile views (older than 30 days)
    DELETE FROM profile_views WHERE created_at < NOW() - INTERVAL '30 days';
    
    -- Delete old skips (older than 90 days)
    DELETE FROM skips WHERE created_at < NOW() - INTERVAL '90 days';
    
    -- Delete inactive users (older than 1 year, no activity)
    DELETE FROM users WHERE 
        created_at < NOW() - INTERVAL '1 year' 
        AND last_active < NOW() - INTERVAL '6 months'
        AND is_active = false;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to run cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data();');

-- Insert some test data (optional, for development)
-- INSERT INTO users (telegram_id, username, name, age, gender, looking_for, bio, city, is_active) VALUES
-- (123456789, 'test_user', 'Test User', 25, 'male', 'female', 'Test bio', 'Test City', true);

COMMIT;
