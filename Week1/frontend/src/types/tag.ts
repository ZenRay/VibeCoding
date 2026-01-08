export interface Tag {
  id: number
  name: string
  color: string
  created_at: string
  ticket_count?: number
}

export interface CreateTagRequest {
  name: string
  color: string
}

export interface UpdateTagRequest {
  name?: string
  color?: string
}

export interface TagListResponse {
  data: Tag[]
}
