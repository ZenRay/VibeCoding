/** 数据库相关类型定义 */

export enum DatabaseType {
  POSTGRESQL = 'postgresql',
  MYSQL = 'mysql',
  SQLITE = 'sqlite',
}

export interface DatabaseConnectionCreate {
  url: string;
}

export interface DatabaseConnectionResponse {
  name: string;
  dbType: DatabaseType;
  host: string | null;
  port: number | null;
  database: string;
  createdAt: string;
  updatedAt: string;
}

export interface DatabaseListResponse {
  databases: DatabaseConnectionResponse[];
  total: number;
}

export interface ColumnInfo {
  name: string;
  dataType: string;
  isNullable: boolean;
  isPrimaryKey?: boolean;
  defaultValue?: string | null;
  comment?: string | null;
}

export interface TableInfo {
  name: string;
  tableType: 'table' | 'view';
  columns: ColumnInfo[];
  rowCount?: number | null;
  comment?: string | null;
}

export interface DatabaseMetadata {
  name: string;
  dbType: string;
  tables: TableInfo[];
  views: TableInfo[];
  versionHash?: string | null;
  cachedAt?: string | null;
  needsRefresh?: boolean;
  warnings?: string[];
}
