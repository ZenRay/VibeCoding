/** 查询 API 服务 */
import apiClient from "./api";
import {
  QueryRequest,
  QueryResult,
  NaturalLanguageQueryRequest,
  NaturalLanguageQueryResult,
} from "../types/query";

export const queryService = {
  /**
   * 执行 SQL 查询
   */
  async execute(dbName: string, sql: string): Promise<QueryResult> {
    const response = await apiClient.post<QueryResult>(
      `/api/v1/dbs/${dbName}/query`,
      { sql } as QueryRequest,
    );
    return response.data;
  },

  /**
   * 自然语言生成 SQL
   */
  async generateFromNaturalLanguage(
    dbName: string,
    prompt: string,
  ): Promise<NaturalLanguageQueryResult> {
    const response = await apiClient.post<NaturalLanguageQueryResult>(
      `/api/v1/dbs/${dbName}/query/natural`,
      { prompt } as NaturalLanguageQueryRequest,
    );
    return response.data;
  },
};
