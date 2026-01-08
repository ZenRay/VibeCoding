import { useState, useEffect, useRef } from 'react'
import { ticketService } from '@/services/ticketService'
import { Ticket, TicketQueryParams, TicketListResponse } from '@/types/ticket'
import { useStore } from '@/store/useStore'

interface PaginationInfo {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

export function useTickets(params?: TicketQueryParams) {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const { setTickets: setStoreTickets } = useStore()
  const paramsRef = useRef(params)

  // tag_ids 已经是字符串，直接使用
  const tagIdsKey = params?.tag_ids ?? ''

  // 更新 ref
  useEffect(() => {
    paramsRef.current = params
  }, [params])

  const fetchTickets = async () => {
    setLoading(true)
    setError(null)
    try {
      const response: TicketListResponse = await ticketService.getTickets(paramsRef.current)
      setTickets(response.data)
      setStoreTickets(response.data)
      // 更新分页信息
      if (response.pagination) {
        setPagination({
          page: response.pagination.page,
          pageSize: response.pagination.page_size,
          total: response.pagination.total,
          totalPages: response.pagination.total_pages,
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('获取 Ticket 列表失败'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTickets()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    params?.search,
    params?.status,
    params?.include_deleted,
    params?.only_deleted,
    tagIdsKey,
    params?.tag_filter,
    params?.sort_by,
    params?.sort_order,
    params?.page,
    params?.page_size,
  ])

  return {
    tickets,
    pagination,
    loading,
    error,
    refetch: fetchTickets,
  }
}
