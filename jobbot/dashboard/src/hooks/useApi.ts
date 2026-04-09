/**
 * React Hooks for JobBot API
 * 
 * Provides convenient hooks for data fetching with:
 * - Automatic loading states
 * - Error handling
 * - Caching via SWR
 * - Optimistic updates
 * - Retry logic
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import useSWR, { mutate as swrMutate, SWRConfiguration } from 'swr';
import { api, ApiResponse, ApiError } from '@/lib/api';

// ============================================================================
// TYPES
// ============================================================================

interface UseApiOptions extends SWRConfiguration {
  skip?: boolean;
  onSuccess?: (data: any) => void;
  onError?: (error: ApiError) => void;
}

interface UseApiMutationOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: ApiError) => void;
  invalidateKeys?: string[];
  optimisticData?: T;
}

interface UseApiState<T> {
  data: T | undefined;
  error: ApiError | null;
  isLoading: boolean;
  isValidating: boolean;
  mutate: (data?: T, shouldRevalidate?: boolean) => Promise<any>;
}

// ============================================================================
// SWR CONFIGURATION
// ============================================================================

const swrConfig: SWRConfiguration = {
  revalidateOnFocus: false,
  revalidateOnReconnect: true,
  dedupingInterval: 2000,
  errorRetryCount: 3,
  errorRetryInterval: 5000,
  shouldRetryOnError: (err) => {
    // Don't retry on 4xx errors (client errors)
    if (err?.status >= 400 && err?.status < 500) {
      return false;
    }
    return true;
  },
};

// Custom fetcher that uses our api client
const fetcher = async <T>(url: string): Promise<T> => {
  const response = await api.get<T>(url);
  if (response.error) {
    const error = new Error(response.error.message) as any;
    error.status = response.error.status;
    error.info = response.error;
    throw error;
  }
  if (response.data === undefined) {
    throw new Error('No data returned');
  }
  return response.data;
};

// ============================================================================
// DATA FETCHING HOOKS
// ============================================================================

/**
 * Generic hook for GET requests with SWR
 */
export function useApi<T>(
  key: string | null,
  options: UseApiOptions = {}
): UseApiState<T> {
  const { skip, onSuccess, onError, ...swrOptions } = options;
  
  const { data, error, isLoading, isValidating, mutate } = useSWR<T>(
    skip ? null : key,
    fetcher,
    {
      ...swrConfig,
      ...swrOptions,
      onSuccess: (data) => {
        onSuccess?.(data);
        swrOptions.onSuccess?.(data);
      },
      onError: (err) => {
        const apiError: ApiError = {
          status: err.status || 500,
          message: err.message,
          detail: err.info?.detail,
          code: err.info?.code,
        };
        onError?.(apiError);
        swrOptions.onError?.(err);
      },
    }
  );

  return {
    data,
    error: error ? {
      status: error.status || 500,
      message: error.message,
      detail: error.info?.detail,
      code: error.info?.code,
    } : null,
    isLoading,
    isValidating,
    mutate,
  };
}

/**
 * Hook for current user data
 */
export function useMe(options: UseApiOptions = {}) {
  return useApi<any>('/auth/me', options);
}

/**
 * Hook for user dashboard data
 */
export function useDashboard(options: UseApiOptions = {}) {
  return useApi<any>('/users/dashboard', {
    refreshInterval: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Hook for user subscription status
 */
export function useSubscription(options: UseApiOptions = {}) {
  return useApi<any>('/subscriptions/status', options);
}

/**
 * Hook for available plans
 */
export function usePlans(options: UseApiOptions = {}) {
  return useApi<any>('/subscriptions/plans', {
    revalidateOnFocus: false,
    ...options,
  });
}

/**
 * Hook for job search with debouncing
 */
export function useJobSearch(
  query: string,
  options: { modality?: string; location?: string; limit?: number } = {},
  apiOptions: UseApiOptions = {}
) {
  const { modality = 'all', location, limit = 20 } = options;
  
  const params = new URLSearchParams();
  if (query) params.set('q', query);
  if (modality !== 'all') params.set('modality', modality);
  if (location) params.set('location', location);
  params.set('limit', limit.toString());
  
  const key = query ? `/jobs/search?${params.toString()}` : null;
  
  return useApi<any>(key, {
    dedupingInterval: 1000,
    ...apiOptions,
  });
}

/**
 * Hook for user's job applications
 */
export function useApplications(options: UseApiOptions = {}) {
  return useApi<any>('/jobs/applications', {
    refreshInterval: 60000, // 1 minute
    ...options,
  });
}

/**
 * Hook for usage statistics
 */
export function useUsage(options: UseApiOptions = {}) {
  return useApi<any>('/users/usage', {
    refreshInterval: 60000,
    ...options,
  });
}

/**
 * Hook for user preferences
 */
export function usePreferences(options: UseApiOptions = {}) {
  return useApi<any>('/users/preferences', options);
}

// ============================================================================
// MUTATION HOOKS
// ============================================================================

/**
 * Generic mutation hook for POST/PUT/PATCH/DELETE
 */
export function useApiMutation<T, V = any>(
  method: 'post' | 'put' | 'patch' | 'delete',
  endpoint: string,
  options: UseApiMutationOptions<T> = {}
) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  
  const { onSuccess, onError, invalidateKeys, optimisticData } = options;

  const mutate = useCallback(async (variables?: V): Promise<T | null> => {
    setIsLoading(true);
    setError(null);
    
    // Optimistic update
    if (optimisticData && invalidateKeys) {
      invalidateKeys.forEach(key => {
        swrMutate(key, optimisticData, false);
      });
    }
    
    try {
      let response: ApiResponse<T>;
      
      switch (method) {
        case 'post':
          response = await api.post<T>(endpoint, variables);
          break;
        case 'put':
          response = await api.put<T>(endpoint, variables);
          break;
        case 'patch':
          response = await api.patch<T>(endpoint, variables);
          break;
        case 'delete':
          response = await api.delete<T>(endpoint);
          break;
      }
      
      if (response.error) {
        throw response.error;
      }
      
      const result = response.data as T;
      
      // Invalidate cache keys
      if (invalidateKeys) {
        invalidateKeys.forEach(key => {
          swrMutate(key);
        });
      }
      
      onSuccess?.(result);
      return result;
      
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      onError?.(apiError);
      return null;
      
    } finally {
      setIsLoading(false);
    }
  }, [method, endpoint, onSuccess, onError, invalidateKeys, optimisticData]);

  return {
    mutate,
    isLoading,
    error,
  };
}

/**
 * Hook for tracking job application
 */
export function useTrackApplication(options: UseApiMutationOptions<any> = {}) {
  return useApiMutation('post', '/jobs/track', {
    invalidateKeys: ['/jobs/applications', '/users/dashboard'],
    ...options,
  });
}

/**
 * Hook for updating application status
 */
export function useUpdateApplication(
  appId: number,
  options: UseApiMutationOptions<any> = {}
) {
  return useApiMutation('patch', `/jobs/applications/${appId}`, {
    invalidateKeys: ['/jobs/applications', '/users/dashboard'],
    ...options,
  });
}

/**
 * Hook for updating user preferences
 */
export function useUpdatePreferences(options: UseApiMutationOptions<any> = {}) {
  return useApiMutation('post', '/users/preferences', {
    invalidateKeys: ['/users/preferences', '/users/dashboard'],
    ...options,
  });
}

/**
 * Hook for creating checkout session
 */
export function useCreateCheckout(options: UseApiMutationOptions<any> = {}) {
  return useApiMutation('post', '/subscriptions/create-checkout', {
    invalidateKeys: ['/subscriptions/status'],
    ...options,
  });
}

/**
 * Hook for cancelling subscription
 */
export function useCancelSubscription(options: UseApiMutationOptions<any> = {}) {
  return useApiMutation('post', '/subscriptions/cancel', {
    invalidateKeys: ['/subscriptions/status', '/users/me', '/users/dashboard'],
    ...options,
  });
}

// ============================================================================
// AUTHENTICATION HOOKS
// ============================================================================

/**
 * Hook for login
 */
export function useLogin(options: UseApiMutationOptions<any> = {}) {
  return useApiMutation('post', '/auth/token', {
    invalidateKeys: ['/auth/me', '/users/dashboard'],
    ...options,
  });
}

/**
 * Hook for registration
 */
export function useRegister(options: UseApiMutationOptions<any> = {}) {
  return useApiMutation('post', '/auth/register', {
    invalidateKeys: ['/auth/me'],
    ...options,
  });
}

/**
 * Hook for logout
 */
export function useLogout(options: UseApiMutationOptions<any> = {}) {
  const { mutate, isLoading, error } = useApiMutation('post', '/auth/logout', {
    ...options,
  });
  
  const logout = useCallback(async () => {
    const result = await mutate();
    if (result !== null) {
      api.clearAuth();
      // Clear all SWR cache
      await swrMutate(() => true, undefined, { revalidate: false });
      window.location.href = '/login';
    }
    return result;
  }, [mutate]);
  
  return {
    logout,
    isLoading,
    error,
  };
}

// ============================================================================
// UTILITY EXPORTS
// ============================================================================

export { api, swrMutate as mutate };
export type { ApiResponse, ApiError, UseApiOptions, UseApiState };
