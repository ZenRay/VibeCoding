import { Tag } from '@/types/tag'
import { Label } from './ui/label'
import { RadioGroup, RadioGroupItem } from './ui/radio-group'

interface SidebarProps {
  statusFilter: 'all' | 'pending' | 'completed'
  onStatusFilterChange: (status: 'all' | 'pending' | 'completed') => void
  selectedTagIds: number[]
  onTagFilterChange: (tagIds: number[]) => void
  tags: Tag[]
  includeDeleted: boolean
  onIncludeDeletedChange: (include: boolean) => void
}

export function Sidebar({
  statusFilter,
  onStatusFilterChange,
  selectedTagIds,
  onTagFilterChange,
  tags,
  includeDeleted,
  onIncludeDeletedChange,
}: SidebarProps) {
  const toggleTag = (tagId: number) => {
    if (selectedTagIds.includes(tagId)) {
      onTagFilterChange(selectedTagIds.filter((id) => id !== tagId))
    } else {
      onTagFilterChange([...selectedTagIds, tagId])
    }
  }

  return (
    <div className="w-64 border-r bg-background p-6 space-y-6">
      {/* 状态过滤 */}
      <div>
        <Label className="text-sm font-semibold mb-3 block">状态</Label>
        <RadioGroup value={statusFilter} onValueChange={onStatusFilterChange as (value: string) => void}>
          <div className="flex items-center space-x-2 mb-2">
            <RadioGroupItem value="all" id="status-all" />
            <Label
              htmlFor="status-all"
              className={`cursor-pointer ${
                statusFilter === 'all' ? 'font-semibold text-primary' : ''
              }`}
            >
              全部
            </Label>
          </div>
          <div className="flex items-center space-x-2 mb-2">
            <RadioGroupItem value="pending" id="status-pending" />
            <Label
              htmlFor="status-pending"
              className={`cursor-pointer ${
                statusFilter === 'pending' ? 'font-semibold text-primary' : ''
              }`}
            >
              待完成
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="completed" id="status-completed" />
            <Label
              htmlFor="status-completed"
              className={`cursor-pointer ${
                statusFilter === 'completed' ? 'font-semibold text-primary' : ''
              }`}
            >
              已完成
            </Label>
          </div>
        </RadioGroup>
      </div>

      {/* 标签过滤 */}
      <div>
        <Label className="text-sm font-semibold mb-3 block">标签</Label>
        <div className="space-y-2">
          {tags.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无标签</p>
          ) : (
            tags.map((tag) => (
              <button
                key={tag.id}
                type="button"
                onClick={() => toggleTag(tag.id)}
                className={`w-full flex items-center justify-between p-2 rounded-md text-sm transition-colors ${
                  selectedTagIds.includes(tag.id)
                    ? 'bg-primary/10 border border-primary'
                    : 'hover:bg-muted'
                }`}
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: tag.color }}
                  />
                  <span>{tag.name}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {tag.ticket_count || 0}
                </span>
              </button>
            ))
          )}
        </div>
      </div>

      {/* 显示选项 */}
      <div>
        <Label className="text-sm font-semibold mb-3 block">显示选项</Label>
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="include-deleted"
            checked={includeDeleted}
            onChange={(e) => onIncludeDeletedChange(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300"
          />
          <Label
            htmlFor="include-deleted"
            className="cursor-pointer text-sm"
          >
            显示已删除的 Ticket
          </Label>
        </div>
      </div>
    </div>
  )
}
