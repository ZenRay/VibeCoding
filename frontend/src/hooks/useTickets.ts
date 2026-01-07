import { useState, useEffect, useRef, useMemo } from 'react'
import { ticketService } from '@/services/ticketService'
import { Ticket, TicketQueryParams } from '@/types/ticket'
import { useStore } from '@/store/useStore'

export function useTickets(params?: TicketQueryParams) {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const { setTickets: setStoreTickets } = useStore()
  const paramsRef = useRef(params)

  // 将 tag_ids 数组转换为字符串，用于依赖比较
  const tagIdsKey = useMemo(
    () => params?.tag_ids?.join(',') ?? '',
    [params?.tag_ids]
  )

  // 更新 ref
  useEffect(() => {
    paramsRef.current = params
  }, [params])

  const fetchTickets = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await ticketService.getTickets(paramsRef.current)
      setTickets(response.data)
      setStoreTickets(response.data)
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
    loading,
    error,
    refetch: fetchTickets,
  }
}
