import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, XCircle, Flag } from 'lucide-react'
import { submitDecision } from '../api/client'

interface Props {
  applicationId: string
  currentStatus: string
}

type Action = 'approve' | 'deny' | 'flag'

const actionConfig: Record<Action, { label: string; icon: typeof CheckCircle; cls: string; newStatus: string }> = {
  approve: { label: 'Approve', icon: CheckCircle, cls: 'bg-green-600 hover:bg-green-700 text-white', newStatus: 'approved' },
  deny: { label: 'Deny', icon: XCircle, cls: 'bg-red-600 hover:bg-red-700 text-white', newStatus: 'denied' },
  flag: { label: 'Flag for Review', icon: Flag, cls: 'bg-purple-600 hover:bg-purple-700 text-white', newStatus: 'flagged' },
}

export default function AuditorActions({ applicationId, currentStatus }: Props) {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState<Action | null>(null)
  const [auditorName, setAuditorName] = useState('')
  const [notes, setNotes] = useState('')
  const [success, setSuccess] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (action: Action) =>
      submitDecision(applicationId, { action, auditor_name: auditorName, notes: notes || undefined }),
    onSuccess: (data, action) => {
      queryClient.invalidateQueries({ queryKey: ['application', applicationId] })
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      setSuccess(`Application ${actionConfig[action].newStatus}.`)
      setOpen(null)
      setAuditorName('')
      setNotes('')
    },
  })

  if (success) {
    return (
      <div className="rounded-lg bg-green-50 border border-green-200 p-4 text-sm text-green-700 font-medium">
        {success}
      </div>
    )
  }

  return (
    <div>
      <div className="flex gap-2 flex-wrap">
        {(Object.keys(actionConfig) as Action[]).map((action) => {
          const { label, icon: Icon, cls } = actionConfig[action]
          const isCurrentStatus = currentStatus === actionConfig[action].newStatus
          return (
            <button
              key={action}
              disabled={isCurrentStatus}
              onClick={() => setOpen(action)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${cls}`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          )
        })}
      </div>

      {open && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">
                {actionConfig[open].label} Application
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Your Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={auditorName}
                    onChange={(e) => setAuditorName(e.target.value)}
                    placeholder="Auditor name"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={3}
                    placeholder="Optional notes for the audit log..."
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  />
                </div>
                {mutation.isError && (
                  <p className="text-sm text-red-600">Failed to submit decision. Please try again.</p>
                )}
              </div>
            </div>
            <div className="px-6 py-4 bg-gray-50 rounded-b-xl flex justify-end gap-3">
              <button
                onClick={() => setOpen(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                disabled={!auditorName.trim() || mutation.isPending}
                onClick={() => mutation.mutate(open)}
                className={`px-4 py-2 text-sm font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed ${actionConfig[open].cls}`}
              >
                {mutation.isPending ? 'Submitting...' : `Confirm ${actionConfig[open].label}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
