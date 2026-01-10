import React, { useState } from "react";
import {
  Layout,
  Typography,
  Button,
  Space,
  Card,
  Empty,
  message,
  Alert,
  Drawer,
} from "antd";
import {
  DatabaseOutlined,
  ReloadOutlined,
  PlusOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { useDatabases } from "../hooks/useDatabases";
import DatabaseCardList from "../components/DatabaseCardList";
import DatabaseList from "../components/DatabaseList";
import DatabaseForm from "../components/DatabaseForm";
import {
  DatabaseConnectionResponse,
  DatabaseConnectionWithUrl,
} from "../types/database";
import { databaseService } from "../services/databaseService";

const { Header, Content } = Layout;
const { Title } = Typography;

const HomePage: React.FC = () => {
  const {
    databases,
    loading,
    error,
    upsertDatabase,
    deleteDatabase,
    loadDatabases,
  } = useDatabases();

  const [formVisible, setFormVisible] = useState(false);
  const [editingDb, setEditingDb] = useState<DatabaseConnectionWithUrl | null>(
    null,
  );
  const [refreshing, setRefreshing] = useState(false);
  const [manageDrawerVisible, setManageDrawerVisible] = useState(false);

  const handleAdd = () => {
    setEditingDb(null);
    setFormVisible(true);
  };

  const handleEdit = async (db: DatabaseConnectionResponse) => {
    try {
      // 获取包含完整 URL 的连接信息
      const dbWithUrl = await databaseService.getWithUrl(db.name);
      setEditingDb(dbWithUrl);
      setFormVisible(true);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "获取连接信息失败";
      message.error(`获取连接信息失败: ${errorMessage}`);
    }
  };

  const handleSubmit = async (name: string, url: string) => {
    await upsertDatabase(name, url);
  };

  const handleDelete = async (name: string) => {
    await deleteDatabase(name);
  };

  const handleRefreshAllSchemas = async () => {
    if (databases.length === 0) {
      message.warning("没有可刷新的数据库连接");
      return;
    }

    setRefreshing(true);
    try {
      const results = await Promise.allSettled(
        databases.map((db) => databaseService.getMetadata(db.name, true)),
      );

      const successCount = results.filter(
        (r) => r.status === "fulfilled",
      ).length;
      const failCount = results.filter((r) => r.status === "rejected").length;

      if (failCount === 0) {
        message.success(`成功刷新 ${successCount} 个数据库的元数据`);
      } else {
        message.warning(
          `刷新完成: 成功 ${successCount} 个, 失败 ${failCount} 个`,
        );
      }
    } catch (err) {
      message.error("刷新失败");
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header
        style={{
          background: "#001529",
          padding: "0 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Title level={3} style={{ color: "#fff", margin: "16px 0" }}>
          数据库查询工具
        </Title>
        <Space size="middle">
          <Button
            icon={<SettingOutlined />}
            onClick={() => setManageDrawerVisible(true)}
          >
            管理数据库
          </Button>
          <Button
            type="text"
            icon={<ReloadOutlined spin={refreshing} />}
            onClick={handleRefreshAllSchemas}
            loading={refreshing}
            style={{ color: "#fff" }}
          >
            刷新 Schema
          </Button>
        </Space>
      </Header>
      <Content style={{ padding: "24px" }}>
        <Space direction="vertical" style={{ width: "100%" }} size="large">
          {error && (
            <Alert
              message="错误"
              description={error}
              type="error"
              showIcon
              closable
            />
          )}

          {databases.length === 0 && !loading ? (
            <Card style={{ textAlign: "center", padding: "48px 24px" }}>
              <Empty
                image={
                  <DatabaseOutlined
                    style={{ fontSize: "64px", color: "#ccc" }}
                  />
                }
                description={
                  <Space direction="vertical" size="middle">
                    <Title
                      level={4}
                      style={{ color: "#999", marginTop: "16px" }}
                    >
                      还没有数据库连接
                    </Title>
                    <p style={{ color: "#999" }}>
                      点击右上角的"管理数据库"按钮创建第一个连接
                    </p>
                  </Space>
                }
              >
                <Button
                  type="primary"
                  size="large"
                  icon={<SettingOutlined />}
                  onClick={() => setManageDrawerVisible(true)}
                >
                  管理数据库
                </Button>
              </Empty>
            </Card>
          ) : (
            <DatabaseCardList databases={databases} loading={loading} />
          )}
        </Space>
      </Content>

      {/* 管理数据库抽屉 */}
      <Drawer
        title={
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>管理数据库</span>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAdd}
              size="small"
            >
              添加数据库
            </Button>
          </div>
        }
        placement="right"
        width={720}
        onClose={() => setManageDrawerVisible(false)}
        open={manageDrawerVisible}
      >
        <DatabaseList
          databases={databases}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </Drawer>

      <DatabaseForm
        visible={formVisible}
        onCancel={() => {
          setFormVisible(false);
          setEditingDb(null);
        }}
        onSubmit={handleSubmit}
        initialName={editingDb?.name}
        initialUrl={editingDb?.url || ""}
      />
    </Layout>
  );
};

export default HomePage;
