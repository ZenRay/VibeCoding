/** 元数据树形展示组件 */
import React from "react";
import { Tree, Tag, Typography, Tooltip } from "antd";
import { DatabaseMetadata, TableInfo } from "../types/database";

const { Text } = Typography;

interface MetadataTreeProps {
  metadata: DatabaseMetadata;
  onTableSelect?: (tableName: string) => void;
}

const MetadataTree: React.FC<MetadataTreeProps> = ({
  metadata,
  onTableSelect,
}) => {
  const buildTreeData = () => {
    const treeData: any[] = [];

    // 表节点
    if (metadata.tables.length > 0) {
      treeData.push({
        title: (
          <span>
            <Text strong style={{ fontSize: "13px" }}>
              表 ({metadata.tables.length})
            </Text>
          </span>
        ),
        key: "tables",
        children: metadata.tables.map((table) => ({
          title: (
            <Tooltip title={table.name} placement="right">
              <div
                onClick={() => onTableSelect?.(table.name)}
                style={{ cursor: "pointer", lineHeight: "20px" }}
              >
                <Text strong style={{ fontSize: "12px" }}>
                  {table.name}
                </Text>
                {table.rowCount !== null && table.rowCount !== undefined && (
                  <Tag
                    style={{
                      marginLeft: 4,
                      fontSize: "10px",
                      padding: "0 3px",
                      lineHeight: "16px",
                      height: "16px",
                    }}
                    color="blue"
                  >
                    {table.rowCount}
                  </Tag>
                )}
              </div>
            </Tooltip>
          ),
          key: `table-${table.name}`,
          children: table.columns.map((col) => ({
            title: (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "3px",
                  flexWrap: "nowrap",
                  lineHeight: "18px",
                  overflow: "hidden",
                }}
              >
                <Tooltip title={col.name} placement="right">
                  <Text
                    style={{
                      fontSize: "11px",
                      minWidth: "40px",
                      maxWidth: "80px",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      flex: "0 0 auto",
                    }}
                  >
                    {col.name}
                  </Text>
                </Tooltip>
                <Tooltip title={col.dataType} placement="right">
                  <Tag
                    style={{
                      fontSize: "9px",
                      padding: "0 3px",
                      margin: 0,
                      lineHeight: "14px",
                      height: "14px",
                      flex: "0 0 auto",
                    }}
                    color="default"
                  >
                    {col.dataType.length > 10
                      ? col.dataType.substring(0, 10) + "..."
                      : col.dataType}
                  </Tag>
                </Tooltip>
                {col.isPrimaryKey && (
                  <Tooltip title="Primary Key" placement="right">
                    <Tag
                      style={{
                        fontSize: "9px",
                        padding: "0 3px",
                        margin: 0,
                        lineHeight: "14px",
                        height: "14px",
                        flex: "0 0 auto",
                      }}
                      color="red"
                    >
                      PK
                    </Tag>
                  </Tooltip>
                )}
                {!col.isNullable && (
                  <Tooltip title="Not Null" placement="right">
                    <Tag
                      style={{
                        fontSize: "9px",
                        padding: "0 2px",
                        margin: 0,
                        lineHeight: "14px",
                        height: "14px",
                        flex: "0 0 auto",
                      }}
                      color="orange"
                    >
                      NN
                    </Tag>
                  </Tooltip>
                )}
              </div>
            ),
            key: `col-${table.name}-${col.name}`,
            isLeaf: true,
          })),
        })),
      });
    }

    // 视图节点
    if (metadata.views.length > 0) {
      treeData.push({
        title: (
          <span>
            <Text strong style={{ fontSize: "13px" }}>
              视图 ({metadata.views.length})
            </Text>
          </span>
        ),
        key: "views",
        children: metadata.views.map((view) => ({
          title: (
            <Tooltip title={view.name} placement="right">
              <div
                onClick={() => onTableSelect?.(view.name)}
                style={{ cursor: "pointer", lineHeight: "20px" }}
              >
                <Text strong style={{ fontSize: "12px" }}>
                  {view.name}
                </Text>
              </div>
            </Tooltip>
          ),
          key: `view-${view.name}`,
          children: view.columns.map((col) => ({
            title: (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "3px",
                  flexWrap: "nowrap",
                  lineHeight: "18px",
                  overflow: "hidden",
                }}
              >
                <Tooltip title={col.name} placement="right">
                  <Text
                    style={{
                      fontSize: "11px",
                      minWidth: "40px",
                      maxWidth: "80px",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      flex: "0 0 auto",
                    }}
                  >
                    {col.name}
                  </Text>
                </Tooltip>
                <Tooltip title={col.dataType} placement="right">
                  <Tag
                    style={{
                      fontSize: "9px",
                      padding: "0 3px",
                      margin: 0,
                      lineHeight: "14px",
                      height: "14px",
                      flex: "0 0 auto",
                    }}
                    color="default"
                  >
                    {col.dataType.length > 10
                      ? col.dataType.substring(0, 10) + "..."
                      : col.dataType}
                  </Tag>
                </Tooltip>
              </div>
            ),
            key: `col-${view.name}-${col.name}`,
            isLeaf: true,
          })),
        })),
      });
    }

    return treeData;
  };

  return (
    <Tree
      treeData={buildTreeData()}
      defaultExpandAll={false}
      showLine={{ showLeafIcon: false }}
      showIcon={false}
      style={{ fontSize: "12px" }}
    />
  );
};

export default MetadataTree;
