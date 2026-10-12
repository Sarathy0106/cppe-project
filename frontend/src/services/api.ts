import { useAuthStore } from '../stores/auth'
import { CONFIG } from '../config'

export interface KpiData {
  total_feedback: number
  pct_positive: number
  pct_negative: number
  pct_neutral: number
  num_departments: number
}

export interface SentimentByDeptItem {
  department: string
  positive: number
  negative: number
  neutral: number
  total: number
}

export interface CategoryCountItem {
  category: string
  count: number
  percentage: number
}

export interface MonthlyTrendItem {
  month: string
  total: number
  negative_count: number
  negative_share: number
}

export interface TopComplaintItem {
  department: string
  category: string
  count: number
}

export interface FeedbackRecord {
  feedback_id: string
  department: string
  category: string
  sentiment: string
  sentiment_score: number
  feedback_text: string
  timestamp: string
  month: string
  has_pii: boolean
}

export interface ChatSource {
  id: string
  text: string
  department: string
  category: string
  sentiment: string
  score: number
}

export interface ChatResponse {
  answer: string
  sources: ChatSource[]
}

export interface AgentStep {
  tool: string
  input: any
  output_summary: string
}

export interface AgentResponse {
  answer: string
  steps: AgentStep[]
}

export interface PipelineStep {
  name: string
  status: string
  entered_at?: string
}

export interface PipelineStatusResponse {
  batch_id: string
  status: string
  execution_arn?: string
  start_date?: string
  stop_date?: string
  steps: PipelineStep[]
}

class ApiService {
  private getBaseUrl(): string {
    return CONFIG.API_URL.replace(/\/+$/, '')
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const authStore = useAuthStore()
    const url = `${this.getBaseUrl()}${path.startsWith('/') ? path : '/' + path}`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    }

    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (response.status === 401) {
      authStore.logout()
      window.location.href = '/login'
      throw new Error('Session expired. Please log in again.')
    }

    if (!response.ok) {
      let errorMessage = `API Error: ${response.status} ${response.statusText}`
      try {
        const errorJson = await response.json()
        errorMessage = errorJson.error || errorJson.message || errorMessage
      } catch {
        // ignore json parse error
      }
      throw new Error(errorMessage)
    }

    return response.json() as Promise<T>
  }

  // --- Stats endpoints ---
  async getKpis(): Promise<KpiData> {
    return this.request<KpiData>('/stats?type=kpis')
  }

  async getSentimentByDept(): Promise<SentimentByDeptItem[]> {
    return this.request<SentimentByDeptItem[]>('/stats?type=sentiment_by_department')
  }

  async getCategoryCounts(): Promise<CategoryCountItem[]> {
    return this.request<CategoryCountItem[]>('/stats?type=category_counts')
  }

  async getMonthlyTrend(): Promise<MonthlyTrendItem[]> {
    return this.request<MonthlyTrendItem[]>('/stats?type=monthly_trend')
  }

  async getTopComplaints(): Promise<TopComplaintItem[]> {
    return this.request<TopComplaintItem[]>('/stats?type=top_complaints')
  }

  // --- Feedback Explorer ---
  async getFeedback(params: {
    department?: string
    category?: string
    sentiment?: string
    limit?: number
    offset?: number
  } = {}): Promise<{ count: number; items: FeedbackRecord[] }> {
    const query = new URLSearchParams()
    if (params.department) query.set('department', params.department)
    if (params.category) query.set('category', params.category)
    if (params.sentiment) query.set('sentiment', params.sentiment)
    if (params.limit) query.set('limit', String(params.limit))
    if (params.offset !== undefined) query.set('offset', String(params.offset))

    return this.request<{ count: number; items: FeedbackRecord[] }>(`/feedback?${query.toString()}`)
  }

  // --- GenAI RAG Chat ---
  async askChat(question: string): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ question }),
    })
  }

  // --- GenAI ReAct Agent ---
  async askAgent(question: string): Promise<AgentResponse> {
    return this.request<AgentResponse>('/agent', {
      method: 'POST',
      body: JSON.stringify({ question }),
    })
  }

  // --- Admin Presigned Upload URL ---
  async getUploadUrl(filename: string): Promise<{ upload_url: string; batch_id: string; s3_key: string }> {
    return this.request<{ upload_url: string; batch_id: string; s3_key: string }>('/upload-url', {
      method: 'POST',
      body: JSON.stringify({ filename }),
    })
  }

  // --- Pipeline Status ---
  async getPipelineStatus(batchId: string): Promise<PipelineStatusResponse> {
    return this.request<PipelineStatusResponse>(`/pipeline-status?batch_id=${encodeURIComponent(batchId)}`)
  }

  // --- Upload CSV to S3 with Progress Bar ---
  uploadCsvToS3(
    presignedUrl: string,
    file: File,
    onProgress?: (percent: number) => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('PUT', presignedUrl, true)
      xhr.setRequestHeader('Content-Type', 'text/csv')

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          const percent = Math.round((e.loaded / e.total) * 100)
          onProgress(percent)
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve()
        } else {
          reject(new Error(`S3 upload failed with status ${xhr.status}`))
        }
      }

      xhr.onerror = () => reject(new Error('Network error during S3 upload'))
      xhr.send(file)
    })
  }
}

export const api = new ApiService()
