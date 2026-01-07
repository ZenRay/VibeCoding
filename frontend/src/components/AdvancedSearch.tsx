import { useState, useEffect } from 'react'
import { Input } from './ui/input'
import { Button } from './ui/button'
import { Select } from './ui/select'
import { Label } from './ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog'
import { Search, X, History, Settings } from 'lucide-react'
import { useLocalStorage } from '@/hooks/useLocalStorage'

interface AdvancedSearchProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  searchScope: 'title' | 'all'
  onSearchScopeChange: (scope: 'title' | 'all') => void
}

export function AdvancedSearch({
  searchQuery,
  onSearchChange,
  searchScope,
  onSearchScopeChange,
}: AdvancedSearchProps) {
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery)
  const [showSettings, setShowSettings] = useState(false)
  const [searchHistory, setSearchHistory] = useLocalStorage<string[]>('search-history', [])
  const [showHistory, setShowHistory] = useState(false)

  // 防抖搜索
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange(localSearchQuery)
      
      // 保存到搜索历史（非空且不重复）
      if (localSearchQuery.trim() && !searchHistory.includes(localSearchQuery.trim())) {
        const newHistory = [localSearchQuery.trim(), ...searchHistory].slice(0, 10) // 最多保存 10 条
        setSearchHistory(newHistory)
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [localSearchQuery, onSearchChange, searchHistory, setSearchHistory])

  const handleClearSearch = () => {
    setLocalSearchQuery('')
    onSearchChange('')
  }

  const handleSelectHistory = (query: string) => {
    setLocalSearchQuery(query)
    onSearchChange(query)
    setShowHistory(false)
  }

  const handleClearHistory = () => {
    if (confirm('确定要清除所有搜索历史吗？')) {
      setSearchHistory([])
    }
  }

  return (
    <div className="relative">
      <div className="flex gap-2">
        {/* 搜索框 */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            type="text"
            placeholder={
              searchScope === 'title'
                ? '搜索 Ticket 标题...'
                : '搜索标题和描述...'
            }
            value={localSearchQuery}
            onChange={e => setLocalSearchQuery(e.target.value)}
            onFocus={() => setShowHistory(searchHistory.length > 0)}
            onBlur={() => setTimeout(() => setShowHistory(false), 200)}
            className="pl-10 pr-20"
          />
          <div className="absolute right-1 top-1/2 transform -translate-y-1/2 flex gap-1">
            {localSearchQuery && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={handleClearSearch}
                title="清除搜索"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
            {searchHistory.length > 0 && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => setShowHistory(!showHistory)}
                title="搜索历史"
              >
                <History className="w-4 h-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setShowSettings(true)}
              title="搜索设置"
            >
              <Settings className="w-4 h-4" />
            </Button>
          </div>

          {/* 搜索历史下拉 */}
          {showHistory && searchHistory.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-background border rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto">
              <div className="p-2">
                <div className="flex items-center justify-between mb-2 px-2">
                  <span className="text-xs font-medium text-muted-foreground">搜索历史</span>
                  <button
                    onClick={handleClearHistory}
                    className="text-xs text-destructive hover:underline"
                  >
                    清除
                  </button>
                </div>
                {searchHistory.map((query, index) => (
                  <button
                    key={index}
                    onClick={() => handleSelectHistory(query)}
                    className="w-full text-left px-3 py-2 hover:bg-muted rounded text-sm flex items-center gap-2"
                  >
                    <History className="w-3 h-3 text-muted-foreground" />
                    <span>{query}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 搜索范围快速切换 */}
        <Button
          variant={searchScope === 'title' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onSearchScopeChange(searchScope === 'title' ? 'all' : 'title')}
          title={searchScope === 'title' ? '仅搜索标题' : '搜索标题和描述'}
        >
          {searchScope === 'title' ? '标题' : '全部'}
        </Button>
      </div>

      {/* 搜索设置对话框 */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>搜索设置</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>搜索范围</Label>
              <Select
                value={searchScope}
                onChange={e => onSearchScopeChange(e.target.value as 'title' | 'all')}
              >
                <option value="title">仅搜索标题</option>
                <option value="all">搜索标题和描述</option>
              </Select>
              <p className="text-xs text-muted-foreground">
                选择搜索时包含的字段范围
              </p>
            </div>

            <div className="space-y-2">
              <Label>搜索历史</Label>
              <div className="flex items-center justify-between p-3 border rounded">
                <span className="text-sm">
                  已保存 {searchHistory.length} 条搜索历史
                </span>
                {searchHistory.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleClearHistory}
                  >
                    清除历史
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                最多保存最近 10 条搜索记录
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
