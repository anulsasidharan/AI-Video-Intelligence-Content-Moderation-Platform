export type UserRole = 'admin' | 'operator' | 'api_consumer';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  organization_id?: string;
  whatsapp_number?: string | null;
  is_active: boolean;
  is_blocked: boolean;
  blocked_at?: string | null;
  blocked_reason?: string | null;
  // Address
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  country?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: 'bearer';
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  whatsapp_number?: string;
}

export interface LoginResponse {
  data: AuthTokens & { user: User };
}
