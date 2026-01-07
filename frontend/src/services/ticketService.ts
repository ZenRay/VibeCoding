import api from './api'
import {
  Ticket,
  CreateTicketRequest,
  UpdateTicketRequest,
  TicketListResponse,
  TicketQueryParams,
} from '@/types/ticket'

export const ticketService = {
  /**
   * 获取 Ticket 列表
   */
  async getTickets(params?: TicketQueryParams): Promise<TicketListResponse> {
    const response = await api.get<TicketListResponse>('/tickets', { params })
    return response.data
  },

  /**
   * 获取单个 Ticket
   */
  async getTicket(id: number): Promise<Ticket> {
    const response = await api.get<Ticket>(`/tickets/${id}`)
    return response.data
  },

  /**
   * 创建 Ticket
   */
  async createTicket(data: CreateTicketRequest): Promise<Ticket> {
    const response = await api.post<Ticket>('/tickets', data)
    return response.data
  },

  /**
   * 更新 Ticket
   */
  async updateTicket(id: number, data: UpdateTicketRequest): Promise<Ticket> {
    const response = await api.put<Ticket>(`/tickets/${id}`, data)
    return response.data
  },

  /**
   * 删除 Ticket（软删除）
   */
  async deleteTicket(id: number, permanent: boolean = false): Promise<void> {
    await api.delete(`/tickets/${id}`, {
      params: { permanent },
    })
  },

  /**
   * 恢复已删除的 Ticket
   */
  async restoreTicket(id: number): Promise<Ticket> {
    const response = await api.post<Ticket>(`/tickets/${id}/restore`)
    return response.data
  },

  /**
   * 切换 Ticket 完成状态
   */
  async toggleTicketStatus(id: number): Promise<Ticket> {
    const response = await api.patch<Ticket>(`/tickets/${id}/toggle-status`)
    return response.data
  },

  /**
   * 为 Ticket 添加标签
   */
  async addTag(ticketId: number, tagId: number): Promise<Ticket> {
    const response = await api.post<Ticket>(`/tickets/${ticketId}/tags`, {
      tag_id: tagId,
    })
    return response.data
  },

  /**
   * 从 Ticket 移除标签
   */
  async removeTag(ticketId: number, tagId: number): Promise<Ticket> {
    const response = await api.delete<Ticket>(
      `/tickets/${ticketId}/tags/${tagId}`
    )
    return response.data
  },
}
