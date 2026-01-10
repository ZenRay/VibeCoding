/** 查询执行 Hook */
import { useState, useCallback } from "react";
import { message } from "antd";
import { queryService } from "../services/queryService";
import { QueryResult } from "../types/query";

interface QueryHistoryItem {
  sql: string;
  result: QueryResult | null;
  error: string | null;
  timestamp: number;
}

export const useQuery = (dbName: string | undefined) => {
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);

  const executeQuery = useCallback(
    async (sql: string) => {
      if (!dbName) {
        message.error("请先选择数据库");
        return;
      }

      setLoading(true);
      setError(null);
      const timestamp = Date.now();

      try {
        const queryResult = await queryService.execute(dbName, sql);
        setResult(queryResult);

        // 添加到历史记录（最多 50 条）
        setHistory((prev) => {
          const newHistory = [
            { sql, result: queryResult, error: null, timestamp },
            ...prev,
          ];
          return newHistory.slice(0, 50);
        });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "查询失败";
        setError(errorMessage);
        message.error(`查询失败: ${errorMessage}`);

        // 添加到历史记录
        setHistory((prev) => {
          const newHistory = [
            { sql, result: null, error: errorMessage, timestamp },
            ...prev,
          ];
          return newHistory.slice(0, 50);
        });
      } finally {
        setLoading(false);
      }
    },
    [dbName],
  );

  const clearResult = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    result,
    loading,
    error,
    history,
    executeQuery,
    clearResult,
  };
};
