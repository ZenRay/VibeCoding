import { useState, useMemo, useEffect } from 'react'
import { useTickets } from '@/hooks/useTickets'
import { useTags } from '@/hooks/useTags'
import { useKeyboard } from '@/hooks/useKeyboard'
import { useToast } from '@/components/ui/toast'
import { TicketListItem } from '@/components/TicketListItem'
import { Sidebar } from '@/components/Sidebar'
import { TicketDialog } from '@/components/TicketDialog'
import { TagDialog } from '@/components/TagDialog'
import { TicketListSkeleton } from '@/components/LoadingState'
import { Pagination } from '@/components/ui/pagination'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Plus, Tag as TagIcon, Search, ChevronUp, ChevronDown } from 'lucide-react'
import { Ticket } from '@/types/ticket'
import { Tag } from '@/types/tag'
import { TicketQueryParams } from '@/types/ticket'
import { ticketService } from '@/services/ticketService'

function HomePage() {
  const { addToast } = useToast()

  // 搜索和过滤状态
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'completed'>('all')
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([])
  const [sortBy, setSortBy] = useState<'created_at' | 'updated_at' | 'title'>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [selectedTicketIds, setSelectedTicketIds] = useState<Set<number>>(new Set())
  const [includeDeleted, setIncludeDeleted] = useState(false)

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // 构建查询参数
  const ticketQueryParams: TicketQueryParams = useMemo(() => {
    const params: TicketQueryParams = {}

    if (searchQuery.trim()) {
      params.search = searchQuery.trim()
    }

    if (statusFilter !== 'all') {
      params.status = statusFilter
    }

    if (selectedTagIds.length > 0) {
      params.tag_ids = selectedTagIds
      params.tag_filter = 'and'
    }

    params.sort_by = sortBy
    params.sort_order = sortOrder

    if (includeDeleted) {
      params.include_deleted = true
    }

    // 分页参数
    params.page = currentPage
    params.page_size = pageSize

    return params
  }, [searchQuery, statusFilter, selectedTagIds, sortBy, sortOrder, includeDeleted, currentPage, pageSize])

  const {
    tickets,
    loading: ticketsLoading,
    error: ticketsError,
    refetch: refetchTickets,
  } = useTickets(ticketQueryParams)
  const { tags, refetch: refetchTags } = useTags()

  const [ticketDialogOpen, setTicketDialogOpen] = useState(false)
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null)
  const [tagDialogOpen, setTagDialogOpen] = useState(false)
  const [editingTag, setEditingTag] = useState<Tag | null>(null)

  const handleCreateTicket = () => {
    setEditingTicket(null)
    setTicketDialogOpen(true)
  }

  const handleEditTicket = (ticket: Ticket) => {
    setEditingTicket(ticket)
    setTicketDialogOpen(true)
  }

  const handleCreateTag = () => {
    setEditingTag(null)
    setTagDialogOpen(true)
  }

  const handleSelectTicket = (ticketId: number, selected: boolean) => {
    setSelectedTicketIds(prev => {
      const newSet = new Set(prev)
      if (selected) {
        newSet.add(ticketId)
      } else {
        newSet.delete(ticketId)
      }
      return newSet
    })
  }

  const handleSelectAll = () => {
    if (selectedTicketIds.size === tickets.length) {
      setSelectedTicketIds(new Set())
    } else {
      setSelectedTicketIds(new Set(tickets.map(t => t.id)))
    }
  }

  const handleBatchDelete = async () => {
    if (selectedTicketIds.size === 0) return
    if (!confirm(`确定要删除选中的 ${selectedTicketIds.size} 个 Ticket 吗？`)) return

    try {
      await Promise.all(
        Array.from(selectedTicketIds).map(id => ticketService.deleteTicket(id, false))
      )
      setSelectedTicketIds(new Set())
      addToast('success', `成功删除 ${selectedTicketIds.size} 个 Ticket`)
      refetchTickets()
    } catch (error) {
      console.error('批量删除失败:', error)
      addToast('error', '批量删除失败，请重试')
    }
  }

  // 键盘快捷键
  useKeyboard([
    {
      key: 'n',
      callback: handleCreateTicket,
      description: '创建新 Ticket',
    },
    {
      key: 'k',
      ctrl: true,
      meta: true,
      callback: () => {
        document.querySelector<HTMLInputElement>('input[type="text"]')?.focus()
      },
      description: '聚焦搜索框',
    },
    {
      key: 'Escape',
      callback: () => {
        setTicketDialogOpen(false)
        setTagDialogOpen(false)
      },
      description: '关闭对话框',
    },
  ])

  const toggleSortOrder = () => {
    setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'))
  }

  return (
    <div className="flex h-screen bg-background">
      {/* 左侧边栏 */}
      <Sidebar
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        selectedTagIds={selectedTagIds}
        onTagFilterChange={setSelectedTagIds}
        tags={tags}
        includeDeleted={includeDeleted}
        onIncludeDeletedChange={setIncludeDeleted}
      />

      {/* 主内容区域 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 顶部栏 */}
        <div className="border-b bg-background p-4">
          <div className="flex items-center justify-between mb-4">
            {/* 左侧：标题 */}
            <h1 className="text-2xl font-bold text-primary">Project Alpha</h1>

            {/* 右侧：操作按钮 */}
            <div className="flex items-center gap-2">
              <Button onClick={handleCreateTag} variant="outline" size="sm">
                <TagIcon className="w-4 h-4 mr-2" />
                管理标签
              </Button>
              <Button onClick={handleCreateTicket} size="sm">
                <Plus className="w-4 h-4 mr-2" />
                新建 Ticket
              </Button>
            </div>
          </div>

          {/* 搜索框 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              type="text"
              placeholder="搜索 Ticket..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* 列表工具栏 */}
        <div className="border-b bg-background px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {selectedTicketIds.size > 0 ? (
              <>
                <span className="text-sm text-muted-foreground">
                  已选择 {selectedTicketIds.size} 项
                </span>
                <Button variant="outline" size="sm" onClick={handleBatchDelete}>
                  批量删除
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setSelectedTicketIds(new Set())}>
                  取消选择
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" onClick={handleSelectAll}>
                  批量操作
                </Button>
              </>
            )}
          </div>

          {/* 排序 */}
          <div className="flex items-center gap-2">
            <Select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as 'created_at' | 'updated_at' | 'title')}
              className="w-32"
            >
              <option value="created_at">创建时间</option>
              <option value="updated_at">更新时间</option>
              <option value="title">标题</option>
            </Select>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={toggleSortOrder}>
              {sortOrder === 'asc' ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Ticket 列表 */}
        <div className="flex-1 overflow-y-auto">
          {ticketsLoading && <TicketListSkeleton />}
          {ticketsError && <div className="p-4 text-red-500">错误: {ticketsError.message}</div>}
          {!ticketsLoading && !ticketsError && (
            <>
              {tickets.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <p className="text-muted-foreground mb-2">
                      {searchQuery || statusFilter !== 'all' || selectedTagIds.length > 0
                        ? '没有找到匹配的 Ticket'
                        : '暂无 Ticket，点击"新建 Ticket"添加'}
                    </p>
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
      </div>

        {/* 分页 */}
        {tickets.length > 0 && (
          <Pagination
            currentPage={currentPage}
            totalPages={Math.ceil(tickets.length / pageSize)}
            pageSize={pageSize}
            totalItems={tickets.length}
            onPageChange={setCurrentPage}
            onPageSizeChange={size => {
              setPageSize(size)
              setCurrentPage(1)
            }}
          />
        )}
      </div>

      {/* Ticket 对话框 */}
      <TicketDialog
        open={ticketDialogOpen}
        onOpenChange={setTicketDialogOpen}
        ticket={editingTicket}
        tags={tags}
        onSuccess={() => {
          addToast('success', editingTicket ? 'Ticket 更新成功' : 'Ticket 创建成功')
          refetchTickets()
          refetchTags()
        }}
      />

      {/* 标签对话框 */}
      <TagDialog
        open={tagDialogOpen}
        onOpenChange={setTagDialogOpen}
        tag={editingTag}
        onSuccess={() => {
          addToast('success', editingTag ? '标签更新成功' : '标签创建成功')
          refetchTags()
          refetchTickets()
        }}
      />
    </div>
  )
}

export default HomePage
