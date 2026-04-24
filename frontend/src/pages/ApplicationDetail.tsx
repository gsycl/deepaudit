import { useParams, Link } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'
import { ArrowLeft, RefreshCw, Skull, CheckCircle, XCircle, Search, AlertTriangle } from 'lucide-react'
import { useApplication } from '../hooks/useApplication'
import SignalCard from '../components/SignalCard'
import StatusBadge from '../components/StatusBadge'
import RiskBadge from '../components/RiskBadge'
import AuditorActions from '../components/AuditorActions'
import { reanalyzeApplication } from '../api/client'

const AI_REC_CONFIG = {
  approve: { cls: 'bg-green-50 border-green-300', titleCls: 'text-green-800', icon: CheckCircle, iconCls: 'text-green-600' },
  deny: { cls: 'bg-red-50 border-red-300', titleCls: 'text-red-800', icon: XCircle, iconCls: 'text-red-600' },
  investigate: { cls: 'bg-orange-50 border-orange-300', titleCls: 'text-orange-800', icon: Search, iconCls: 'text-orange-600' },
}

export default function ApplicationDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const { data: app, isLoading, isError } = useApplication(id!)

  const reanalyzeMutation = useMutation({
    mutationFn: () => reanalyzeApplication(id!),
    onSuccess: (data) => {
      queryClient.setQueryData(['application', id], data)
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        Loading application...
      </div>
    )
  }

  if (isError || !app) {
    return (
      <div className="flex items-center justify-center h-64 text-red-500 gap-2">
        <AlertTriangle className="w-5 h-5" /> Application not found.
      </div>
    )
  }

  const aiConfig = app.ai_recommendation ? AI_REC_CONFIG[app.ai_recommendation] : null
  const AiIcon = aiConfig?.icon ?? Search
  const age = Math.floor((Date.now() - new Date(app.applicant_dob).getTime()) / (365.25 * 24 * 60 * 60 * 1000))
  const riskData = [{ name: 'Risk', value: app.risk_score ?? 0, fill: app.risk_score! >= 81 ? '#ef4444' : app.risk_score! >= 61 ? '#f97316' : app.risk_score! >= 31 ? '#fbbf24' : '#22c55e' }]

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/" className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
        <span className="text-gray-300">/</span>
        <span className="text-sm text-gray-700 font-medium">
          {app.applicant_first_name} {app.applicant_last_name}
        </span>
        <div className="ml-auto flex items-center gap-3">
          <StatusBadge status={app.status} />
          <RiskBadge score={app.risk_score} size="md" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT: Applicant Info */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-gray-900">
                    {app.applicant_first_name} {app.applicant_last_name}
                  </h2>
                  {app.applicant_is_deceased && (
                    <span className="flex items-center gap-1 text-xs text-red-700 bg-red-100 border border-red-200 px-2 py-0.5 rounded-full font-medium">
                      <Skull className="w-3 h-3" /> Deceased
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-0.5">Age {age} · {app.program_type.toUpperCase()}</p>
              </div>
            </div>

            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div><dt className="text-gray-400">Phone</dt><dd className="font-medium">{app.applicant_phone}</dd></div>
              <div><dt className="text-gray-400">Email</dt><dd className="font-medium truncate">{app.applicant_email}</dd></div>
              <div><dt className="text-gray-400">DOB</dt><dd className="font-medium">{app.applicant_dob}</dd></div>
              <div><dt className="text-gray-400">Claim Period</dt><dd className="font-medium">{app.claim_start_date} – {app.claim_end_date}</dd></div>
              <div><dt className="text-gray-400">Weekly Benefit</dt><dd className="font-medium text-green-700">${Number(app.weekly_benefit_amount ?? 0).toFixed(2)}</dd></div>
              <div><dt className="text-gray-400">Submitted</dt><dd className="font-medium">{new Date(app.submitted_at).toLocaleDateString()}</dd></div>
            </dl>
          </div>

          {app.addresses.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Address</h3>
              {app.addresses.map((addr) => (
                <div key={addr.id} className="text-sm text-gray-600">
                  <p>{addr.street}</p>
                  <p>{addr.city}, {addr.state} {addr.zip_code}</p>
                </div>
              ))}
            </div>
          )}

          {app.financial_records.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Financial Records</h3>
              {app.financial_records.map((f) => (
                <div key={f.id} className="text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Institution</span>
                    <span className="font-medium">{f.institution_name ?? 'Unknown'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Monthly Income</span>
                    <span className="font-medium">${Number(f.monthly_income_reported ?? 0).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {app.employment_history.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Employment History</h3>
              <div className="space-y-3">
                {app.employment_history.map((emp) => (
                  <div key={emp.id} className="text-sm">
                    <p className="font-medium text-gray-800">{emp.employer_name}</p>
                    <p className="text-gray-500">{emp.start_date} – {emp.end_date ?? <span className="text-red-500 font-semibold">MISSING</span>}</p>
                    <p className="text-gray-500 capitalize">Reason: {emp.separation_reason} · ${Number(emp.reported_salary ?? 0).toLocaleString()}/yr</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {app.weekly_certifications.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Weekly Certifications ({app.weekly_certifications.length} weeks)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-gray-400 border-b border-gray-100">
                      <th className="pb-1 text-left">Week</th>
                      <th className="pb-1 text-center">Worked</th>
                      <th className="pb-1 text-right">Earnings</th>
                      <th className="pb-1 text-right">Job Contacts</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {app.weekly_certifications.map((c) => (
                      <tr key={c.id}>
                        <td className="py-1 text-gray-600">{c.week_start}</td>
                        <td className="py-1 text-center">{c.did_work ? '✓' : '–'}</td>
                        <td className="py-1 text-right">${Number(c.reported_earnings).toFixed(0)}</td>
                        <td className={`py-1 text-right font-medium ${c.job_search_contacts <= 3 ? 'text-orange-600' : 'text-gray-700'}`}>{c.job_search_contacts}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* CENTER: Risk Analysis */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-700">Risk Score</h3>
              <button
                onClick={() => reanalyzeMutation.mutate()}
                disabled={reanalyzeMutation.isPending}
                className={`flex items-center gap-1.5 text-xs font-medium transition-all ${
                  reanalyzeMutation.isPending
                    ? 'text-orange-500 cursor-not-allowed'
                    : reanalyzeMutation.isSuccess
                    ? 'text-green-600'
                    : 'text-blue-600 hover:text-blue-800'
                }`}
              >
                {reanalyzeMutation.isPending ? (
                  <>
                    <span className="text-base leading-none animate-bounce">🔍</span>
                    <span>Analyzing<span className="animate-pulse">…</span></span>
                  </>
                ) : reanalyzeMutation.isSuccess ? (
                  <>
                    <span className="text-base leading-none">✅</span>
                    <span>Done!</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Re-analyze</span>
                  </>
                )}
              </button>
            </div>
            <div className="flex items-center gap-4">
              <div className="w-28 h-28 flex-shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart
                    cx="50%" cy="50%"
                    innerRadius="60%" outerRadius="100%"
                    startAngle={90} endAngle={90 - 360 * ((app.risk_score ?? 0) / 100)}
                    data={riskData}
                    barSize={12}
                  >
                    <RadialBar dataKey="value" cornerRadius={6} />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
              <div>
                <div className="text-4xl font-black text-gray-900">{app.risk_score ?? 'N/A'}</div>
                <div className="text-sm text-gray-500">out of 100</div>
                {app.last_analyzed_at && (
                  <div className="text-xs text-gray-400 mt-1">
                    Last run: {new Date(app.last_analyzed_at).toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 relative">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              Fraud Signals ({app.fraud_signals.length})
            </h3>
            {reanalyzeMutation.isPending && (
              <div className="absolute inset-0 bg-white/80 rounded-xl flex flex-col items-center justify-center gap-2 z-10">
                <span className="text-3xl animate-spin">🔍</span>
                <p className="text-sm font-medium text-orange-600 animate-pulse">Re-analyzing signals…</p>
              </div>
            )}
            {app.fraud_signals.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">No fraud signals detected.</p>
            ) : (
              <div className="space-y-3">
                {app.fraud_signals
                  .sort((a, b) => b.score_contribution - a.score_contribution)
                  .map((signal) => (
                    <SignalCard key={signal.id} signal={signal} />
                  ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: AI Panel + Auditor Actions */}
        <div className="space-y-4">
          {aiConfig ? (
            <div className={`rounded-xl border-2 p-5 ${aiConfig.cls}`}>
              <div className="flex items-center gap-2 mb-3">
                <AiIcon className={`w-5 h-5 ${aiConfig.iconCls}`} />
                <h3 className={`text-base font-bold uppercase tracking-wide ${aiConfig.titleCls}`}>
                  {app.ai_recommendation}
                </h3>
                {app.ai_confidence && (
                  <span className="ml-auto text-xs text-gray-500 font-medium capitalize">
                    {app.ai_confidence} confidence
                  </span>
                )}
              </div>

              {app.ai_headline && (
                <p className="text-sm font-semibold text-gray-800 mb-3">{app.ai_headline}</p>
              )}

              {app.ai_explanation && (
                <p className="text-sm text-gray-700 leading-relaxed mb-4">{app.ai_explanation}</p>
              )}

              {app.ai_key_signals && app.ai_key_signals.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Key Signals</p>
                  <div className="flex flex-wrap gap-2">
                    {app.ai_key_signals.map((s) => (
                      <span key={s} className="text-xs bg-white/60 border border-gray-200 rounded-full px-2.5 py-0.5 text-gray-700">
                        {s.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {app.ai_suggested_action && (
                <div className="rounded-lg bg-white/50 border border-current/10 p-3">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Suggested Action</p>
                  <p className="text-sm text-gray-700">{app.ai_suggested_action}</p>
                </div>
              )}

              {app.ai_analyzed_at && (
                <p className="text-xs text-gray-400 mt-3">
                  AI analyzed: {new Date(app.ai_analyzed_at).toLocaleString()}
                </p>
              )}
            </div>
          ) : (
            <div className="rounded-xl border-2 border-dashed border-gray-200 bg-gray-50 p-5 text-center">
              <Search className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500 font-medium">AI Analysis Pending</p>
              <p className="text-xs text-gray-400 mt-1">Click Re-analyze to generate a recommendation</p>
            </div>
          )}

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Auditor Decision</h3>
            <AuditorActions applicationId={app.id} currentStatus={app.status} />
          </div>
        </div>
      </div>
    </div>
  )
}
