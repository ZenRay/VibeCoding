"""initial migration

Revision ID: 20260110_000001
Revises:
Create Date: 2026-01-10

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260110_000001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 创建 database_connections 表
    op.create_table(
        'database_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('db_type', sa.String(length=50), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('database', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_database_connections_name'), 'database_connections', ['name'], unique=False)

    # 创建 metadata_cache 表
    op.create_table(
        'metadata_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=False),
        sa.Column('version_hash', sa.String(length=64), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('cached_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['database_connections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id')
    )
    op.create_index('idx_metadata_connection', 'metadata_cache', ['connection_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_metadata_connection', table_name='metadata_cache')
    op.drop_table('metadata_cache')
    op.drop_index(op.f('ix_database_connections_name'), table_name='database_connections')
    op.drop_table('database_connections')
