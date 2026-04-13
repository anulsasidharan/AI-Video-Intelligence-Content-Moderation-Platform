/**
 * F-11 — Zustand authStore tests
 */
import { act } from 'react';

// Mock dependencies before any imports
jest.mock('@/lib/api', () => ({
  apiClient: {
    post: jest.fn(),
    setTokens: jest.fn(),
    clearTokens: jest.fn(),
  },
}));

jest.mock('@/lib/socket', () => ({
  connectSocket: jest.fn(),
  disconnectSocket: jest.fn(),
}));

// Mock localStorage
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

import { apiClient } from '@/lib/api';
import { connectSocket, disconnectSocket } from '@/lib/socket';
import { useAuthStore } from '@/stores/authStore';

const mockPost = apiClient.post as jest.MockedFunction<typeof apiClient.post>;
const mockSetTokens = apiClient.setTokens as jest.MockedFunction<typeof apiClient.setTokens>;
const mockClearTokens = apiClient.clearTokens as jest.MockedFunction<typeof apiClient.clearTokens>;
const mockConnect = connectSocket as jest.MockedFunction<typeof connectSocket>;
const mockDisconnect = disconnectSocket as jest.MockedFunction<typeof disconnectSocket>;

beforeEach(() => {
  localStorageMock.clear();
  jest.clearAllMocks();
  // Reset store to initial state
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, error: null });
});

describe('useAuthStore (F-11)', () => {
  it('starts with unauthenticated state', () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.error).toBeNull();
  });

  it('login() sets authenticated state and calls setTokens', async () => {
    const mockUser = { id: 'u1', email: 'user@test.com', name: 'Test User', role: 'operator' };
    // apiClient.post returns response.data (axios response body already unwrapped)
    mockPost.mockResolvedValueOnce({
      data: {
        access_token: 'acc-token',
        refresh_token: 'ref-token',
        user: mockUser,
      },
    } as any);

    await act(async () => {
      await useAuthStore.getState().login('user@test.com', 'pass123');
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockUser);
    expect(mockSetTokens).toHaveBeenCalledWith('acc-token', 'ref-token');
    expect(mockConnect).toHaveBeenCalledWith('acc-token');
  });

  it('login() sets error on failure and keeps unauthenticated', async () => {
    mockPost.mockRejectedValueOnce(new Error('Invalid credentials'));

    await act(async () => {
      try {
        await useAuthStore.getState().login('bad@test.com', 'wrong');
      } catch {}
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.error).toBeTruthy();
  });

  it('logout() clears state and disconnects socket', () => {
    useAuthStore.setState({
      user: { id: 'u1', email: 'user@test.com', name: 'Test', role: 'operator' } as any,
      isAuthenticated: true,
    });

    act(() => {
      useAuthStore.getState().logout();
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(mockClearTokens).toHaveBeenCalled();
    expect(mockDisconnect).toHaveBeenCalled();
  });

  it('clearError() resets error to null', () => {
    useAuthStore.setState({ error: 'some error' });

    act(() => {
      useAuthStore.getState().clearError();
    });

    expect(useAuthStore.getState().error).toBeNull();
  });

  it('setUser() updates user in state', () => {
    const newUser = { id: 'u2', email: 'new@test.com', name: 'New', role: 'admin' } as any;

    act(() => {
      useAuthStore.getState().setUser(newUser);
    });

    expect(useAuthStore.getState().user).toEqual(newUser);
  });
});
