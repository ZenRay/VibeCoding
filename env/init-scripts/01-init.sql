-- 初始化数据库脚本

-- 创建 tickets 表
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT status_check CHECK (status IN ('pending', 'completed'))
);

-- 创建 tags 表
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT '#6B7280',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT color_format CHECK (color ~ '^#[0-9A-Fa-f]{6}$')
);

-- 创建 ticket_tags 关联表
CREATE TABLE IF NOT EXISTS ticket_tags (
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (ticket_id, tag_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_deleted_at ON tickets(deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tickets_active ON tickets(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tickets_title ON tickets USING gin(to_tsvector('english', title));
-- tags 表的 name 字段已经设置了 UNIQUE 约束，会自动创建唯一索引
CREATE INDEX IF NOT EXISTS idx_ticket_tags_ticket_id ON ticket_tags(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_tags_tag_id ON ticket_tags(tag_id);

-- 创建触发器函数：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器：tickets 表的 updated_at 自动更新
DROP TRIGGER IF EXISTS update_tickets_updated_at ON tickets;
CREATE TRIGGER update_tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 创建触发器函数：自动设置 completed_at
CREATE OR REPLACE FUNCTION set_completed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        NEW.completed_at = NOW();
    ELSIF NEW.status = 'pending' THEN
        NEW.completed_at = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器：tickets 表的 completed_at 自动设置
DROP TRIGGER IF EXISTS set_ticket_completed_at ON tickets;
CREATE TRIGGER set_ticket_completed_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION set_completed_at();

-- 创建触发器函数：标签名称标准化（英文转大写）
CREATE OR REPLACE FUNCTION normalize_tag_name()
RETURNS TRIGGER AS $$
BEGIN
    -- 去除首尾空格，并将英文字符转换为大写
    -- UPPER() 函数只会转换英文字符，中文、数字和特殊字符保持不变
    NEW.name = TRIM(UPPER(NEW.name));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器：tags 表插入时标准化名称
DROP TRIGGER IF EXISTS normalize_tag_name_on_insert ON tags;
CREATE TRIGGER normalize_tag_name_on_insert
    BEFORE INSERT ON tags
    FOR EACH ROW
    EXECUTE FUNCTION normalize_tag_name();

-- 创建触发器：tags 表更新时标准化名称
DROP TRIGGER IF EXISTS normalize_tag_name_on_update ON tags;
CREATE TRIGGER normalize_tag_name_on_update
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION normalize_tag_name();

-- 插入一些示例标签数据
-- 注意：触发器会自动将英文字符转换为大写
INSERT INTO tags (name, color) VALUES
    ('BACKEND后端', '#3B82F6'),
    ('FRONTEND前端', '#10B981'),
    ('DATABASE数据库', '#8B5CF6'),
    ('BUG', '#EF4444'),
    ('FEATURE功能', '#06B6D4'),
    ('OPTIMIZE优化', '#F59E0B')
ON CONFLICT (name) DO NOTHING;

-- 插入一些示例 Ticket 数据
INSERT INTO tickets (title, description, status) VALUES
    ('实现用户认证功能', '添加 JWT 认证机制，包括登录、注册和令牌刷新', 'pending'),
    ('优化数据库查询性能', '添加必要的索引，优化慢查询', 'pending'),
    ('修复标签删除的 Bug', '删除标签时未正确清理关联关系', 'completed')
ON CONFLICT DO NOTHING;

-- 为示例 Ticket 添加标签
INSERT INTO ticket_tags (ticket_id, tag_id)
SELECT 1, id FROM tags WHERE name = 'BACKEND后端'
ON CONFLICT DO NOTHING;

INSERT INTO ticket_tags (ticket_id, tag_id)
SELECT 1, id FROM tags WHERE name = 'FEATURE功能'
ON CONFLICT DO NOTHING;

INSERT INTO ticket_tags (ticket_id, tag_id)
SELECT 2, id FROM tags WHERE name = 'DATABASE数据库'
ON CONFLICT DO NOTHING;

INSERT INTO ticket_tags (ticket_id, tag_id)
SELECT 2, id FROM tags WHERE name = 'OPTIMIZE优化'
ON CONFLICT DO NOTHING;

INSERT INTO ticket_tags (ticket_id, tag_id)
SELECT 3, id FROM tags WHERE name = 'BUG'
ON CONFLICT DO NOTHING;
