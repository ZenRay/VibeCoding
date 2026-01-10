/** 数据库连接列表组件 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { List, Card, Button, Popconfirm, Tag, Space } from 'antd';
import { DeleteOutlined, EditOutlined, EyeOutlined } from '@ant-design/icons';
import { DatabaseConnectionResponse } from '../types/database';

interface DatabaseListProps {
  databases: DatabaseConnectionResponse[];
  loading?: boolean;
  onEdit: (db: DatabaseConnectionResponse) => void;
  onDelete: (name: string) => void;
}

const DatabaseList: React.FC<DatabaseListProps> = ({
  databases,
  loading = false,
  onEdit,
  onDelete,
}) => {
  const navigate = useNavigate();
  const getDbTypeColor = (dbType: string) => {
    switch (dbType) {
      case 'postgresql':
        return 'blue';
      case 'mysql':
        return 'orange';
      case 'sqlite':
        return 'green';
      default:
        return 'default';
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
            title={
              <Space>
                <Tag color={getDbTypeColor(db.dbType)}>{db.dbType}</Tag>
                {db.name}
              </Space>
            }
            extra={
              <Space>
                <Button
                  type="text"
                  icon={<EyeOutlined />}
                  onClick={() => navigate(`/database/${db.name}`)}
                />
                <Button
                  type="text"
                  icon={<EditOutlined />}
                  onClick={() => onEdit(db)}
                />
                <Popconfirm
                  title={`确认删除连接 '${db.name}'？`}
                  description="该操作无法撤销"
                  onConfirm={() => onDelete(db.name)}
                  okText="确认"
                  cancelText="取消"
                >
                  <Button type="text" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            }
          >
            <div>
              <div>
                <strong>数据库:</strong> {db.database}
              </div>
              {db.host && (
                <div>
                  <strong>主机:</strong> {db.host}
                  {db.port && `:${db.port}`}
                </div>
              )}
              <div style={{ marginTop: 8, fontSize: '12px', color: '#999' }}>
                创建于: {new Date(db.createdAt).toLocaleString('zh-CN')}
              </div>
            </div>
          </Card>
        </List.Item>
      )}
    />
  );
};

export default DatabaseList;
