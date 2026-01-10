/** 查询历史组件 */
import React, { useState } from "react";
import { List, Typography, Tag, Button } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";

const { Text } = Typography;

interface QueryHistoryItem {
  sql: string;
  result: any;
  error: string | null;
  timestamp: number;
}

interface QueryHistoryProps {
  history: QueryHistoryItem[];
  onSelect: (sql: string) => void;
}

const QueryHistory: React.FC<QueryHistoryProps> = ({ history, onSelect }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  if (history.length === 0) {
    return (
      <div style={{ color: "#999", padding: "16px", textAlign: "center" }}>
        暂无查询历史
      </div>
    );
  }

  return (
    <List
      size="small"
      dataSource={history}
      pagination={{
        current: currentPage,
        pageSize: pageSize,
        total: history.length,
        onChange: (page) => setCurrentPage(page),
        showSizeChanger: false,
        showTotal: (total) => `共 ${total} 条`,
        size: "small",
      }}
      renderItem={(item) => (
        <List.Item>
          <div style={{ width: "100%" }}>
            <div style={{ marginBottom: 8 }}>
              {item.error ? (
                <Tag color="red" icon={<CloseCircleOutlined />}>
                  失败
                </Tag>
              ) : (
                <Tag color="green" icon={<CheckCircleOutlined />}>
                  成功
                </Tag>
              )}
              <Text code style={{ fontSize: "12px" }}>
                {item.sql.length > 80
                  ? `${item.sql.substring(0, 80)}...`
                  : item.sql}
              </Text>
            </div>
            <div style={{ fontSize: "12px", color: "#999" }}>
              {new Date(item.timestamp).toLocaleString("zh-CN")}
            </div>
            <Button
              type="link"
              size="small"
              onClick={() => onSelect(item.sql)}
              style={{ padding: 0, marginTop: 4 }}
            >
              使用此查询
            </Button>
          </div>
        </List.Item>
      )}
    />
  );
};

export default QueryHistory;
