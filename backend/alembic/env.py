"""Alembic 环境配置"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# 导入应用配置和模型
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.database import Base
from app.models import Ticket, Tag, TicketTag  # noqa: F401

# 这是 Alembic Config 对象，提供对 .ini 文件中值的访问
config = context.config

# 从环境变量或配置文件读取数据库 URL
config.set_main_option("sqlalchemy.url", settings.database_url)

# 解释日志配置（如果提供了）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型元数据，以便 'autogenerate' 支持
target_metadata = Base.metadata

# 其他从 config 获取的值，由 env.py 定义
# ... 等等


def run_migrations_offline() -> None:
    """在 'offline' 模式下运行迁移。

    这将配置上下文，只使用 URL 而不是 Engine，尽管 Engine 在这里也可以接受。
    通过跳过 Engine 的创建，我们甚至不需要 DBAPI 可用。

    调用 context.execute() 来发出字符串到脚本输出。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在 'online' 模式下运行迁移。

    在这种情况下，我们需要创建一个 Engine 并将连接与上下文关联。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
