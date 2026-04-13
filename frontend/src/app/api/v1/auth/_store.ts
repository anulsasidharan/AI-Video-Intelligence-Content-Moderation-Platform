// Shared mock user store for auth and user-management routes.
// Data is persisted to frontend/.mock-data/users.json so registrations
// survive dev-server restarts without needing a real database.

import fs from 'fs';
import path from 'path';

export interface MockUser {
  id: string;
  email: string;
  password: string;
  name: string;
  role: 'admin' | 'operator';
  organization_id: string;
  created_at: string;
  updated_at: string;
}

const DATA_DIR = path.join(process.cwd(), '.mock-data');
const USERS_FILE = path.join(DATA_DIR, 'users.json');

const SEED_USERS: MockUser[] = [
  {
    id: 'user-admin',
    email: 'admin@vidshield.ai',
    password: 'password123',
    name: 'Admin User',
    role: 'admin',
    organization_id: 'org-vidshield-demo',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-03-17T00:00:00Z',
  },
  {
    id: 'user-operator',
    email: 'operator@vidshield.ai',
    password: 'password123',
    name: 'Operator User',
    role: 'operator',
    organization_id: 'org-vidshield-demo',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-03-17T00:00:00Z',
  },
];

function loadFromFile(): MockUser[] {
  try {
    if (fs.existsSync(USERS_FILE)) {
      const raw = fs.readFileSync(USERS_FILE, 'utf-8');
      const parsed = JSON.parse(raw) as MockUser[];
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch {
    // fall through to seeds if file is missing or corrupt
  }
  return SEED_USERS.map((u) => ({ ...u }));
}

export const MOCK_USER_STORE: MockUser[] = loadFromFile();

export function saveStore(): void {
  try {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    fs.writeFileSync(USERS_FILE, JSON.stringify(MOCK_USER_STORE, null, 2), 'utf-8');
  } catch {
    // non-fatal — mock data just won't persist this write
  }
}
