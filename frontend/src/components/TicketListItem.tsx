import { memo } from 'react'
import { Ticket } from '@/types/ticket'
import { Button } from './ui/button'
import { ticketService } from '@/services/ticketService'
import { useToast } from './ui/toast'
import { Edit2, Trash2, RotateCcw, CheckCircle2, Circle } from 'lucide-react'

interface TicketListItemProps {
  ticket: Ticket
  selected: boolean
  onSelect: (ticketId: number, selected: boolean) => void
  onUpdate: () => void
  onEdit: (ticket: Ticket) => void
}

/**
 * Ticket 列表项组件
 * 使用 React.memo 优化，只有当 props 变化时才重新渲染
 */
export const TicketListItem = memo(
  function TicketListItem({ ticket, selected, onSelect, onUpdate, onEdit }: TicketListItemProps) {
    const { addToast } = useToast()

    const handleToggleStatus = async () => {
      try {
        await ticketService.toggleTicketStatus(ticket.id)
        addToast('success', ticket.status === 'completed' ? '已标记为未完成' : '已标记为完成')
        onUpdate()
      } catch (error) {
        console.error('切换状态失败:', error)
        addToast('error', '切换状态失败，请重试')
      }
    }

    const handleDelete = async () => {
      if (!confirm('确定要删除这个 Ticket 吗？')) return
      try {
        await ticketService.deleteTicket(ticket.id, false)
        addToast('success', 'Ticket 已删除')
        onUpdate()
      } catch (error) {
        console.error('删除失败:', error)
        addToast('error', '删除失败，请重试')
      }
    }

    const handleRestore = async () => {
      try {
        await ticketService.restoreTicket(ticket.id)
        addToast('success', 'Ticket 已恢复')
        onUpdate()
      } catch (error) {
        console.error('恢复失败:', error)
        addToast('error', '恢复失败，请重试')
      }
    }

    const handlePermanentDelete = async () => {
      // 二次确认
      if (!confirm('⚠️ 警告：此操作将永久删除 Ticket，无法恢复！\n\n确定要继续吗？')) return
      if (!confirm('⚠️ 最后确认：永久删除后将无法恢复！\n\n确定要永久删除吗？')) return

      try {
        await ticketService.deleteTicket(ticket.id, true)
        addToast('success', 'Ticket 已永久删除')
        onUpdate()
      } catch (error) {
        console.error('永久删除失败:', error)
        addToast('error', '永久删除失败，请重试')
      }
    }

    const formatDate = (dateString: string) => {
      const date = new Date(dateString)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}`
    }

    const isDeleted = !!ticket.deleted_at

    return (
      <div
        className={`flex items-start gap-4 p-4 border-b hover:bg-muted/50 transition-all duration-200 animate-slide-in-up ${
          isDeleted ? 'opacity-60' : ''
        }`}
      >
        {/* 复选框 */}
        <input
          type="checkbox"
          checked={selected}
          onChange={e => onSelect(ticket.id, e.target.checked)}
          className="mt-1 h-4 w-4 rounded border-gray-300"
        />

        {/* 内容区域 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 mb-1">
            <div className="flex items-center gap-2 flex-1">
              {/* 状态图标 */}
              {!isDeleted && (
                <button
                  onClick={handleToggleStatus}
                  className="flex-shrink-0 transition-colors"
                  title={ticket.status === 'completed' ? '标记为未完成' : '标记为完成'}
                >
                  {ticket.status === 'completed' ? (
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                  ) : (
                    <Circle className="h-5 w-5 text-muted-foreground hover:text-primary" />
                  )}
                </button>
              )}

              <h3
                className={`text-base font-medium ${
                  isDeleted ? 'line-through text-muted-foreground' : ''
                } ${ticket.status === 'completed' && !isDeleted ? 'line-through text-muted-foreground' : ''}`}
              >
                {ticket.title}
              </h3>
            </div>

            <div className="flex items-center gap-2 flex-shrink-0">
              {!isDeleted ? (
                <>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => onEdit(ticket)}
                    title="编辑"
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive"
                    onClick={handleDelete}
                    title="删除"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-blue-600 hover:text-blue-700"
                    onClick={handleRestore}
                    title="恢复"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive"
                    onClick={handlePermanentDelete}
                    title="永久删除"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          </div>

          {ticket.description && (
            <p className={`text-sm text-muted-foreground mb-2 ${isDeleted ? 'line-through' : ''}`}>
              {ticket.description}
            </p>
          )}

          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            {/* 状态标签 */}
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${
                ticket.status === 'completed'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-yellow-100 text-yellow-700'
              }`}
            >
              {ticket.status === 'completed' ? '已完成' : '未完成'}
            </span>

            <span>创建于 {formatDate(ticket.created_at)}</span>

            {ticket.tags.length > 0 && (
              <div className="flex items-center gap-2">
                {ticket.tags.map(tag => (
                  <span
                    key={tag.id}
                    className="px-2 py-0.5 rounded text-xs"
                    style={{
                      backgroundColor: tag.color + '20',
                      color: tag.color,
                      border: `1px solid ${tag.color}`,
                    }}
                  >
                    {tag.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  },
  (prevProps, nextProps) => {
    // 自定义比较函数，优化重渲染
    return (
      prevProps.ticket.id === nextProps.ticket.id &&
      prevProps.ticket.title === nextProps.ticket.title &&
      prevProps.ticket.description === nextProps.ticket.description &&
      prevProps.ticket.status === nextProps.ticket.status &&
      prevProps.ticket.deleted_at === nextProps.ticket.deleted_at &&
      prevProps.ticket.updated_at === nextProps.ticket.updated_at &&
      prevProps.ticket.tags.length === nextProps.ticket.tags.length &&
      prevProps.selected === nextProps.selected
    )
  }
)
