interface RiskBadgeProps {
  score: number | null
  size?: 'sm' | 'md' | 'lg'
}

const colorMap = (score: number) => {
  if (score >= 81) return 'bg-red-100 text-red-800 border-red-300'
  if (score >= 61) return 'bg-orange-100 text-orange-800 border-orange-300'
  if (score >= 31) return 'bg-yellow-100 text-yellow-800 border-yellow-300'
  return 'bg-green-100 text-green-800 border-green-300'
}

const barColor = (score: number) => {
  if (score >= 81) return 'bg-red-500'
  if (score >= 61) return 'bg-orange-500'
  if (score >= 31) return 'bg-yellow-500'
  return 'bg-green-500'
}

export default function RiskBadge({ score, size = 'md' }: RiskBadgeProps) {
  if (score === null || score === undefined) {
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200">N/A</span>
  }

  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : size === 'lg' ? 'text-base px-4 py-1.5 font-bold' : 'text-sm px-3 py-1 font-semibold'

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${colorMap(score)} ${sizeClass}`}>
      <span className={`w-2 h-2 rounded-full ${barColor(score)}`} />
      {score}
    </span>
  )
}
