/** 元数据树形展示组件 */
import React from 'react';
import { Tree, Tag, Typography } from 'antd';
import { DatabaseMetadata, TableInfo } from '../types/database';

const { Text } = Typography;

interface MetadataTreeProps {
  metadata: DatabaseMetadata;
  onTableSelect?: (tableName: string) => void;
}

const MetadataTree: React.FC<MetadataTreeProps> = ({ metadata, onTableSelect }) => {
  const buildTreeData = () => {
    const treeData: any[] = [];

    // 表节点
    if (metadata.tables.length > 0) {
      treeData.push({
        title: (
          <span>
            <Tag color="blue">表</Tag>
            <Text strong>Tables ({metadata.tables.length})</Text>
          </span>
        ),
        key: 'tables',
        children: metadata.tables.map((table) => ({
          title: (
            <span onClick={() => onTableSelect?.(table.name)}>
              {table.name}
              {table.columns.length > 0 && (
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  ({table.columns.length} 列)
                </Text>
              )}
            </span>
          ),
          key: `table-${table.name}`,
          children: table.columns.map((col) => ({
            title: (
              <span>
                <Text code>{col.name}</Text>
                <Tag style={{ marginLeft: 8 }}>{col.dataType}</Tag>
                {col.isNullable && <Tag color="default">NULL</Tag>}
                {col.isPrimaryKey && <Tag color="red">PK</Tag>}
              </span>
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
            <Tag color="green">视图</Tag>
            <Text strong>Views ({metadata.views.length})</Text>
          </span>
        ),
        key: 'views',
        children: metadata.views.map((view) => ({
          title: (
            <span onClick={() => onTableSelect?.(view.name)}>
              {view.name}
              {view.columns.length > 0 && (
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  ({view.columns.length} 列)
                </Text>
              )}
            </span>
          ),
          key: `view-${view.name}`,
          children: view.columns.map((col) => ({
            title: (
              <span>
                <Text code>{col.name}</Text>
                <Tag style={{ marginLeft: 8 }}>{col.dataType}</Tag>
                {col.isNullable && <Tag color="default">NULL</Tag>}
              </span>
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
      showLine
      showIcon={false}
    />
  );
};

export default MetadataTree;
