-- ============================================================
-- Medium Test Database: Social Media Platform
-- ============================================================
-- Tables: 15
-- Purpose: Social network with users, posts, comments, likes
-- Complexity: Moderate relationships, polymorphic associations
-- Data Volume: ~10,000 total records
-- ============================================================

-- Custom types
CREATE TYPE content_type AS ENUM ('text', 'image', 'video', 'link');
CREATE TYPE privacy_level AS ENUM ('public', 'friends', 'private');
CREATE TYPE notification_type AS ENUM ('like', 'comment', 'follow', 'mention', 'share');
CREATE TYPE reaction_type AS ENUM ('like', 'love', 'haha', 'wow', 'sad', 'angry');

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),
    cover_photo_url VARCHAR(500),
    location VARCHAR(100),
    website VARCHAR(255),
    birth_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP,
    is_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = true;

-- Posts table
CREATE TABLE posts (
    post_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_type content_type DEFAULT 'text',
    media_url VARCHAR(500),
    privacy privacy_level DEFAULT 'public',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_pinned BOOLEAN DEFAULT false
);

CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_posts_privacy ON posts(privacy);
CREATE INDEX idx_posts_content_type ON posts(content_type);

-- Comments table
CREATE TABLE comments (
    comment_id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(post_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    parent_comment_id INTEGER REFERENCES comments(comment_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_comments_parent ON comments(parent_comment_id);
CREATE INDEX idx_comments_created_at ON comments(created_at DESC);

-- Reactions table
CREATE TABLE reactions (
    reaction_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(post_id) ON DELETE CASCADE,
    comment_id INTEGER REFERENCES comments(comment_id) ON DELETE CASCADE,
    reaction_type reaction_type NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT reaction_target_check CHECK (
        (post_id IS NOT NULL AND comment_id IS NULL) OR 
        (post_id IS NULL AND comment_id IS NOT NULL)
    ),
    CONSTRAINT unique_user_post_reaction UNIQUE (user_id, post_id, reaction_type),
    CONSTRAINT unique_user_comment_reaction UNIQUE (user_id, comment_id, reaction_type)
);

CREATE INDEX idx_reactions_post_id ON reactions(post_id);
CREATE INDEX idx_reactions_comment_id ON reactions(comment_id);
CREATE INDEX idx_reactions_user_id ON reactions(user_id);
CREATE INDEX idx_reactions_type ON reactions(reaction_type);

-- Follows table
CREATE TABLE follows (
    follow_id SERIAL PRIMARY KEY,
    follower_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    following_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT no_self_follow CHECK (follower_id != following_id),
    CONSTRAINT unique_follow UNIQUE (follower_id, following_id)
);

CREATE INDEX idx_follows_follower ON follows(follower_id);
CREATE INDEX idx_follows_following ON follows(following_id);
CREATE INDEX idx_follows_created_at ON follows(created_at DESC);

-- Messages table
CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_recipient ON messages(recipient_id);
CREATE INDEX idx_messages_is_read ON messages(is_read) WHERE is_read = false;
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);

-- Notifications table
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    actor_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type notification_type NOT NULL,
    entity_id INTEGER,
    content TEXT,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_is_read ON notifications(is_read) WHERE is_read = false;
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);

-- Hashtags table
CREATE TABLE hashtags (
    hashtag_id SERIAL PRIMARY KEY,
    tag VARCHAR(100) UNIQUE NOT NULL,
    use_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hashtags_tag ON hashtags(tag);
CREATE INDEX idx_hashtags_use_count ON hashtags(use_count DESC);

-- Post hashtags junction table
CREATE TABLE post_hashtags (
    post_id INTEGER NOT NULL REFERENCES posts(post_id) ON DELETE CASCADE,
    hashtag_id INTEGER NOT NULL REFERENCES hashtags(hashtag_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (post_id, hashtag_id)
);

CREATE INDEX idx_post_hashtags_post ON post_hashtags(post_id);
CREATE INDEX idx_post_hashtags_hashtag ON post_hashtags(hashtag_id);

-- Groups table
CREATE TABLE groups (
    group_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    creator_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    privacy privacy_level DEFAULT 'public',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    member_count INTEGER DEFAULT 1
);

CREATE INDEX idx_groups_creator ON groups(creator_id);
CREATE INDEX idx_groups_privacy ON groups(privacy);
CREATE INDEX idx_groups_created_at ON groups(created_at DESC);

-- Group members table
CREATE TABLE group_members (
    group_id INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    is_admin BOOLEAN DEFAULT false,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, user_id)
);

CREATE INDEX idx_group_members_group ON group_members(group_id);
CREATE INDEX idx_group_members_user ON group_members(user_id);
CREATE INDEX idx_group_members_admin ON group_members(is_admin) WHERE is_admin = true;

-- User settings table
CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true,
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'en',
    privacy_default privacy_level DEFAULT 'public',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User activity log
CREATE TABLE user_activity (
    activity_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_activity_user ON user_activity(user_id);
CREATE INDEX idx_user_activity_type ON user_activity(activity_type);
CREATE INDEX idx_user_activity_created_at ON user_activity(created_at DESC);
CREATE INDEX idx_user_activity_metadata ON user_activity USING gin(metadata);

-- Reported content table
CREATE TABLE reports (
    report_id SERIAL PRIMARY KEY,
    reporter_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    reported_user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    reported_post_id INTEGER REFERENCES posts(post_id) ON DELETE CASCADE,
    reason VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_reports_reporter ON reports(reporter_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);

-- Views
CREATE VIEW user_stats AS
SELECT 
    u.user_id,
    u.username,
    COUNT(DISTINCT p.post_id) AS post_count,
    COUNT(DISTINCT f1.follow_id) AS follower_count,
    COUNT(DISTINCT f2.follow_id) AS following_count,
    COUNT(DISTINCT r.reaction_id) AS reactions_received
FROM users u
LEFT JOIN posts p ON u.user_id = p.user_id
LEFT JOIN follows f1 ON u.user_id = f1.following_id
LEFT JOIN follows f2 ON u.user_id = f2.follower_id
LEFT JOIN reactions r ON p.post_id = r.post_id
GROUP BY u.user_id, u.username;

CREATE VIEW trending_posts AS
SELECT 
    p.post_id,
    p.user_id,
    p.content,
    p.created_at,
    COUNT(DISTINCT r.reaction_id) AS reaction_count,
    COUNT(DISTINCT c.comment_id) AS comment_count,
    (COUNT(DISTINCT r.reaction_id) + COUNT(DISTINCT c.comment_id)) AS engagement_score
FROM posts p
LEFT JOIN reactions r ON p.post_id = r.post_id
LEFT JOIN comments c ON p.post_id = c.post_id
WHERE p.created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
GROUP BY p.post_id, p.user_id, p.content, p.created_at;
