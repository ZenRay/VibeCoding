"""数据库连接 Pydantic 模型"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DatabaseType(str, Enum):
    """支持的数据库类型"""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


class DatabaseConnectionCreate(BaseModel):
    """创建/更新数据库连接的请求模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    url: str = Field(
        ...,
        description="数据库连接 URL",
        examples=["postgresql://user:pass@localhost:5432/mydb"],
    )


class DatabaseConnectionResponse(BaseModel):
    """数据库连接响应模型

    注意：此模型不包含密码字段（安全设计决策）。
    密码仅在 DatabaseConnectionCreate 请求中接收，不在响应中返回。
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str = Field(
        ...,
        description="连接名称/标识符",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    db_type: DatabaseType = Field(..., description="数据库类型")
    host: str | None = Field(None, description="主机名（SQLite 为 null）")
    port: int | None = Field(
        None, description="端口（范围 1-65535，SQLite 为 null）", ge=1, le=65535
    )
    database: str = Field(..., description="数据库名或文件路径")
    created_at: datetime = Field(..., description="创建时间（UTC）")
    updated_at: datetime = Field(..., description="更新时间（UTC）")


class DatabaseListResponse(BaseModel):
    """数据库列表响应模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    databases: list[DatabaseConnectionResponse] = Field(
        default_factory=list,
        description="数据库连接列表",
    )
    total: int = Field(..., description="总数")
