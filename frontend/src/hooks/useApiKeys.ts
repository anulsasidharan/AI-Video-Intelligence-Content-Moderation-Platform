'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api';
import type {
  ApiKey,
  ApiKeyListResponse,
  CreateApiKeyRequest,
  CreateApiKeyResponse,
  RenameApiKeyRequest,
} from '@/types/apiKey';

export const apiKeyKeys = {
  all: ['api-keys'] as const,
  list: () => ['api-keys', 'list'] as const,
};

export function useApiKeys() {
  return useQuery({
    queryKey: apiKeyKeys.list(),
    queryFn: () => apiClient.get<ApiKeyListResponse>('/api-keys'),
  });
}

export function useCreateApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: CreateApiKeyRequest) =>
      apiClient.post<CreateApiKeyResponse>('/api-keys', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: apiKeyKeys.list() });
    },
    onError: () => {
      toast.error('Failed to generate API key');
    },
  });
}

export function useRenameApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: RenameApiKeyRequest }) =>
      apiClient.patch<ApiKey>(`/api-keys/${id}`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: apiKeyKeys.list() });
      toast.success('API key renamed');
    },
    onError: () => {
      toast.error('Failed to rename API key');
    },
  });
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api-keys/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: apiKeyKeys.list() });
      toast.success('API key revoked');
    },
    onError: () => {
      toast.error('Failed to revoke API key');
    },
  });
}
