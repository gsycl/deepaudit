import { useQuery } from '@tanstack/react-query'
import { fetchGraph } from '../api/client'

export function useGraph(params: { min_risk?: number; program_type?: string } = {}) {
  return useQuery({
    queryKey: ['graph', params],
    queryFn: () => fetchGraph(params),
    staleTime: 60_000,
  })
}
