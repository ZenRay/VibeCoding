"""查询 Pydantic 模型"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class QueryRequest(BaseModel):
    """SQL 查询请求模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    sql: str = Field(
        ...,
        description="SQL 查询语句",
        min_length=1,
        max_length=10000,
    )


class QueryResultColumn(BaseModel):
    """查询结果列信息模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str = Field(..., description="列名")
    data_type: str = Field(..., description="数据类型")


class QueryResult(BaseModel):
    """查询结果模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    columns: list[QueryResultColumn] = Field(..., description="列信息")
    rows: list[dict[str, Any]] = Field(..., description="行数据")
    row_count: int = Field(..., description="返回行数")
    execution_time_ms: int = Field(..., description="执行时间（毫秒）")
    truncated: bool = Field(False, description="是否因 LIMIT 被截断")
    sql: str = Field(..., description="执行的 SQL（可能被修改添加 LIMIT）")


class NaturalLanguageQueryRequest(BaseModel):
    """自然语言查询请求模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    prompt: str = Field(
        ...,
        description="自然语言查询描述",
        min_length=1,
        max_length=1000,
    )


class NaturalLanguageQueryResult(BaseModel):
    """自然语言查询结果模型"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    generated_sql: str = Field(..., description="生成的 SQL")
    result: QueryResult | None = Field(None, description="查询结果（如果执行）")
    generation_time_ms: int = Field(..., description="SQL 生成时间（毫秒）")
