"""元数据 Pydantic 模型"""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ColumnInfo(BaseModel):
    """列信息模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str = Field(..., description="列名")
    data_type: str = Field(..., description="数据类型")
    is_nullable: bool = Field(True, description="是否可为空")
    is_primary_key: bool = Field(False, description="是否为主键")
    default_value: str | None = Field(None, description="默认值")
    comment: str | None = Field(None, description="列注释")


class TableInfo(BaseModel):
    """表/视图信息模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str = Field(..., description="表名")
    table_type: str = Field("table", description="类型: table 或 view")
    columns: list[ColumnInfo] = Field(default_factory=list, description="列列表")
    row_count: int | None = Field(None, description="估计行数")
    comment: str | None = Field(None, description="表注释")


class DatabaseMetadata(BaseModel):
    """数据库元数据模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str = Field(..., description="数据库名")
    db_type: str = Field(..., description="数据库类型")
    tables: list[TableInfo] = Field(default_factory=list, description="表列表")
    views: list[TableInfo] = Field(default_factory=list, description="视图列表")
    version_hash: str | None = Field(None, description="元数据版本哈希")
    cached_at: str | None = Field(None, description="缓存时间")
    needs_refresh: bool = Field(False, description="是否需要刷新")
    warnings: list[str] = Field(default_factory=list, description="提取时的警告信息")
