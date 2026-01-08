import { Tag } from './tag'

export interface Ticket {
  id: number
  title: string
  description: string | null
  status: 'pending' | 'completed'
  tags: Tag[]
  created_at: string
  updated_at: string
  completed_at: string | null
  deleted_at: string | null
}

export interface CreateTicketRequest {
  title: string
  description?: string
  tag_ids?: number[]
}

export interface UpdateTicketRequest {
  title?: string
  description?: string
}

export interface TicketListResponse {
  data: Ticket[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

export interface TicketQueryParams {
  status?: 'pending' | 'completed' | 'all'
  include_deleted?: boolean
  only_deleted?: boolean
  tag_ids?: string // 逗号分隔的 ID 字符串，如 "1,2,3"
  tag_filter?: 'and' | 'or'
  search?: string
  sort_by?: 'created_at' | 'updated_at' | 'title'
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}
