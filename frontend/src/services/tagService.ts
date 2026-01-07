import api from './api'
import {
  Tag,
  CreateTagRequest,
  UpdateTagRequest,
  TagListResponse,
} from '@/types/tag'

export interface TagQueryParams {
  sort_by?: 'name' | 'created_at' | 'usage_count'
  sort_order?: 'asc' | 'desc'
}

export const tagService = {
  /**
   * 获取标签列表
   */
  async getTags(params?: TagQueryParams): Promise<TagListResponse> {
    const response = await api.get<TagListResponse>('/tags', { params })
    return response.data
  },

  /**
   * 获取单个标签
   */
  async getTag(id: number): Promise<Tag> {
    const response = await api.get<Tag>(`/tags/${id}`)
    return response.data
  },

  /**
   * 创建标签
   */
  async createTag(data: CreateTagRequest): Promise<Tag> {
    const response = await api.post<Tag>('/tags', data)
    return response.data
  },

  /**
   * 更新标签
   */
  async updateTag(id: number, data: UpdateTagRequest): Promise<Tag> {
    const response = await api.put<Tag>(`/tags/${id}`, data)
    return response.data
  },

  /**
   * 删除标签
   */
  async deleteTag(id: number): Promise<void> {
    await api.delete(`/tags/${id}`)
  },
}
