import React, { useState } from 'react';
import { Layout, Typography, Button, Space, Alert } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useDatabases } from '../hooks/useDatabases';
import DatabaseList from '../components/DatabaseList';
import DatabaseForm from '../components/DatabaseForm';
import { DatabaseConnectionResponse } from '../types/database';

const { Header, Content } = Layout;
const { Title } = Typography;

const HomePage: React.FC = () => {
  const {
    databases,
    loading,
    error,
    upsertDatabase,
    deleteDatabase,
  } = useDatabases();

  const [formVisible, setFormVisible] = useState(false);
  const [editingDb, setEditingDb] = useState<DatabaseConnectionResponse | null>(null);

  const handleAdd = () => {
    setEditingDb(null);
    setFormVisible(true);
  };

  const handleEdit = (db: DatabaseConnectionResponse) => {
    setEditingDb(db);
    setFormVisible(true);
  };

  const handleSubmit = async (name: string, url: string) => {
    await upsertDatabase(name, url);
  };

  const handleDelete = async (name: string) => {
    await deleteDatabase(name);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 24px' }}>
        <Title level={3} style={{ color: '#fff', margin: '16px 0' }}>
          数据库查询工具
        </Title>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAdd}
            >
              添加数据库连接
            </Button>
          </Space>

          {error && (
            <Alert
              message="错误"
              description={error}
              type="error"
              showIcon
              closable
            />
          )}

          <DatabaseList
            databases={databases}
            loading={loading}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        </Space>

        <DatabaseForm
          visible={formVisible}
          onCancel={() => {
            setFormVisible(false);
            setEditingDb(null);
          }}
          onSubmit={handleSubmit}
          initialName={editingDb?.name}
          initialUrl={editingDb ? undefined : ''}
        />
      </Content>
    </Layout>
  );
};

export default HomePage;
