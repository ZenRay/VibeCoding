import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose } from './ui/dialog'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Ticket, CreateTicketRequest, UpdateTicketRequest } from '@/types/ticket'
import { Tag } from '@/types/tag'
import { ticketService } from '@/services/ticketService'

interface TicketDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  ticket?: Ticket | null
  tags: Tag[]
  onSuccess: () => void
}

export function TicketDialog({
  open,
  onOpenChange,
  ticket,
  tags,
  onSuccess,
}: TicketDialogProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (ticket) {
      setTitle(ticket.title)
      setDescription(ticket.description || '')
      setSelectedTagIds(ticket.tags.map((t) => t.id))
    } else {
      setTitle('')
      setDescription('')
      setSelectedTagIds([])
    }
  }, [ticket, open])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (ticket) {
        // 更新 Ticket
        const updateData: UpdateTicketRequest = {
          title,
          description: description || undefined,
        }
        await ticketService.updateTicket(ticket.id, updateData)

        // 更新标签
        const currentTagIds = ticket.tags.map((t) => t.id)
        const tagsToAdd = selectedTagIds.filter((id) => !currentTagIds.includes(id))
        const tagsToRemove = currentTagIds.filter((id) => !selectedTagIds.includes(id))

        for (const tagId of tagsToAdd) {
          await ticketService.addTag(ticket.id, tagId)
        }
        for (const tagId of tagsToRemove) {
          await ticketService.removeTag(ticket.id, tagId)
        }
      } else {
        // 创建 Ticket
        const createData: CreateTicketRequest = {
          title,
          description: description || undefined,
          tag_ids: selectedTagIds.length > 0 ? selectedTagIds : undefined,
        }
        await ticketService.createTicket(createData)
      }

      onSuccess()
      onOpenChange(false)
    } catch (error) {
      console.error('保存失败:', error)
      alert('保存失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const toggleTag = (tagId: number) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId)
        ? prev.filter((id) => id !== tagId)
        : [...prev, tagId]
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{ticket ? '编辑 Ticket' : '创建 Ticket'}</DialogTitle>
          <DialogDescription>
            {ticket
              ? '修改 Ticket 信息'
              : '填写 Ticket 信息并选择标签'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">标题 *</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="输入 Ticket 标题"
              required
              maxLength={200}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">描述</Label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="输入 Ticket 描述（可选）"
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              maxLength={5000}
            />
          </div>

          <div className="space-y-2">
            <Label>标签</Label>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <button
                  key={tag.id}
                  type="button"
                  onClick={() => toggleTag(tag.id)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${
                    selectedTagIds.includes(tag.id)
                      ? 'ring-2 ring-offset-2'
                      : 'opacity-60 hover:opacity-100'
                  }`}
                  style={{
                    backgroundColor: selectedTagIds.includes(tag.id)
                      ? tag.color
                      : tag.color + '20',
                    color: selectedTagIds.includes(tag.id) ? 'white' : tag.color,
                    border: `1px solid ${tag.color}`,
                  }}
                >
                  {tag.name}
                </button>
              ))}
            </div>
            {tags.length === 0 && (
              <p className="text-sm text-muted-foreground">暂无标签</p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              取消
            </Button>
            <Button type="submit" disabled={loading || !title.trim()}>
              {loading ? '保存中...' : ticket ? '更新' : '创建'}
            </Button>
          </div>
        </form>

        <DialogClose onClose={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  )
}
