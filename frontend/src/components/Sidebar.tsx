import { useState } from 'react'
import { Tag } from '@/types/tag'
import { Label } from './ui/label'
import { RadioGroup, RadioGroupItem } from './ui/radio-group'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface SidebarProps {
  statusFilter: 'all' | 'pending' | 'completed'
  onStatusFilterChange: (status: 'all' | 'pending' | 'completed') => void
  selectedTagIds: number[]
  onTagFilterChange: (tagIds: number[]) => void
  tags: Tag[]
  includeDeleted: boolean
  onIncludeDeletedChange: (include: boolean) => void
}

// 默认显示的标签数量
const DEFAULT_VISIBLE_TAGS = 8

export function Sidebar({
  statusFilter,
  onStatusFilterChange,
  selectedTagIds,
  onTagFilterChange,
  tags,
  includeDeleted,
  onIncludeDeletedChange,
}: SidebarProps) {
  const [showAllTags, setShowAllTags] = useState(false)

  const toggleTag = (tagId: number) => {
    if (selectedTagIds.includes(tagId)) {
      onTagFilterChange(selectedTagIds.filter(id => id !== tagId))
    } else {
      onTagFilterChange([...selectedTagIds, tagId])
    }
  }

  // 决定显示哪些标签
  const visibleTags = showAllTags ? tags : tags.slice(0, DEFAULT_VISIBLE_TAGS)
  const hasMoreTags = tags.length > DEFAULT_VISIBLE_TAGS
  const hiddenCount = tags.length - DEFAULT_VISIBLE_TAGS

  return (
    <div className="w-64 border-r bg-background flex flex-col h-screen animate-slide-in-left">
      {/* 固定区域：状态过滤 */}
      <div className="p-6 pb-4 flex-shrink-0">
        <Label className="text-sm font-semibold mb-3 block">状态</Label>
        <RadioGroup
          value={statusFilter}
          onValueChange={onStatusFilterChange as (value: string) => void}
        >
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

      {/* 可滚动区域：标签过滤 */}
      <div className="flex-1 overflow-y-auto px-6 pb-4 min-h-0">
        <div className="flex items-center justify-between mb-3">
          <Label className="text-sm font-semibold">标签</Label>
          {tags.length > 0 && (
            <span className="text-xs text-muted-foreground">{tags.length} 个</span>
          )}
        </div>
        <div className="space-y-1">
          {tags.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无标签</p>
          ) : (
            <>
              {visibleTags.map(tag => (
                <button
                  key={tag.id}
                  type="button"
                  onClick={() => toggleTag(tag.id)}
                  className={`w-full flex items-center justify-between p-2 rounded-md text-sm transition-all duration-200 hover:translate-x-1 ${
                    selectedTagIds.includes(tag.id)
                      ? 'bg-primary/10 border border-primary'
                      : 'hover:bg-muted'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: tag.color }}
                    />
                    <span className="truncate">{tag.name}</span>
                  </div>
                  <span className="text-xs text-muted-foreground flex-shrink-0 ml-2">
                    {tag.ticket_count || 0}
                  </span>
                </button>
              ))}
              {/* 展开/收起按钮 */}
              {hasMoreTags && (
                <button
                  type="button"
                  onClick={() => setShowAllTags(!showAllTags)}
                  className="w-full flex items-center justify-center gap-1 p-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors"
                >
                  {showAllTags ? (
                    <>
                      <ChevronUp className="w-4 h-4" />
                      收起
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-4 h-4" />
                      显示更多 ({hiddenCount})
                    </>
                  )}
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* 固定区域：显示选项 */}
      <div className="p-6 pt-4 border-t flex-shrink-0">
        <Label className="text-sm font-semibold mb-3 block">显示选项</Label>
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="include-deleted"
            checked={includeDeleted}
            onChange={e => onIncludeDeletedChange(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300"
          />
          <Label htmlFor="include-deleted" className="cursor-pointer text-sm">
            显示已删除的 Ticket
          </Label>
        </div>
      </div>
    </div>
  )
}
