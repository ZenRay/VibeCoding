import { create } from 'zustand'
import { Ticket } from '@/types/ticket'
import { Tag } from '@/types/tag'

export interface FilterState {
  status?: 'pending' | 'completed' | 'all'
  tagIds?: number[]
  tagFilter?: 'and' | 'or'
  search?: string
  sortBy?: 'created_at' | 'updated_at' | 'title'
  sortOrder?: 'asc' | 'desc'
}

interface AppState {
  // 数据
  tickets: Ticket[]
  tags: Tag[]
  filters: FilterState

  // Actions
  setTickets: (tickets: Ticket[]) => void
  setTags: (tags: Tag[]) => void
  setFilters: (filters: Partial<FilterState>) => void
  resetFilters: () => void

  // Ticket 操作
  addTicket: (ticket: Ticket) => void
  updateTicket: (id: number, ticket: Partial<Ticket>) => void
  removeTicket: (id: number) => void

  // Tag 操作
  addTag: (tag: Tag) => void
  updateTag: (id: number, tag: Partial<Tag>) => void
  removeTag: (id: number) => void
}

const defaultFilters: FilterState = {
  status: 'all',
  tagIds: undefined,
  tagFilter: 'and',
  search: undefined,
  sortBy: 'created_at',
  sortOrder: 'desc',
}

export const useStore = create<AppState>(set => ({
  // 初始状态
  tickets: [],
  tags: [],
  filters: defaultFilters,

  // 设置 Tickets
  setTickets: tickets => set({ tickets }),

  // 设置 Tags
  setTags: tags => set({ tags }),

  // 设置过滤器
  setFilters: newFilters =>
    set(state => ({
      filters: { ...state.filters, ...newFilters },
    })),

  // 重置过滤器
  resetFilters: () => set({ filters: defaultFilters }),

  // 添加 Ticket
  addTicket: ticket =>
    set(state => ({
      tickets: [ticket, ...state.tickets],
    })),

  // 更新 Ticket
  updateTicket: (id, updates) =>
    set(state => ({
      tickets: state.tickets.map(ticket => (ticket.id === id ? { ...ticket, ...updates } : ticket)),
    })),

  // 删除 Ticket
  removeTicket: id =>
    set(state => ({
      tickets: state.tickets.filter(ticket => ticket.id !== id),
    })),

  // 添加 Tag
  addTag: tag =>
    set(state => ({
      tags: [...state.tags, tag],
    })),

  // 更新 Tag
  updateTag: (id, updates) =>
    set(state => ({
      tags: state.tags.map(tag => (tag.id === id ? { ...tag, ...updates } : tag)),
    })),

  // 删除 Tag
  removeTag: id =>
    set(state => ({
      tags: state.tags.filter(tag => tag.id !== id),
    })),
}))
