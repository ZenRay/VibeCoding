/** 数据库连接管理 Hook */
import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { databaseService } from '../services/databaseService';
import { DatabaseConnectionResponse } from '../types/database';

export const useDatabases = () => {
  const [databases, setDatabases] = useState<DatabaseConnectionResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载数据库列表
  const loadDatabases = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await databaseService.list();
      setDatabases(response.databases);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载失败';
      setError(errorMessage);
      message.error(`加载数据库列表失败: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // 添加/更新数据库连接
  const upsertDatabase = useCallback(
    async (name: string, url: string) => {
      try {
        await databaseService.upsert(name, { url });
        message.success(`数据库连接 ${name} 已保存`);
        await loadDatabases();
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '保存失败';
        message.error(`保存失败: ${errorMessage}`);
        throw err;
      }
    },
    [loadDatabases]
  );

  // 删除数据库连接
  const deleteDatabase = useCallback(
    async (name: string) => {
      try {
        await databaseService.delete(name);
        message.success(`数据库连接 ${name} 已删除`);
        await loadDatabases();
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '删除失败';
        message.error(`删除失败: ${errorMessage}`);
        throw err;
      }
    },
    [loadDatabases]
  );

  useEffect(() => {
    loadDatabases();
  }, [loadDatabases]);

  return {
    databases,
    loading,
    error,
    loadDatabases,
    upsertDatabase,
    deleteDatabase,
  };
};
