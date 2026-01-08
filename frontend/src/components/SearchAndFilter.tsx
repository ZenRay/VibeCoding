import { useState, useEffect } from 'react'
import { Input } from './ui/input'
import { Button } from './ui/button'
import { Select } from './ui/select'
import { Label } from './ui/label'
import { Search, X, Filter } from 'lucide-react'
import { Tag } from '@/types/tag'

interface SearchAndFilterProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  statusFilter: 'all' | 'pending' | 'completed'
  onStatusFilterChange: (status: 'all' | 'pending' | 'completed') => void
  selectedTagIds: number[]
  onTagFilterChange: (tagIds: number[]) => void
  tags: Tag[]
  includeDeleted: boolean
  onIncludeDeletedChange: (include: boolean) => void
}

export function SearchAndFilter({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  selectedTagIds,
  onTagFilterChange,
  tags,
  includeDeleted,
  onIncludeDeletedChange,
}: SearchAndFilterProps) {
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery)
  const [showFilters, setShowFilters] = useState(false)

  // 防抖搜索
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange(localSearchQuery)
    }, 300)

    return () => clearTimeout(timer)
  }, [localSearchQuery, onSearchChange])

  const handleClearSearch = () => {
    setLocalSearchQuery('')
    onSearchChange('')
  }

  const toggleTag = (tagId: number) => {
    if (selectedTagIds.includes(tagId)) {
      onTagFilterChange(selectedTagIds.filter(id => id !== tagId))
    } else {
      onTagFilterChange([...selectedTagIds, tagId])
    }
  }

  const clearAllFilters = () => {
    setLocalSearchQuery('')
    onSearchChange('')
    onStatusFilterChange('all')
    onTagFilterChange([])
    onIncludeDeletedChange(false)
  }

  const hasActiveFilters =
    localSearchQuery.trim() !== '' ||
    statusFilter !== 'all' ||
    selectedTagIds.length > 0 ||
    includeDeleted

  return (
    <div className="space-y-4 mb-6">
      {/* 搜索框 */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
        <Input
          type="text"
          placeholder="搜索 Ticket 标题..."
          value={localSearchQuery}
          onChange={e => setLocalSearchQuery(e.target.value)}
          className="pl-10 pr-10"
        />
        {localSearchQuery && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8"
            onClick={handleClearSearch}
          >
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* 过滤器和快速过滤 */}
      <div className="flex items-center gap-2 flex-wrap">
        <Button
          variant={showFilters ? 'default' : 'outline'}
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="w-4 h-4 mr-2" />
          过滤器
        </Button>

        {/* 状态快速过滤 */}
        <div className="flex gap-2">
          <Button
            variant={statusFilter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onStatusFilterChange('all')}
          >
            全部
          </Button>
          <Button
            variant={statusFilter === 'pending' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onStatusFilterChange('pending')}
          >
            未完成
          </Button>
          <Button
            variant={statusFilter === 'completed' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onStatusFilterChange('completed')}
          >
            已完成
          </Button>
        </div>

        {hasActiveFilters && (
          <Button variant="outline" size="sm" onClick={clearAllFilters}>
            <X className="w-4 h-4 mr-1" />
            清除所有
          </Button>
        )}
      </div>

      {/* 展开的过滤器面板 */}
      <div
        className={`border rounded-lg p-4 bg-muted/50 space-y-4 transition-all duration-200 ease-out overflow-hidden ${
          showFilters
            ? 'opacity-100 max-h-96 translate-y-0'
            : 'opacity-0 max-h-0 -translate-y-2 pointer-events-none p-0 border-0'
        }`}
      >
        {/* 状态过滤 */}
        <div className="space-y-2">
          <Label>状态</Label>
          <Select
            value={statusFilter}
            onChange={e => onStatusFilterChange(e.target.value as 'all' | 'pending' | 'completed')}
          >
            <option value="all">全部</option>
            <option value="pending">未完成</option>
            <option value="completed">已完成</option>
          </Select>
        </div>

        {/* 标签过滤 */}
        {tags.length > 0 && (
          <div className="space-y-2">
            <Label>标签过滤</Label>
            <div className="flex flex-wrap gap-2">
              {tags.map(tag => (
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
                    backgroundColor: selectedTagIds.includes(tag.id) ? tag.color : tag.color + '20',
                    color: selectedTagIds.includes(tag.id) ? 'white' : tag.color,
                    border: `1px solid ${tag.color}`,
                  }}
                >
                  {tag.name}
                </button>
              ))}
            </div>
            {selectedTagIds.length > 0 && (
              <p className="text-xs text-muted-foreground">已选择 {selectedTagIds.length} 个标签</p>
            )}
          </div>
        )}

        {/* 包含已删除 */}
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="include-deleted"
            checked={includeDeleted}
            onChange={e => onIncludeDeletedChange(e.target.checked)}
            className="w-4 h-4 rounded border-gray-300"
          />
          <Label htmlFor="include-deleted" className="cursor-pointer">
            包含已删除的 Ticket
          </Label>
        </div>
      </div>

      {/* 当前过滤条件显示 */}
      <div
        className={`flex items-center gap-2 flex-wrap text-sm text-muted-foreground transition-all duration-200 ease-out ${
          hasActiveFilters
            ? 'opacity-100 max-h-20 translate-y-0'
            : 'opacity-0 max-h-0 -translate-y-1 pointer-events-none overflow-hidden'
        }`}
      >
        <span>当前过滤：</span>
        {localSearchQuery && (
          <span className="px-2 py-1 bg-background rounded border">搜索: "{localSearchQuery}"</span>
        )}
        {statusFilter !== 'all' && (
          <span className="px-2 py-1 bg-background rounded border">
            状态: {statusFilter === 'pending' ? '未完成' : '已完成'}
          </span>
        )}
        {selectedTagIds.length > 0 && (
          <span className="px-2 py-1 bg-background rounded border">
            标签: {selectedTagIds.length} 个
          </span>
        )}
        {includeDeleted && (
          <span className="px-2 py-1 bg-background rounded border">包含已删除</span>
        )}
      </div>
    </div>
  )
}
