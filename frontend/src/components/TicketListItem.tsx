import { Ticket } from '@/types/ticket'
import { Button } from './ui/button'
import { ticketService } from '@/services/ticketService'
import { useToast } from './ui/toast'
import { Edit2, Trash2 } from 'lucide-react'

interface TicketListItemProps {
  ticket: Ticket
  selected: boolean
  onSelect: (ticketId: number, selected: boolean) => void
  onUpdate: () => void
  onEdit: (ticket: Ticket) => void
}

export function TicketListItem({
  ticket,
  selected,
  onSelect,
  onUpdate,
  onEdit,
}: TicketListItemProps) {
  const { addToast } = useToast()
  
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
      className={`flex items-start gap-4 p-4 border-b hover:bg-muted/50 transition-colors ${
        isDeleted ? 'opacity-60' : ''
      }`}
    >
      {/* 复选框 */}
      <input
        type="checkbox"
        checked={selected}
        onChange={e => onSelect(ticket.id, e.target.checked)}
        disabled={isDeleted}
        className="mt-1 h-4 w-4 rounded border-gray-300"
      />

      {/* 内容区域 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-4 mb-1">
          <h3
            className={`text-base font-medium ${
              isDeleted ? 'line-through text-muted-foreground' : ''
            }`}
          >
            {ticket.title}
          </h3>
          <div className="flex items-center gap-2 flex-shrink-0">
            {!isDeleted && (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onEdit(ticket)}
                >
                  <Edit2 className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive hover:text-destructive"
                  onClick={handleDelete}
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
}
