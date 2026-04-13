/**
 * F-14 — ApiClient tests
 * Note: jest.mock factories are hoisted before variable declarations,
 * so mock state is managed inside the factory closure.
 */

// localStorage mock
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });

// Interceptor capture variables (initialized via interceptors.use calls in the factory)
let requestInterceptorFn: (config: Record<string, unknown>) => Record<string, unknown>;
let responseSuccessFn: (res: unknown) => unknown;

const getMockInstance = () => ({
  get: jest.fn(),
  post: jest.fn(),
  patch: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  request: jest.fn(),
  interceptors: {
    request: {
      use: jest.fn((fn: typeof requestInterceptorFn) => { requestInterceptorFn = fn; }),
    },
    response: {
      use: jest.fn((onOk: typeof responseSuccessFn) => { responseSuccessFn = onOk; }),
    },
  },
});

// Must use inline value, not variable reference (due to hoisting)
jest.mock('axios', () => {
  const real = jest.requireActual('axios');
  const instance = {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    request: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };
  return {
    ...real,
    default: { ...real.default, create: jest.fn(() => instance), post: jest.fn(), isAxiosError: jest.fn() },
    create: jest.fn(() => instance),
    post: jest.fn(),
    isAxiosError: jest.fn((e: unknown) => !!(e && typeof e === 'object' && 'response' in e)),
  };
});

import axios from 'axios';
import { ApiClient } from '@/lib/api';

let mockInstance: ReturnType<typeof getMockInstance>;

beforeEach(() => {
  localStorageMock.clear();
  jest.clearAllMocks();
  mockInstance = getMockInstance();
  (axios.create as jest.Mock).mockReturnValue(mockInstance);
});

function makeClient() {
  const client = new ApiClient('http://localhost:8000/api/v1');
  // Capture interceptors from this instance
  const reqCall = mockInstance.interceptors.request.use.mock.calls[0];
  const resCall = mockInstance.interceptors.response.use.mock.calls[0];
  if (reqCall) requestInterceptorFn = reqCall[0];
  if (resCall) responseSuccessFn = resCall[0];
  return client;
}

describe('ApiClient (F-14)', () => {
  it('creates axios instance with provided baseURL', () => {
    makeClient();
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({ baseURL: 'http://localhost:8000/api/v1' })
    );
  });

  it('attaches Authorization header when access_token exists', () => {
    makeClient();
    localStorageMock.setItem('access_token', 'test-token');
    const config = { headers: {} as Record<string, string> };
    const result = requestInterceptorFn(config as any);
    expect((result as any).headers.Authorization).toBe('Bearer test-token');
  });

  it('does not attach Authorization header when no token', () => {
    makeClient();
    const config = { headers: {} as Record<string, string> };
    const result = requestInterceptorFn(config as any);
    expect((result as any).headers.Authorization).toBeUndefined();
  });

  it('setTokens() persists tokens to localStorage', () => {
    const client = makeClient();
    client.setTokens('access-abc', 'refresh-xyz');
    expect(localStorageMock.getItem('access_token')).toBe('access-abc');
    expect(localStorageMock.getItem('refresh_token')).toBe('refresh-xyz');
  });

  it('clearTokens() removes both tokens from localStorage', () => {
    const client = makeClient();
    localStorageMock.setItem('access_token', 'acc');
    localStorageMock.setItem('refresh_token', 'ref');
    client.clearTokens();
    expect(localStorageMock.getItem('access_token')).toBeNull();
    expect(localStorageMock.getItem('refresh_token')).toBeNull();
  });

  it('get() unwraps response.data', async () => {
    const client = makeClient();
    mockInstance.get.mockResolvedValueOnce({ data: { items: [], total: 0 } });
    const result = await client.get('/videos');
    expect(result).toEqual({ items: [], total: 0 });
  });

  it('post() unwraps response.data', async () => {
    const client = makeClient();
    mockInstance.post.mockResolvedValueOnce({ data: { id: 'new-id' } });
    const result = await client.post('/videos', { title: 'Test' });
    expect(result).toEqual({ id: 'new-id' });
  });

  it('patch() unwraps response.data', async () => {
    const client = makeClient();
    mockInstance.patch.mockResolvedValueOnce({ data: { updated: true } });
    const result = await client.patch('/videos/1', { title: 'New' });
    expect(result).toEqual({ updated: true });
  });

  it('delete() unwraps response.data', async () => {
    const client = makeClient();
    mockInstance.delete.mockResolvedValueOnce({ data: null });
    const result = await client.delete('/videos/1');
    expect(result).toBeNull();
  });

  it('response success interceptor is a pass-through', () => {
    makeClient();
    const resp = { status: 200, data: { ok: true } };
    expect(responseSuccessFn(resp)).toBe(resp);
  });
});
