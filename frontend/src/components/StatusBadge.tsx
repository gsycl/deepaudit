import type { ApplicationStatus } from '../types'

const config: Record<ApplicationStatus, { label: string; cls: string }> = {
  pending: { label: 'Pending', cls: 'bg-blue-100 text-blue-800 border-blue-200' },
  approved: { label: 'Approved', cls: 'bg-green-100 text-green-800 border-green-200' },
  denied: { label: 'Denied', cls: 'bg-red-100 text-red-800 border-red-200' },
  flagged: { label: 'Flagged', cls: 'bg-purple-100 text-purple-800 border-purple-200' },
  under_review: { label: 'Under Review', cls: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
}

export default function StatusBadge({ status }: { status: ApplicationStatus }) {
  const { label, cls } = config[status] ?? { label: status, cls: 'bg-gray-100 text-gray-700 border-gray-200' }
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {label}
    </span>
  )
}
