import type { FraudSignalSchema, SignalSeverity } from '../types'
import { AlertTriangle, AlertCircle, Info, XCircle } from 'lucide-react'

const severityConfig: Record<SignalSeverity, { cls: string; icon: typeof AlertTriangle; label: string }> = {
  low: { cls: 'border-gray-200 bg-gray-50', icon: Info, label: 'Low' },
  medium: { cls: 'border-yellow-200 bg-yellow-50', icon: AlertTriangle, label: 'Medium' },
  high: { cls: 'border-orange-200 bg-orange-50', icon: AlertCircle, label: 'High' },
  critical: { cls: 'border-red-200 bg-red-50', icon: XCircle, label: 'Critical' },
}

const iconColor: Record<SignalSeverity, string> = {
  low: 'text-gray-400',
  medium: 'text-yellow-500',
  high: 'text-orange-500',
  critical: 'text-red-500',
}

export default function SignalCard({ signal }: { signal: FraudSignalSchema }) {
  const { cls, icon: Icon, label } = severityConfig[signal.severity]
  return (
    <div className={`rounded-lg border p-4 ${cls}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${iconColor[signal.severity]}`} />
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold text-gray-500">{signal.rule_id}</span>
              <span className="text-sm font-semibold text-gray-800">{signal.signal_type.replace(/_/g, ' ')}</span>
              <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                signal.severity === 'critical' ? 'bg-red-200 text-red-800' :
                signal.severity === 'high' ? 'bg-orange-200 text-orange-800' :
                signal.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                'bg-gray-200 text-gray-700'
              }`}>{label}</span>
            </div>
            <p className="text-sm text-gray-600 mt-1">{signal.description}</p>
            {signal.metadata && Object.keys(signal.metadata).length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {Object.entries(signal.metadata).map(([k, v]) => (
                  <span key={k} className="text-xs bg-white/70 border border-current/20 rounded px-2 py-0.5 font-mono">
                    {k}: {String(v)}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex-shrink-0 text-right">
          <span className="text-sm font-bold text-gray-700">+{signal.score_contribution}</span>
          <p className="text-xs text-gray-400">pts</p>
        </div>
      </div>
    </div>
  )
}
