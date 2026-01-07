import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose } from './ui/dialog'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Tag, CreateTagRequest, UpdateTagRequest } from '@/types/tag'
import { tagService } from '@/services/tagService'

interface TagDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  tag?: Tag | null
  onSuccess: () => void
}

export function TagDialog({
  open,
  onOpenChange,
  tag,
  onSuccess,
}: TagDialogProps) {
  const [name, setName] = useState('')
  const [color, setColor] = useState('#6B7280')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (tag) {
      setName(tag.name)
      setColor(tag.color)
    } else {
      setName('')
      setColor('#6B7280')
    }
  }, [tag, open])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (tag) {
        const updateData: UpdateTagRequest = {
          name,
          color,
        }
        await tagService.updateTag(tag.id, updateData)
      } else {
        const createData: CreateTagRequest = {
          name,
          color,
        }
        await tagService.createTag(createData)
      }

      onSuccess()
      onOpenChange(false)
    } catch (error: unknown) {
      console.error('保存失败:', error)
      let message = '保存失败，请重试'
      if (error instanceof Error) {
        message = error.message
      } else if (
        typeof error === 'object' &&
        error !== null &&
        'error' in error &&
        typeof (error as { error?: { message?: string } }).error === 'object' &&
        (error as { error?: { message?: string } }).error !== null
      ) {
        const errorObj = (error as { error: { message?: string } }).error
        message = errorObj.message || message
      } else if (
        typeof error === 'object' &&
        error !== null &&
        'message' in error &&
        typeof (error as { message?: unknown }).message === 'string'
      ) {
        message = (error as { message: string }).message
      }
      alert(message)
    } finally {
      setLoading(false)
    }
  }

  const presetColors = [
    '#3B82F6', // blue
    '#10B981', // green
    '#EF4444', // red
    '#F59E0B', // yellow
    '#8B5CF6', // purple
    '#06B6D4', // cyan
    '#6B7280', // gray
  ]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{tag ? '编辑标签' : '创建标签'}</DialogTitle>
          <DialogDescription>
            {tag ? '修改标签信息' : '创建新标签'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="tag-name">名称 *</Label>
            <Input
              id="tag-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="输入标签名称"
              required
              maxLength={50}
            />
            <p className="text-xs text-muted-foreground">
              注意：英文字符会自动转换为大写
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tag-color">颜色 *</Label>
            <div className="flex gap-2 items-center">
              <Input
                id="tag-color"
                type="color"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="w-20 h-10"
              />
              <Input
                type="text"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                placeholder="#6B7280"
                pattern="^#[0-9A-Fa-f]{6}$"
                maxLength={7}
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              {presetColors.map((presetColor) => (
                <button
                  key={presetColor}
                  type="button"
                  onClick={() => setColor(presetColor)}
                  className={`w-8 h-8 rounded-full border-2 ${
                    color === presetColor ? 'border-foreground scale-110' : 'border-transparent'
                  }`}
                  style={{ backgroundColor: presetColor }}
                  aria-label={`选择颜色 ${presetColor}`}
                />
              ))}
            </div>
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
            <Button type="submit" disabled={loading || !name.trim()}>
              {loading ? '保存中...' : tag ? '更新' : '创建'}
            </Button>
          </div>
        </form>

        <DialogClose onClose={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  )
}
