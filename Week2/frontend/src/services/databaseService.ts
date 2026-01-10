/** 数据库连接 API 服务 */
import apiClient from './api';
import {
  DatabaseConnectionCreate,
  DatabaseConnectionResponse,
  DatabaseListResponse,
} from '../types/database';

export const databaseService = {
  /**
   * 获取所有数据库连接
   */
  async list(): Promise<DatabaseListResponse> {
    const response = await apiClient.get<DatabaseListResponse>('/api/v1/dbs');
    return response.data;
  },

  /**
   * 获取单个数据库连接
   */
  async get(name: string): Promise<DatabaseConnectionResponse> {
    const response = await apiClient.get<DatabaseConnectionResponse>(
      `/api/v1/dbs/${name}`
    );
    return response.data;
  },

  /**
   * 添加或更新数据库连接
   */
  async upsert(
    name: string,
    data: DatabaseConnectionCreate
  ): Promise<DatabaseConnectionResponse> {
    const response = await apiClient.put<DatabaseConnectionResponse>(
      `/api/v1/dbs/${name}`,
      data
    );
    return response.data;
  },

  /**
   * 删除数据库连接
   */
  async delete(name: string): Promise<void> {
    await apiClient.delete(`/api/v1/dbs/${name}`);
  },

  /**
   * 获取数据库元数据
   */
  async getMetadata(name: string, refresh = false): Promise<import('../types/database').DatabaseMetadata> {
    const response = await apiClient.get<import('../types/database').DatabaseMetadata>(
      `/api/v1/dbs/${name}/metadata`,
      { params: { refresh } }
    );
    return response.data;
  },
};
