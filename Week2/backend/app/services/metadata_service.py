"""元数据提取服务 - 增强版包含并发互斥锁"""

import hashlib
import json

from sqlalchemy.orm import Session

from app.models.metadata import ColumnInfo, DatabaseMetadata, TableInfo
from app.services.db_service import get_adapter
from app.storage.local_db import LocalStorage
from app.storage.models import DatabaseConnection
from app.utils.error_handler import ErrorCode, create_error_response
from app.utils.locks import get_metadata_lock, is_query_executing


class MetadataService:
    """元数据服务类"""

    @staticmethod
    async def extract_metadata(
        db: Session,
        connection: DatabaseConnection,
        force_refresh: bool = False,
    ) -> DatabaseMetadata:
        """提取数据库元数据 (带并发互斥锁)"""

        # === 并发控制: 检查是否有查询正在执行 ===
        if force_refresh and is_query_executing():
            raise create_error_response(ErrorCode.CONFLICT, "查询执行中,无法刷新元数据")

        # 检查缓存
        if not force_refresh:
            cache = LocalStorage.get_metadata_cache(db, connection.id)
            if cache:
                # 返回缓存的元数据
                metadata_dict = json.loads(cache.metadata_json)
                return DatabaseMetadata(**metadata_dict)

        # === 获取元数据刷新锁 ===
        metadata_lock = get_metadata_lock()
        async with metadata_lock:
            # 提取元数据
            adapter = get_adapter(connection.db_type)
            await adapter.connect(connection.url)

            try:
                raw_metadata = await adapter.get_metadata()

                # 转换为 Pydantic 模型
                tables = [
                    TableInfo(
                        name=table["name"],
                        table_type=table.get("tableType", "table"),
                        columns=[
                            ColumnInfo(
                                name=col["name"],
                                data_type=col.get("dataType", ""),
                                is_nullable=col.get("isNullable", True),
                                is_primary_key=col.get("isPrimaryKey", False),
                                default_value=col.get("defaultValue"),
                                comment=col.get("comment"),
                            )
                            for col in table.get("columns", [])
                        ],
                        row_count=table.get("rowCount"),
                        comment=table.get("comment"),
                    )
                    for table in raw_metadata.get("tables", [])
                ]

                views = [
                    TableInfo(
                        name=view["name"],
                        table_type="view",
                        columns=[
                            ColumnInfo(
                                name=col["name"],
                                data_type=col.get("dataType", ""),
                                is_nullable=col.get("isNullable", True),
                                is_primary_key=col.get("isPrimaryKey", False),
                                default_value=col.get("defaultValue"),
                                comment=col.get("comment"),
                            )
                            for col in view.get("columns", [])
                        ],
                        row_count=view.get("rowCount"),
                        comment=view.get("comment"),
                    )
                    for view in raw_metadata.get("views", [])
                ]

                metadata = DatabaseMetadata(
                    name=connection.name,
                    db_type=connection.db_type,
                    tables=tables,
                    views=views,
                    version_hash=None,  # 将在下面设置
                    cached_at=None,
                    needs_refresh=False,
                )

                # 计算版本哈希 (使用表名列表的 SHA-256)
                table_names = sorted([t.name for t in tables] + [v.name for v in views])
                version_content = json.dumps(
                    {"table_count": len(table_names), "table_names": table_names}
                )
                version_hash = hashlib.sha256(version_content.encode()).hexdigest()
                metadata.version_hash = version_hash

                # 保存到缓存
                LocalStorage.save_metadata_cache(
                    db,
                    connection.id,
                    metadata.model_dump_json(),
                    version_hash,
                )

                return metadata

            finally:
                await adapter.close()

    @staticmethod
    def detect_changes(
        db: Session,
        connection: DatabaseConnection,
    ) -> bool:
        """检测元数据是否已变化 (基于版本哈希)"""
        cache = LocalStorage.get_metadata_cache(db, connection.id)
        if not cache:
            return True  # 没有缓存，需要刷新

        # 这里可以添加更复杂的检测逻辑
        # 例如：定期重新计算哈希并比较
        # 当前实现：总是返回 False（不自动检测，用户手动刷新）
        return False
