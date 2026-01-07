export interface ApiError {
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
}

export interface ApiResponse<T> {
  data?: T
  message?: string
}

export interface PaginationParams {
  page?: number
  page_size?: number
}

export interface PaginationResponse {
  page: number
  page_size: number
  total: number
  total_pages: number
}
