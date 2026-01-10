/** 查询相关类型定义 */

export interface QueryRequest {
  sql: string;
}

export interface QueryResultColumn {
  name: string;
  dataType: string;
}

export interface QueryResult {
  columns: QueryResultColumn[];
  rows: Record<string, unknown>[];
  rowCount: number;
  executionTimeMs: number;
  truncated: boolean;
  sql: string;
}

export interface NaturalLanguageQueryRequest {
  prompt: string;
}

export interface NaturalLanguageQueryResult {
  generatedSql: string;
  result: QueryResult | null;
  generationTimeMs: number;
}
