export type ApiKeyStatus = 'active' | 'revoked';

export interface ApiKey {
  id: string;
  name: string;
  masked: string;         // e.g. "sk_live_••••••••••••1a2b"
  created_at: string;
  last_used_at: string | null;
  request_count: number;
  status: ApiKeyStatus;
}

export interface CreateApiKeyResponse {
  id: string;
  name: string;
  key: string;            // full plaintext key — shown exactly once
  masked: string;
  created_at: string;
}

export interface ApiKeyListResponse {
  items: ApiKey[];
  total: number;
}

export interface CreateApiKeyRequest {
  name: string;
}

export interface RenameApiKeyRequest {
  name: string;
}
