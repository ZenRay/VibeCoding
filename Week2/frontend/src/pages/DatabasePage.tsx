/** 数据库详情页面 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout, Typography, Button, Spin, message, Space, Tabs, Card } from 'antd';
import { ArrowLeftOutlined, ReloadOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { databaseService } from '../services/databaseService';
import { DatabaseMetadata } from '../types/database';
import MetadataTree from '../components/MetadataTree';
import MetadataRefreshBanner from '../components/MetadataRefreshBanner';
import SqlEditor from '../components/SqlEditor';
import QueryResult from '../components/QueryResult';
import QueryHistory from '../components/QueryHistory';
import NaturalLanguageInput from '../components/NaturalLanguageInput';
import { useQuery } from '../hooks/useQuery';
import { queryService } from '../services/queryService';

const { Header, Content } = Layout;
const { Title } = Typography;

const DatabasePage: React.FC = () => {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [metadata, setMetadata] = useState<DatabaseMetadata | null>(null);
  const [loading, setLoading] = useState(false);
  const [needsRefresh, setNeedsRefresh] = useState(false);
  const [sql, setSql] = useState('');

  const { result, loading: queryLoading, error: queryError, history, executeQuery, clearResult } = useQuery(name);
  const [aiLoading, setAiLoading] = useState(false);

  const loadMetadata = async (refresh = false) => {
    if (!name) return;

    setLoading(true);
    try {
      const data = await databaseService.getMetadata(name, refresh);
      setMetadata(data);
      setNeedsRefresh(data.needsRefresh || false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载失败';
      message.error(`加载元数据失败: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetadata();
  }, [name]);

  const handleRefresh = () => {
    loadMetadata(true);
  };

  const handleExecuteQuery = () => {
    if (!sql.trim()) {
      message.warning('请输入 SQL 查询');
      return;
    }
    executeQuery(sql);
  };

  const handleSelectHistory = (selectedSql: string) => {
    setSql(selectedSql);
  };

  const handleGenerateSQL = async (prompt: string): Promise<string> => {
    if (!name) {
      throw new Error('数据库名称无效');
    }

    setAiLoading(true);
    try {
      const result = await queryService.generateFromNaturalLanguage(name, prompt);
      return result.generatedSql;
    } finally {
      setAiLoading(false);
    }
  };

  const handleSqlGenerated = (generatedSql: string) => {
    setSql(generatedSql);
  };

  if (!name) {
    return <div>无效的数据库名称</div>;
  }

  const tabItems = [
    {
      key: 'metadata',
      label: '元数据',
      children: (
        <>
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={loading}
            >
              刷新元数据
            </Button>
          </Space>

          <MetadataRefreshBanner
            visible={needsRefresh}
            onRefresh={handleRefresh}
          />

          {loading && !metadata ? (
            <Spin size="large" />
          ) : metadata ? (
            <MetadataTree metadata={metadata} />
          ) : (
            <div>暂无数据</div>
          )}
        </>
      ),
    },
    {
      key: 'query',
      label: 'SQL 查询',
      children: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Card title="自然语言生成 SQL">
            <NaturalLanguageInput
              onGenerate={handleGenerateSQL}
              onSqlGenerated={handleSqlGenerated}
              loading={aiLoading}
            />
          </Card>

          <Card title="SQL 编辑器">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <SqlEditor value={sql} onChange={(value) => setSql(value || '')} height="200px" />
              <Space>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleExecuteQuery}
                  loading={queryLoading}
                >
                  执行查询
                </Button>
                <Button onClick={clearResult}>清除结果</Button>
              </Space>
            </Space>
          </Card>

          {queryError && (
            <Card>
              <Typography.Text type="danger">{queryError}</Typography.Text>
            </Card>
          )}

          {result && (
            <Card title="查询结果">
              <QueryResult result={result} />
            </Card>
          )}

          {history.length > 0 && (
            <Card title="查询历史">
              <QueryHistory history={history} onSelect={handleSelectHistory} />
            </Card>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 24px' }}>
        <Space>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
            style={{ color: '#fff' }}
          >
            返回
          </Button>
          <Title level={3} style={{ color: '#fff', margin: '16px 0' }}>
            {name}
          </Title>
        </Space>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Tabs items={tabItems} />
      </Content>
    </Layout>
  );
};

export default DatabasePage;
