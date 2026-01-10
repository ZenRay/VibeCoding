/** 数据库卡片展示组件（首页用，只读） */
import React from "react";
import { useNavigate } from "react-router-dom";
import { List, Card, Tag, Space } from "antd";
import { DatabaseConnectionResponse } from "../types/database";

interface DatabaseCardListProps {
  databases: DatabaseConnectionResponse[];
  loading?: boolean;
}

const DatabaseCardList: React.FC<DatabaseCardListProps> = ({
  databases,
  loading = false,
}) => {
  const navigate = useNavigate();

  const getDbTypeColor = (dbType: string) => {
    switch (dbType) {
      case "postgresql":
        return "blue";
      case "mysql":
        return "orange";
      case "sqlite":
        return "green";
      default:
        return "default";
    }
  };

  return (
    <List
      loading={loading}
      grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4 }}
      dataSource={databases}
      renderItem={(db) => (
        <List.Item>
          <Card
            hoverable
            onClick={() => navigate(`/database/${db.name}`)}
            style={{ cursor: "pointer" }}
          >
            <Space direction="vertical" style={{ width: "100%" }} size="middle">
              <div>
                <Tag
                  color={getDbTypeColor(db.dbType)}
                  style={{ marginBottom: 8 }}
                >
                  {db.dbType}
                </Tag>
                <div
                  style={{
                    fontSize: "18px",
                    fontWeight: "bold",
                    marginBottom: 8,
                  }}
                >
                  {db.name}
                </div>
              </div>

              <div>
                <div style={{ marginBottom: 4 }}>
                  <strong>数据库:</strong> {db.database}
                </div>
                {db.host && (
                  <div style={{ marginBottom: 4 }}>
                    <strong>主机:</strong> {db.host}
                    {db.port && `:${db.port}`}
                  </div>
                )}
              </div>

              <div
                style={{
                  fontSize: "12px",
                  color: "#999",
                  borderTop: "1px solid #f0f0f0",
                  paddingTop: 8,
                }}
              >
                创建于: {new Date(db.createdAt).toLocaleString("zh-CN")}
              </div>
            </Space>
          </Card>
        </List.Item>
      )}
    />
  );
};

export default DatabaseCardList;
