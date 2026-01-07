import { Ticket } from '@/types/ticket'
import { Card, CardContent, CardFooter } from './ui/card'
import { Button } from './ui/button'
import { ticketService } from '@/services/ticketService'
import { CheckCircle2, Circle, Trash2, Edit2, RotateCcw } from 'lucide-react'

interface TicketCardProps {
  ticket: Ticket
  onUpdate: () => void
  onEdit: (ticket: Ticket) => void
}

export function TicketCard({ ticket, onUpdate, onEdit }: TicketCardProps) {
  const handleToggleStatus = async () => {
    try {
      await ticketService.toggleTicketStatus(ticket.id)
      onUpdate()
    } catch (error) {
      console.error('切换状态失败:', error)
      alert('切换状态失败，请重试')
    }
  }

  const handleDelete = async () => {
    if (!confirm('确定要删除这个 Ticket 吗？')) return
    try {
      await ticketService.deleteTicket(ticket.id, false)
      onUpdate()
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败，请重试')
    }
  }

  const handleRestore = async () => {
    try {
      await ticketService.restoreTicket(ticket.id)
      onUpdate()
    } catch (error) {
      console.error('恢复失败:', error)
      alert('恢复失败，请重试')
    }
  }

  const isDeleted = !!ticket.deleted_at

  return (
    <Card
      className={`${
        isDeleted
          ? 'opacity-60 grayscale border-dashed'
          : 'hover:shadow-md transition-shadow'
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3
            className={`text-lg font-semibold ${
              isDeleted ? 'line-through' : ''
            }`}
          >
            {ticket.title}
          </h3>
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${
              ticket.status === 'completed'
                ? 'bg-green-100 text-green-800'
                : 'bg-yellow-100 text-yellow-800'
            }`}
          >
            {ticket.status === 'completed' ? '已完成' : '未完成'}
          </span>
        </div>

        {ticket.description && (
          <p
            className={`text-sm text-muted-foreground mb-3 ${
              isDeleted ? 'line-through' : ''
            }`}
          >
            {ticket.description}
          </p>
        )}

        {ticket.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {ticket.tags.map((tag) => (
              <span
                key={tag.id}
                className="px-2 py-1 rounded text-xs font-medium"
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

        <p className="text-xs text-muted-foreground">
          创建时间: {new Date(ticket.created_at).toLocaleString('zh-CN')}
        </p>
      </CardContent>

      {!isDeleted && (
        <CardFooter className="p-4 pt-0 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleStatus}
            className="flex-1"
          >
            {ticket.status === 'completed' ? (
              <>
                <Circle className="w-4 h-4 mr-1" />
                标记未完成
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4 mr-1" />
                标记完成
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(ticket)}
          >
            <Edit2 className="w-4 h-4" />
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleDelete}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </CardFooter>
      )}

      {isDeleted && (
        <CardFooter className="p-4 pt-0">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRestore}
            className="w-full"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            恢复
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}
