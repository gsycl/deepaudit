import { useQuery } from '@tanstack/react-query'
import { fetchApplications } from '../api/client'
import type { ApplicationsQueryParams } from '../api/client'

export function useApplications(params: ApplicationsQueryParams = {}) {
  return useQuery({
    queryKey: ['applications', params],
    queryFn: () => fetchApplications(params),
  })
}
