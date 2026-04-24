import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { AlertTriangle, ChevronRight, RefreshCw } from 'lucide-react'
import { useApplications } from '../hooks/useApplications'
import { useStats } from '../hooks/useStats'
import RiskBadge from '../components/RiskBadge'
import StatusBadge from '../components/StatusBadge'
import type { ApplicationStatus, ProgramType } from '../types'

const STATUS_OPTIONS: ApplicationStatus[] = ['pending', 'approved', 'denied', 'flagged', 'under_review']
const PROGRAM_OPTIONS: ProgramType[] = ['unemployment', 'medicare', 'snap', 'disability']

const RISK_BUCKETS = [
  { label: '0-20', min: 0, max: 20, fill: '#22c55e' },
  { label: '21-40', min: 21, max: 40, fill: '#86efac' },
  { label: '41-60', min: 41, max: 60, fill: '#fbbf24' },
  { label: '61-80', min: 61, max: 80, fill: '#f97316' },
  { label: '81-100', min: 81, max: 100, fill: '#ef4444' },
]

const PIE_COLORS: Record<ApplicationStatus, string> = {
  pending: '#3b82f6',
  approved: '#22c55e',
  denied: '#ef4444',
  flagged: '#a855f7',
  under_review: '#f59e0b',
}

const AI_REC_COLORS: Record<string, string> = {
  approve: 'text-green-700 bg-green-50 border-green-200',
  deny: 'text-red-700 bg-red-50 border-red-200',
  investigate: 'text-orange-700 bg-orange-50 border-orange-200',
}

export default function Dashboard() {
  const [selectedStatuses, setSelectedStatuses] = useState<ApplicationStatus[]>([])
  const [minRisk, setMinRisk] = useState<number | undefined>()
  const [maxRisk, setMaxRisk] = useState<number | undefined>()
  const [programType, setProgramType] = useState<string>('')
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 15

  const { data, isLoading, isError, refetch } = useApplications({
    status: selectedStatuses.length === 1 ? selectedStatuses[0] : undefined,
    min_risk: minRisk,
    max_risk: maxRisk,
    program_type: programType || undefined,
    page,
    page_size: PAGE_SIZE,
  })

  const toggleStatus = (s: ApplicationStatus) => {
    setPage(1)
    setSelectedStatuses((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    )
  }

  const { data: stats } = useStats()
  const items = data?.items ?? []

  const riskBucketData = (stats?.risk_buckets ?? RISK_BUCKETS.map(b => ({ label: b.label, count: 0 }))).map((b) => {
    const fill = RISK_BUCKETS.find(r => r.label === b.label)?.fill ?? '#94a3b8'
    return { ...b, fill }
  })

  const statusCounts = (stats?.status_counts ?? []).map((s) => ({
    name: s.status.replace('_', ' '),
    value: s.count,
    fill: PIE_COLORS[s.status as ApplicationStatus] ?? '#94a3b8',
  })).filter((x) => x.value > 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Applications Queue</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {stats?.total ?? data?.total ?? 0} total applications — sorted by risk score
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Risk Score Distribution</h2>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={riskBucketData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip formatter={(v) => [`${v} applications`, 'Count']} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {riskBucketData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Status Breakdown</h2>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={statusCounts} dataKey="value" cx="50%" cy="50%" outerRadius={60} paddingAngle={2}>
                {statusCounts.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip formatter={(v, name) => [`${v}`, name]} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {statusCounts.map((s) => (
              <span key={s.name} className="flex items-center gap-1 text-xs text-gray-600">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: s.fill }} />
                {s.name} ({s.value})
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Filters sidebar */}
        <aside className="w-52 flex-shrink-0 space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Status</h3>
            <div className="space-y-2">
              {STATUS_OPTIONS.map((s) => (
                <label key={s} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedStatuses.includes(s)}
                    onChange={() => toggleStatus(s)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 capitalize">{s.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Risk Score</h3>
            <div className="space-y-2">
              <div>
                <label className="text-xs text-gray-500">Min</label>
                <input
                  type="number"
                  min={0} max={100}
                  value={minRisk ?? ''}
                  onChange={(e) => { setPage(1); setMinRisk(e.target.value ? +e.target.value : undefined) }}
                  placeholder="0"
                  className="w-full mt-1 border border-gray-300 rounded px-2 py-1 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">Max</label>
                <input
                  type="number"
                  min={0} max={100}
                  value={maxRisk ?? ''}
                  onChange={(e) => { setPage(1); setMaxRisk(e.target.value ? +e.target.value : undefined) }}
                  placeholder="100"
                  className="w-full mt-1 border border-gray-300 rounded px-2 py-1 text-sm"
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Program</h3>
            <select
              value={programType}
              onChange={(e) => { setPage(1); setProgramType(e.target.value) }}
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm bg-white"
            >
              <option value="">All programs</option>
              {PROGRAM_OPTIONS.map((p) => (
                <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
              ))}
            </select>
          </div>
        </aside>

        {/* Table */}
        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            {isLoading ? (
              <div className="flex items-center justify-center h-64 text-gray-400">Loading...</div>
            ) : isError ? (
              <div className="flex items-center justify-center h-64 text-red-500 gap-2">
                <AlertTriangle className="w-5 h-5" /> Failed to load. Is the backend running?
              </div>
            ) : items.length === 0 ? (
              <div className="flex items-center justify-center h-64 text-gray-400">No applications found.</div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Applicant</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Program</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Submitted</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Risk</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Status</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">AI Rec</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {items.map((app) => (
                    <tr key={app.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-medium text-gray-900">{app.applicant_name}</td>
                      <td className="px-4 py-3">
                        <span className="capitalize text-gray-600 text-xs px-2 py-0.5 bg-gray-100 rounded-full">
                          {app.program_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {new Date(app.submitted_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <RiskBadge score={app.risk_score} size="sm" />
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={app.status} />
                      </td>
                      <td className="px-4 py-3">
                        {app.ai_recommendation ? (
                          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${AI_REC_COLORS[app.ai_recommendation] ?? ''}`}>
                            {app.ai_recommendation}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">Pending</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          to={`/applications/${app.id}`}
                          className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          View <ChevronRight className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination */}
          {data && data.total > PAGE_SIZE && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, data.total)} of {data.total}
              </p>
              <div className="flex gap-2">
                <button
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
                >
                  Previous
                </button>
                <button
                  disabled={page * PAGE_SIZE >= data.total}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
