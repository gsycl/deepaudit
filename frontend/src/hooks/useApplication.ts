import { useQuery } from '@tanstack/react-query'
import { fetchApplication } from '../api/client'

export function useApplication(id: string) {
  return useQuery({
    queryKey: ['application', id],
    queryFn: () => fetchApplication(id),
    enabled: !!id,
  })
}
