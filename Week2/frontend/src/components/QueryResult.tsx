/** 查询结果表格组件 */
import React from "react";
import { Table, Typography, Tag, Space } from "antd";
import { QueryResult as QueryResultType } from "../types/query";
import { ExportButton } from "./export/ExportButton";

const { Text } = Typography;

interface QueryResultProps {
  result: QueryResultType;
}

const QueryResult: React.FC<QueryResultProps> = ({ result }) => {
  // 处理 NULL 值显示
  const renderCell = (value: unknown) => {
    if (value === null || value === undefined) {
      return <span className="null-value">null</span>;
    }

    // 处理大文本截断
    const strValue = String(value);
    if (strValue.length > 100) {
      return (
        <span title={strValue} className="cell-truncate">
          {strValue.substring(0, 100)}...
        </span>
      );
    }

    // 处理二进制数据
    if (
      value instanceof Uint8Array ||
      (typeof value === "string" && value.startsWith("[BINARY]"))
    ) {
      return <Text code>[BINARY]</Text>;
    }

    return strValue;
  };

  // 构建表格列
  const columns = result.columns.map((col) => ({
    title: (
      <Space>
        <Text strong>{col.name}</Text>
        <Tag>{col.dataType}</Tag>
      </Space>
    ),
    dataIndex: col.name,
    key: col.name,
    render: renderCell,
    ellipsis: true,
  }));

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          <Text>
            返回 <Text strong>{result.rowCount}</Text> 行
          </Text>
          <Text type="secondary">
            执行时间: <Text strong>{result.executionTimeMs}</Text> ms
          </Text>
          {result.truncated && <Tag color="orange">结果已截断（LIMIT 1000）</Tag>}
        </Space>

        <ExportButton
          queryResult={result}
          size="small"
        />
      </div>

      {result.rowCount === 0 ? (
        <div style={{ textAlign: "center", padding: "40px", color: "#999" }}>
          无结果
        </div>
      ) : (
        <Table
          columns={columns}
          dataSource={result.rows.map((row, index) => ({ ...row, key: index }))}
          pagination={{
            pageSize: 50,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          scroll={{ x: "max-content" }}
        />
      )}
    </div>
  );
};

export default QueryResult;
