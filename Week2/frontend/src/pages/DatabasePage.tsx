/** 数据库详情页面 */
import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Layout,
  Typography,
  Button,
  Spin,
  message,
  Space,
  Card,
  Menu,
  Tag,
  Statistic,
  Row,
  Col,
} from "antd";
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import { databaseService } from "../services/databaseService";
import {
  DatabaseMetadata,
  DatabaseConnectionResponse,
} from "../types/database";
import { useDatabases } from "../hooks/useDatabases";
import MetadataTree from "../components/MetadataTree";
import MetadataRefreshBanner from "../components/MetadataRefreshBanner";
import SqlEditor from "../components/SqlEditor";
import QueryResult from "../components/QueryResult";
import QueryHistory from "../components/QueryHistory";
import { useQuery } from "../hooks/useQuery";

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;

const DatabasePage: React.FC = () => {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const { databases } = useDatabases();
  const [metadata, setMetadata] = useState<DatabaseMetadata | null>(null);
  const [loading, setLoading] = useState(false);
  const [needsRefresh, setNeedsRefresh] = useState(false);
  const [sql, setSql] = useState("");
  const [resultRowCount, setResultRowCount] = useState(0);
  const [showHistory, setShowHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<"result" | "history">("result");

  const {
    result,
    loading: queryLoading,
    error: queryError,
    history,
    executeQuery,
    clearResult,
  } = useQuery(name);

  const loadMetadata = async (refresh = false) => {
    if (!name) return;

    setLoading(true);
    try {
      const data = await databaseService.getMetadata(name, refresh);
      setMetadata(data);
      setNeedsRefresh(data.needsRefresh || false);

      // 如果是刷新操作，显示成功提示
      if (refresh) {
        message.success({
          content: `元数据刷新成功! 表: ${data.tables?.length || 0}, 视图: ${data.views?.length || 0}`,
          key: "refresh",
          duration: 3,
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "加载失败";

      // 如果是刷新操作，使用特定的 key 更新消息
      if (refresh) {
        message.error({
          content: `元数据刷新失败: ${errorMessage}`,
          key: "refresh",
          duration: 5,
        });
      } else {
        message.error(`加载元数据失败: ${errorMessage}`);
      }
    } finally {
      setLoading(false);
    }
  };

  // 监听 name 变化，重新加载元数据
  useEffect(() => {
    loadMetadata();
    // 切换数据库时重置结果行数
    setResultRowCount(0);
  }, [name]);

  // 监听查询结果变化，更新行数
  useEffect(() => {
    if (result) {
      setResultRowCount(result.rowCount || 0);
      // 有新结果时，如果显示历史则切换到结果标签
      if (showHistory) {
        setActiveTab("result");
      }
    }
  }, [result, showHistory]);

  const handleRefresh = () => {
    loadMetadata(true);
    message.loading({ content: "正在刷新元数据...", key: "refresh" });
  };

  const handleExecuteQuery = () => {
    if (!sql.trim()) {
      message.warning("请输入 SQL 查询");
      return;
    }
    executeQuery(sql);
  };

  const handleSelectHistory = (selectedSql: string) => {
    setSql(selectedSql);
    // 选择历史后可以关闭历史面板
    setShowHistory(false);
  };

  const handleToggleHistory = () => {
    setShowHistory(!showHistory);
    if (!showHistory) {
      setActiveTab("history");
    }
  };

  const handleClearResult = () => {
    clearResult();
    setResultRowCount(0);
    // 如果当前显示历史，保持显示历史
    if (showHistory) {
      setActiveTab("history");
    }
  };

  const handleCloseHistory = () => {
    setShowHistory(false);
    // 如果有查询结果，切换到结果标签
    if (result) {
      setActiveTab("result");
    }
  };

  const handleDatabaseSelect = (dbName: string) => {
    navigate(`/database/${dbName}`);
  };

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

  if (!name) {
    return <div>无效的数据库名称</div>;
  }

  return (
    <Layout style={{ minHeight: "100vh" }}>
      {/* Header */}
      <Header
        style={{
          background: "#001529",
          padding: "0 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Space>
          <Text style={{ color: "#fff", fontSize: "18px", fontWeight: "bold" }}>
            DB Query Tool
          </Text>
        </Space>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/")}>
            返回
          </Button>
        </Space>
      </Header>

      <Layout>
        {/* Left Sidebar - Database List */}
        <Sider
          width={200}
          style={{
            background: "#fff",
            borderRight: "1px solid #f0f0f0",
            overflow: "auto",
            height: "calc(100vh - 64px)",
          }}
        >
          <div style={{ padding: "16px", borderBottom: "1px solid #f0f0f0" }}>
            <Button
              type="primary"
              icon={<DatabaseOutlined />}
              onClick={() => navigate("/")}
              block
            >
              添加数据库
            </Button>
          </div>

          <Menu
            mode="inline"
            selectedKeys={[name || ""]}
            style={{ border: "none" }}
          >
            {databases.map((db) => (
              <Menu.Item
                key={db.name}
                icon={<DatabaseOutlined />}
                onClick={() => handleDatabaseSelect(db.name)}
                style={{
                  height: "auto",
                  lineHeight: "normal",
                  padding: "12px 16px",
                }}
              >
                <Space direction="vertical" size={4} style={{ width: "100%" }}>
                  <Space>
                    <Tag
                      color={getDbTypeColor(db.dbType)}
                      style={{ margin: 0 }}
                    >
                      {db.dbType}
                    </Tag>
                  </Space>
                  <Text strong style={{ fontSize: "14px" }}>
                    {db.name}
                  </Text>
                  <Text type="secondary" style={{ fontSize: "12px" }}>
                    {db.database}
                  </Text>
                </Space>
              </Menu.Item>
            ))}
          </Menu>
        </Sider>

        {/* Middle Section - Schema */}
        <Sider
          width={300}
          style={{
            background: "#fff",
            borderRight: "1px solid #f0f0f0",
            overflow: "hidden",
            height: "calc(100vh - 64px)",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              padding: "16px",
              overflow: "hidden",
            }}
          >
            {/* Schema Tree */}
            <Card
              title="Schema"
              size="small"
              bodyStyle={{
                padding: "8px",
                height: "calc(100% - 40px)",
                overflow: "auto",
              }}
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
              }}
              extra={
                <Button
                  size="small"
                  icon={<ReloadOutlined spin={loading} />}
                  onClick={handleRefresh}
                  loading={loading}
                >
                  刷新
                </Button>
              }
            >
              <MetadataRefreshBanner
                visible={needsRefresh}
                onRefresh={handleRefresh}
              />

              {loading && !metadata ? (
                <div style={{ textAlign: "center", padding: "24px" }}>
                  <Spin />
                </div>
              ) : metadata ? (
                <MetadataTree metadata={metadata} />
              ) : (
                <div
                  style={{
                    textAlign: "center",
                    padding: "24px",
                    color: "#999",
                    fontSize: "12px",
                  }}
                >
                  暂无数据
                </div>
              )}
            </Card>
          </div>
        </Sider>

        {/* Right Section - SQL Editor and Results */}
        <Layout style={{ background: "#fff" }}>
          <Content
            style={{
              padding: "16px",
              height: "calc(100vh - 64px)",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                gap: "16px",
              }}
            >
              {/* Statistics and SQL Editor Container */}
              <div
                style={{
                  display: "flex",
                  gap: "16px",
                  alignItems: "flex-start",
                }}
              >
                {/* Statistics Column - 四个统计卡片 */}
                <div
                  style={{
                    width: "200px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  {/* 表数量 */}
                  <Card size="small" bodyStyle={{ padding: "12px" }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        height: "38px",
                      }}
                    >
                      <span
                        style={{
                          color: "rgba(0, 0, 0, 0.65)",
                          fontSize: "14px",
                        }}
                      >
                        表数量
                      </span>
                      <span
                        style={{
                          fontSize: "24px",
                          fontWeight: 600,
                          color: "#1890ff",
                        }}
                      >
                        {metadata?.tables?.length || 0}
                      </span>
                    </div>
                  </Card>

                  {/* 视图数量 */}
                  <Card size="small" bodyStyle={{ padding: "12px" }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        height: "38px",
                      }}
                    >
                      <span
                        style={{
                          color: "rgba(0, 0, 0, 0.65)",
                          fontSize: "14px",
                        }}
                      >
                        视图数量
                      </span>
                      <span
                        style={{
                          fontSize: "24px",
                          fontWeight: 600,
                          color: "#52c41a",
                        }}
                      >
                        {metadata?.views?.length || 0}
                      </span>
                    </div>
                  </Card>

                  {/* 返回行数 */}
                  <Card size="small" bodyStyle={{ padding: "12px" }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        height: "38px",
                      }}
                    >
                      <span
                        style={{
                          color: "rgba(0, 0, 0, 0.65)",
                          fontSize: "14px",
                        }}
                      >
                        返回行数
                      </span>
                      <span
                        style={{
                          fontSize: "24px",
                          fontWeight: 600,
                          color: "#fa8c16",
                        }}
                      >
                        {resultRowCount}
                      </span>
                    </div>
                  </Card>

                  {/* 查询历史 - 两行布局 */}
                  <Card size="small" bodyStyle={{ padding: "12px" }}>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      {/* 第一行：标题和数量 */}
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          height: "38px",
                        }}
                      >
                        <span
                          style={{
                            color: "rgba(0, 0, 0, 0.65)",
                            fontSize: "14px",
                          }}
                        >
                          查询历史
                        </span>
                        <span
                          style={{
                            fontSize: "24px",
                            fontWeight: 600,
                            color: "#722ed1",
                          }}
                        >
                          {history.length}
                        </span>
                      </div>

                      {/* 第二行：交互按钮 */}
                      {history.length > 0 && (
                        <div
                          style={{
                            paddingTop: "8px",
                            borderTop: "1px solid #f0f0f0",
                            marginTop: "8px",
                          }}
                        >
                          <Button
                            type="link"
                            size="small"
                            onClick={handleToggleHistory}
                            block
                            style={{
                              padding: 0,
                              height: "22px",
                              fontSize: "12px",
                            }}
                          >
                            {showHistory ? "关闭历史" : "查看历史"}
                          </Button>
                        </div>
                      )}
                    </div>
                  </Card>
                </div>

                {/* SQL Editor - Match left column height */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <Card
                    title="SQL 编辑器"
                    size="small"
                    bodyStyle={{ padding: "8px" }}
                    extra={
                      <Space>
                        <Button
                          type="primary"
                          icon={<PlayCircleOutlined />}
                          onClick={handleExecuteQuery}
                          loading={queryLoading}
                        >
                          执行
                        </Button>
                        <Button onClick={handleClearResult}>清除结果</Button>
                      </Space>
                    }
                  >
                    {/*
                      左侧4个卡片精确计算：
                      - 前3个卡片：padding 12px*2 + 内容高度 38px = 62px，共 62px * 3 = 186px
                      - 查询历史卡片：padding 12px*2 + 内容 38px + 按钮区 (8+1+8+22) 39px = 101px
                      - 4个卡片总高：186px + 101px = 287px
                      - 3个间距：8px * 3 = 24px
                      - 总高度：287px + 24px = 311px

                      右侧卡片 size="small" 标题栏约 40px
                      编辑器内容区：311px - 40px = 271px
                    */}
                    <div style={{ height: "271px" }}>
                      <SqlEditor
                        value={sql}
                        onChange={(value) => setSql(value || "")}
                        height="271px"
                      />
                    </div>
                  </Card>
                </div>
              </div>

              {/* Query Error */}
              {queryError && (
                <Card size="small">
                  <Typography.Text type="danger">{queryError}</Typography.Text>
                </Card>
              )}

              {/* Query Result and History with Tabs - 填充剩余空间 */}
              {(result || showHistory) && (
                <Card
                  size="small"
                  style={{
                    flex: 1, // 填充剩余空间
                    display: "flex",
                    flexDirection: "column",
                    overflow: "hidden",
                    minHeight: 0,
                  }}
                  bodyStyle={{
                    flex: 1,
                    overflow: "auto", // 内容区域滚动
                    padding: "16px",
                    minHeight: 0,
                  }}
                  tabList={
                    result && showHistory
                      ? [
                          {
                            key: "result",
                            tab: `查询结果 (${result.rowCount || 0} 行)`,
                          },
                          {
                            key: "history",
                            tab: `查询历史 (${history.length} 条)`,
                          },
                        ]
                      : undefined
                  }
                  activeTabKey={activeTab}
                  onTabChange={(key) =>
                    setActiveTab(key as "result" | "history")
                  }
                  tabBarExtraContent={
                    // 只在有标签页且当前显示历史标签时显示关闭按钮
                    showHistory && result && activeTab === "history" ? (
                      <Button
                        size="small"
                        onClick={handleCloseHistory}
                        style={{ marginTop: 4 }}
                      >
                        关闭历史
                      </Button>
                    ) : null
                  }
                  title={
                    // 没有标签页时显示标题
                    !result && showHistory
                      ? "查询历史"
                      : result && !showHistory
                        ? `查询结果 - 共 ${result.rowCount || 0} 行`
                        : undefined
                  }
                  extra={
                    // 只在没有标签页但显示历史时,在标题旁显示关闭按钮
                    !result && showHistory ? (
                      <Button size="small" onClick={handleCloseHistory}>
                        关闭历史
                      </Button>
                    ) : null
                  }
                >
                  {!result && !showHistory ? null : (
                    <>
                      {/* 只有结果时 */}
                      {result && !showHistory && (
                        <QueryResult result={result} />
                      )}

                      {/* 只有历史时 */}
                      {!result && showHistory && (
                        <QueryHistory
                          history={history}
                          onSelect={handleSelectHistory}
                        />
                      )}

                      {/* 同时有结果和历史时，显示标签页 */}
                      {result && showHistory && (
                        <>
                          {activeTab === "result" && (
                            <QueryResult result={result} />
                          )}
                          {activeTab === "history" && (
                            <QueryHistory
                              history={history}
                              onSelect={handleSelectHistory}
                            />
                          )}
                        </>
                      )}
                    </>
                  )}
                </Card>
              )}
            </div>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default DatabasePage;
