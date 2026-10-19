import { countryApi } from '@/apis/country.api';
import { useQuery } from '@tanstack/react-query';

// get all (public)
export function useGetCountries(
  staleTime: number = 1000 * 60 * 5,
  gcTime: number = 1000 * 60 * 10,
) {
  return useQuery({
    queryKey: ['countries'],
    queryFn: async () => {
      // Lấy tối đa để đủ cho dropdown lọc (backend mặc định limit = 10).
      const response = await countryApi.getAll({ page: 1, limit: 100 });
      return response.result;
    },
    staleTime: staleTime, // 5 minutes
    gcTime: gcTime, // 10 minutes
  });
}

const useCountry = {
  useGetCountries,
};

export default useCountry;
