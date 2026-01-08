import { useState, useMemo, useCallback } from 'react'
import { useTickets } from '@/hooks/useTickets'
import { useToast } from '@/components/ui/toast'
import { TicketListItem } from '@/components/TicketListItem'
import { TicketDialog } from '@/components/TicketDialog'
import { TicketListSkeleton } from '@/components/LoadingState'
import { Pagination } from '@/components/ui/pagination'
import { Button } from '@/components/ui/button'
import { Trash2, RotateCcw, AlertTriangle } from 'lucide-react'
import { Ticket, TicketQueryParams } from '@/types/ticket'
import { ticketService } from '@/services/ticketService'
import { useTags } from '@/hooks/useTags'

function TrashPage() {
  const { addToast } = useToast()
  const [selectedTicketIds, setSelectedTicketIds] = useState<Set<number>>(new Set())
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null)
  const [ticketDialogOpen, setTicketDialogOpen] = useState(false)

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // 获取已删除的 Tickets
  const ticketQueryParams: TicketQueryParams = useMemo(
    () => ({
      only_deleted: true,
      sort_by: 'deleted_at',
      sort_order: 'desc',
      page: currentPage,
      page_size: pageSize,
    }),
    [currentPage, pageSize]
  )

  const {
    tickets,
    pagination,
    loading: ticketsLoading,
    error: ticketsError,
    refetch: refetchTickets,
  } = useTickets(ticketQueryParams)

  const { tags, refetch: refetchTags } = useTags()

  // 批量恢复
  const handleBatchRestore = async () => {
    if (selectedTicketIds.size === 0) {
      addToast('warning', '请先选择要恢复的 Ticket')
      return
    }

    try {
      await Promise.all(Array.from(selectedTicketIds).map(id => ticketService.restoreTicket(id)))
      addToast('success', `成功恢复 ${selectedTicketIds.size} 个 Ticket`)
      setSelectedTicketIds(new Set())
      refetchTickets()
    } catch (error) {
      console.error('批量恢复失败:', error)
      addToast('error', '批量恢复失败，请重试')
    }
  }

  // 批量永久删除（二次确认）
  const handleBatchPermanentDelete = async () => {
    if (selectedTicketIds.size === 0) {
      addToast('warning', '请先选择要永久删除的 Ticket')
      return
    }

    const count = selectedTicketIds.size

    // 第一次确认
    if (!confirm(`⚠️ 警告：您即将永久删除 ${count} 个 Ticket\n\n此操作不可恢复！是否继续？`)) {
      return
    }

    // 第二次确认
    if (!confirm(`⚠️ 最后确认：永久删除 ${count} 个 Ticket\n\n删除后无法恢复，确定要继续吗？`)) {
      return
    }

    try {
      await Promise.all(
        Array.from(selectedTicketIds).map(id => ticketService.deleteTicket(id, true))
      )
      addToast('success', `已永久删除 ${count} 个 Ticket`)
      setSelectedTicketIds(new Set())
      refetchTickets()
    } catch (error) {
      console.error('批量永久删除失败:', error)
      addToast('error', '批量永久删除失败，请重试')
    }
  }

  // 清空回收站（超级确认）
  const handleEmptyTrash = async () => {
    if (tickets.length === 0) {
      addToast('info', '回收站已经是空的')
      return
    }

    // 第一次确认
    if (
      !confirm(
        `⚠️⚠️⚠️ 危险操作 ⚠️⚠️⚠️\n\n即将清空回收站，永久删除 ${tickets.length} 个 Ticket\n\n此操作不可恢复！是否继续？`
      )
    ) {
      return
    }

    // 第二次确认（要求输入"确认删除"）
    const confirmation = prompt(
      '请输入"确认删除"来执行此操作：\n\n（此操作将永久删除所有已删除的 Ticket，无法恢复）'
    )
    if (confirmation !== '确认删除') {
      addToast('info', '已取消清空回收站')
      return
    }

    try {
      await Promise.all(tickets.map(ticket => ticketService.deleteTicket(ticket.id, true)))
      addToast('success', `已清空回收站，永久删除 ${tickets.length} 个 Ticket`)
      refetchTickets()
    } catch (error) {
      console.error('清空回收站失败:', error)
      addToast('error', '清空回收站失败，请重试')
    }
  }

  const handleSelectTicket = useCallback((ticketId: number, selected: boolean) => {
    setSelectedTicketIds(prev => {
      const newSet = new Set(prev)
      if (selected) {
        newSet.add(ticketId)
      } else {
        newSet.delete(ticketId)
      }
      return newSet
    })
  }, [])

  const handleSelectAll = useCallback(() => {
    if (selectedTicketIds.size === tickets.length) {
      setSelectedTicketIds(new Set())
    } else {
      setSelectedTicketIds(new Set(tickets.map(t => t.id)))
    }
  }, [tickets, selectedTicketIds.size])

  const handleEditTicket = (ticket: Ticket) => {
    setEditingTicket(ticket)
    setTicketDialogOpen(true)
  }

  return (
    <div className="flex h-screen bg-background">
      {/* 主内容区域 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 顶部栏 */}
        <div className="border-b bg-background p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Trash2 className="w-6 h-6 text-muted-foreground" />
              <h1 className="text-2xl font-bold text-muted-foreground">回收站</h1>
              {tickets.length > 0 && (
                <span className="text-sm text-muted-foreground">({tickets.length} 项)</span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={() => window.history.back()}>
                返回
              </Button>
              {tickets.length > 0 && (
                <Button variant="destructive" onClick={handleEmptyTrash}>
                  <Trash2 className="w-4 h-4 mr-2" />
                  清空回收站
                </Button>
              )}
            </div>
          </div>

          {/* 说明 */}
          <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-800">
              <p className="font-medium">回收站说明</p>
              <p className="mt-1">
                这里显示所有已删除的
                Ticket。您可以恢复它们或永久删除。永久删除后无法恢复，请谨慎操作。
              </p>
            </div>
          </div>
        </div>

        {/* 工具栏 */}
        <div className="border-b bg-background px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {selectedTicketIds.size > 0 ? (
              <>
                <span className="text-sm text-muted-foreground">
                  已选择 {selectedTicketIds.size} 项
                </span>
                <Button variant="outline" size="sm" onClick={handleBatchRestore}>
                  <RotateCcw className="w-4 h-4 mr-2" />
                  批量恢复
                </Button>
                <Button variant="destructive" size="sm" onClick={handleBatchPermanentDelete}>
                  <Trash2 className="w-4 h-4 mr-2" />
                  永久删除
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setSelectedTicketIds(new Set())}>
                  取消选择
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" onClick={handleSelectAll}>
                  {selectedTicketIds.size === tickets.length && tickets.length > 0
                    ? '取消全选'
                    : '全选'}
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Ticket 列表 */}
        <div className="flex-1 overflow-y-auto">
          {ticketsLoading && <TicketListSkeleton />}
          {ticketsError && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center p-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-destructive/10 flex items-center justify-center">
                  <AlertTriangle className="w-8 h-8 text-destructive" />
                </div>
                <h3 className="text-lg font-semibold text-destructive mb-2">加载失败</h3>
                <p className="text-muted-foreground mb-4">
                  {ticketsError.message || '无法加载回收站'}
                </p>
                <Button onClick={() => refetchTickets()} variant="outline">
                  重新加载
                </Button>
              </div>
            </div>
          )}
          {!ticketsLoading && !ticketsError && (
            <>
              {tickets.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Trash2 className="w-16 h-16 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-xl font-medium text-muted-foreground mb-2">回收站是空的</p>
                    <p className="text-sm text-muted-foreground">已删除的 Ticket 会显示在这里</p>
                  </div>
                </div>
              ) : (
                <div className="divide-y">
                  {tickets.map(ticket => (
                    <TicketListItem
                      key={ticket.id}
                      ticket={ticket}
                      selected={selectedTicketIds.has(ticket.id)}
                      onSelect={handleSelectTicket}
                      onUpdate={refetchTickets}
                      onEdit={handleEditTicket}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* 分页 */}
        {!ticketsLoading && !ticketsError && pagination.total > 0 && (
          <Pagination
            currentPage={pagination.page}
            totalPages={pagination.totalPages}
            pageSize={pagination.pageSize}
            totalItems={pagination.total}
            onPageChange={setCurrentPage}
            onPageSizeChange={size => {
              setPageSize(size)
              setCurrentPage(1)
            }}
          />
        )}
      </div>

      {/* Ticket 编辑对话框 */}
      <TicketDialog
        open={ticketDialogOpen}
        onOpenChange={setTicketDialogOpen}
        ticket={editingTicket}
        tags={tags}
        onSuccess={() => {
          addToast('success', 'Ticket 更新成功')
          refetchTickets()
          refetchTags()
        }}
      />
    </div>
  )
}

export default TrashPage
