import axios from 'axios'
import type {
  ApplicationSummary,
  ApplicationDetail,
  PaginatedApplicationList,
  GraphData,
} from '../types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

export interface ApplicationsQueryParams {
  status?: string
  min_risk?: number
  max_risk?: number
  program_type?: string
  page?: number
  page_size?: number
}

export interface DecisionPayload {
  action: 'approve' | 'deny' | 'flag'
  auditor_name: string
  notes?: string
}

export const fetchApplications = async (
  params: ApplicationsQueryParams = {}
): Promise<PaginatedApplicationList> => {
  const { data } = await api.get('/applications', { params })
  return data
}

export const fetchApplication = async (id: string): Promise<ApplicationDetail> => {
  const { data } = await api.get(`/applications/${id}`)
  return data
}

export const submitDecision = async (
  id: string,
  payload: DecisionPayload
): Promise<ApplicationSummary> => {
  const { data } = await api.post(`/applications/${id}/decision`, payload)
  return data
}

export const reanalyzeApplication = async (id: string): Promise<ApplicationDetail> => {
  const { data } = await api.post(`/fraud/analyze/${id}`)
  return data
}

export const fetchGraph = async (params: { min_risk?: number; program_type?: string } = {}): Promise<GraphData> => {
  const { data } = await api.get('/graph', { params })
  return data
}

export const fetchHealth = async (): Promise<{ status: string }> => {
  const { data } = await api.get('/health')
  return data
}

export interface StatsData {
  total: number
  risk_buckets: { label: string; count: number }[]
  status_counts: { status: string; count: number }[]
}

export const fetchStats = async (): Promise<StatsData> => {
  const { data } = await api.get('/applications/stats')
  return data
}
