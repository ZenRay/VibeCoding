import { useState, useEffect, useCallback, useMemo } from 'react'
import { tagService, TagQueryParams } from '@/services/tagService'
import { Tag } from '@/types/tag'
import { useStore } from '@/store/useStore'

export function useTags(params?: TagQueryParams) {
  const [tags, setTags] = useState<Tag[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const { setTags: setStoreTags } = useStore()

  // 将 params 序列化为字符串，用于依赖比较
  const paramsKey = useMemo(() => JSON.stringify(params), [params])

  const fetchTags = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await tagService.getTags(params)
      setTags(response.data)
      setStoreTags(response.data)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('获取标签列表失败'))
    } finally {
      setLoading(false)
    }
  }, [params, setStoreTags])

  useEffect(() => {
    fetchTags()
  }, [fetchTags, paramsKey])

  return {
    tags,
    loading,
    error,
    refetch: fetchTags,
  }
}
