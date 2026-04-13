/**
 * F-12 — useWebSocket hook tests
 */
import { renderHook, act } from '@testing-library/react';

// Mock @/lib/socket
const mockSocket = {
  on: jest.fn(),
  off: jest.fn(),
  emit: jest.fn(),
  disconnect: jest.fn(),
  connect: jest.fn(),
  connected: true,
};

jest.mock('@/lib/socket', () => ({
  connectSocket: jest.fn(),
  disconnectSocket: jest.fn(),
  getSocket: jest.fn(() => mockSocket),
}));

jest.mock('@/stores/authStore', () => ({
  useAuthStore: jest.fn(() => ({ isAuthenticated: true })),
}));

beforeEach(() => {
  jest.clearAllMocks();
  mockSocket.on.mockClear();
  mockSocket.off.mockClear();
  mockSocket.emit.mockClear();
});

describe('useWebSocket (F-12)', () => {
  it('returns subscribe, joinRoom, leaveRoom', () => {
    const { useWebSocket } = require('@/hooks/useWebSocket');
    const { result } = renderHook(() => useWebSocket());
    expect(typeof result.current.subscribe).toBe('function');
    expect(typeof result.current.joinRoom).toBe('function');
    expect(typeof result.current.leaveRoom).toBe('function');
  });

  it('subscribe() registers event listener on socket', () => {
    const { useWebSocket } = require('@/hooks/useWebSocket');
    const { result } = renderHook(() => useWebSocket());
    const handler = jest.fn();

    act(() => {
      result.current.subscribe('test-event', handler);
    });

    expect(mockSocket.on).toHaveBeenCalledWith('test-event', handler);
  });

  it('subscribe() returns cleanup that calls socket.off', () => {
    const { useWebSocket } = require('@/hooks/useWebSocket');
    const { result } = renderHook(() => useWebSocket());
    const handler = jest.fn();

    let cleanup: () => void;
    act(() => {
      cleanup = result.current.subscribe('test-event', handler);
    });

    act(() => {
      cleanup();
    });

    expect(mockSocket.off).toHaveBeenCalledWith('test-event', handler);
  });

  it('joinRoom() emits join event with room name', () => {
    const { useWebSocket } = require('@/hooks/useWebSocket');
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      result.current.joinRoom('stream:abc');
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('join', { room: 'stream:abc' });
  });

  it('leaveRoom() emits leave event with room name', () => {
    const { useWebSocket } = require('@/hooks/useWebSocket');
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      result.current.leaveRoom('stream:abc');
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('leave', { room: 'stream:abc' });
  });
});
