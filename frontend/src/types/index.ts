export type ProgramType = 'unemployment' | 'medicare' | 'snap' | 'disability'
export type ApplicationStatus = 'pending' | 'approved' | 'denied' | 'flagged' | 'under_review'
export type SignalSeverity = 'low' | 'medium' | 'high' | 'critical'
export type AIRecommendation = 'approve' | 'deny' | 'investigate'

export interface AddressSchema {
  id: string
  street: string
  city: string
  state: string
  zip_code: string
  lat: number | null
  lon: number | null
}

export interface EmploymentHistorySchema {
  id: string
  employer_name: string
  start_date: string
  end_date: string | null
  separation_reason: string
  reported_salary: number | null
  is_verified: boolean
}

export interface WeeklyCertificationSchema {
  id: string
  week_start: string
  did_work: boolean
  reported_earnings: number
  job_search_contacts: number
  submitted_at: string
}

export interface FraudSignalSchema {
  id: string
  rule_id: string
  signal_type: string
  severity: SignalSeverity
  score_contribution: number
  description: string
  metadata: Record<string, unknown> | null
  detected_at: string
}

export interface FinancialRecordSchema {
  id: string
  institution_name: string | null
  account_type: string
  monthly_income_reported: number | null
}

export interface ApplicationSummary {
  id: string
  program_type: ProgramType
  status: ApplicationStatus
  submitted_at: string
  risk_score: number | null
  ai_recommendation: AIRecommendation | null
  ai_headline: string | null
  weekly_benefit_amount: number | null
  applicant_name: string
  applicant_id: string
}

export interface ApplicationDetail {
  id: string
  program_type: ProgramType
  status: ApplicationStatus
  submitted_at: string
  weekly_benefit_amount: number | null
  claim_start_date: string | null
  claim_end_date: string | null
  risk_score: number | null
  ai_recommendation: AIRecommendation | null
  ai_explanation: string | null
  ai_headline: string | null
  ai_confidence: 'low' | 'medium' | 'high' | null
  ai_key_signals: string[] | null
  ai_suggested_action: string | null
  ai_analyzed_at: string | null
  last_analyzed_at: string | null
  applicant_id: string
  applicant_first_name: string
  applicant_last_name: string
  applicant_dob: string
  applicant_is_deceased: boolean
  applicant_phone: string
  applicant_email: string
  addresses: AddressSchema[]
  employment_history: EmploymentHistorySchema[]
  weekly_certifications: WeeklyCertificationSchema[]
  fraud_signals: FraudSignalSchema[]
  financial_records: FinancialRecordSchema[]
}

export interface PaginatedApplicationList {
  total: number
  page: number
  page_size: number
  items: ApplicationSummary[]
}

export interface GraphNode {
  id: string
  label: string
  full_name: string
  risk_score: number
  status: ApplicationStatus
  program_type: ProgramType
  is_deceased: boolean
  ai_recommendation: AIRecommendation | null
}

export interface GraphEdge {
  source: string
  target: string
  relationship: string
  weight: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}
