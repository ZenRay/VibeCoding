"""Initial migration

Revision ID: 20260108_000001
Revises: 
Create Date: 2026-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260108_000001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 tickets 表（如果不存在）
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'tickets' not in inspector.get_table_names():
        op.create_table(
            'tickets',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.CheckConstraint("status IN ('pending', 'completed')", name='status_check')
        )
        op.create_index(op.f('ix_tickets_id'), 'tickets', ['id'], unique=False)
        op.create_index(op.f('ix_tickets_title'), 'tickets', ['title'], unique=False)
        op.create_index(op.f('ix_tickets_status'), 'tickets', ['status'], unique=False)
        op.create_index(op.f('ix_tickets_deleted_at'), 'tickets', ['deleted_at'], unique=False)
        op.create_index('idx_tickets_created_at', 'tickets', [sa.text('created_at DESC')], unique=False)
        op.create_index('idx_tickets_active', 'tickets', ['deleted_at'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
        op.create_index('idx_tickets_title_gin', 'tickets', [sa.text("to_tsvector('english', title)")], unique=False, postgresql_using='gin')

    # 创建 tags 表（如果不存在）
    if 'tags' not in inspector.get_table_names():
        op.create_table(
            'tags',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('color', sa.String(length=7), nullable=False, server_default='#6B7280'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
            sa.CheckConstraint("color ~ '^#[0-9A-Fa-f]{6}$'", name='color_format')
        )
        op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)
        op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=False)

    # 创建 ticket_tags 关联表（如果不存在）
    if 'ticket_tags' not in inspector.get_table_names():
        op.create_table(
            'ticket_tags',
            sa.Column('ticket_id', sa.Integer(), nullable=False),
            sa.Column('tag_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('ticket_id', 'tag_id')
        )
        op.create_index(op.f('ix_ticket_tags_ticket_id'), 'ticket_tags', ['ticket_id'], unique=False)
        op.create_index(op.f('ix_ticket_tags_tag_id'), 'ticket_tags', ['tag_id'], unique=False)

    # 创建触发器函数：自动更新 updated_at（如果不存在）
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 创建触发器：tickets 表的 updated_at 自动更新（如果不存在）
    op.execute("""
        DROP TRIGGER IF EXISTS update_tickets_updated_at ON tickets;
        CREATE TRIGGER update_tickets_updated_at 
        BEFORE UPDATE ON tickets
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    # 创建触发器函数：自动设置 completed_at
    op.execute("""
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
    """)

    # 创建触发器：tickets 表的 completed_at 自动设置（如果不存在）
    op.execute("""
        DROP TRIGGER IF EXISTS set_ticket_completed_at ON tickets;
        CREATE TRIGGER set_ticket_completed_at 
        BEFORE UPDATE ON tickets
        FOR EACH ROW
        EXECUTE FUNCTION set_completed_at();
    """)

    # 创建触发器函数：标签名称标准化（英文转大写）
    op.execute("""
        CREATE OR REPLACE FUNCTION normalize_tag_name()
        RETURNS TRIGGER AS $$
        BEGIN
            -- 去除首尾空格，并将英文字符转换为大写
            -- UPPER() 函数只会转换英文字符，中文、数字和特殊字符保持不变
            NEW.name = TRIM(UPPER(NEW.name));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 创建触发器：tags 表插入时标准化名称（如果不存在）
    op.execute("""
        DROP TRIGGER IF EXISTS normalize_tag_name_on_insert ON tags;
        CREATE TRIGGER normalize_tag_name_on_insert
        BEFORE INSERT ON tags
        FOR EACH ROW
        EXECUTE FUNCTION normalize_tag_name();
    """)

    # 创建触发器：tags 表更新时标准化名称（如果不存在）
    op.execute("""
        DROP TRIGGER IF EXISTS normalize_tag_name_on_update ON tags;
        CREATE TRIGGER normalize_tag_name_on_update
        BEFORE UPDATE ON tags
        FOR EACH ROW
        EXECUTE FUNCTION normalize_tag_name();
    """)


def downgrade() -> None:
    # 删除触发器
    op.execute("DROP TRIGGER IF EXISTS normalize_tag_name_on_update ON tags;")
    op.execute("DROP TRIGGER IF EXISTS normalize_tag_name_on_insert ON tags;")
    op.execute("DROP TRIGGER IF EXISTS set_ticket_completed_at ON tickets;")
    op.execute("DROP TRIGGER IF EXISTS update_tickets_updated_at ON tickets;")

    # 删除触发器函数
    op.execute("DROP FUNCTION IF EXISTS normalize_tag_name();")
    op.execute("DROP FUNCTION IF EXISTS set_completed_at();")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    # 删除表
    op.drop_table('ticket_tags')
    op.drop_table('tags')
    op.drop_table('tickets')
