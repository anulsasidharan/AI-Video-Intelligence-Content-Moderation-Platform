'use client';

import { useEffect, useCallback } from 'react';
import { connectSocket, getSocket, type SocketEventHandler } from '@/lib/socket';
import { useAuthStore } from '@/stores/authStore';

export function useWebSocket() {
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) return;
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (token) {
      // connectSocket sets socket.auth before connecting so the backend can
      // authenticate the WebSocket handshake. Calling socket.connect() directly
      // (without auth) causes the server to reject the connection with a timeout.
      connectSocket(token);
    } else {
      const socket = getSocket();
      if (!socket.connected) socket.connect();
    }
    return () => {
      // keep connection alive across route changes; disconnect on logout instead
    };
  }, [isAuthenticated]);

  const subscribe = useCallback(
    <T = unknown>(event: string, handler: SocketEventHandler<T>) => {
      const socket = getSocket();
      socket.on(event, handler as SocketEventHandler);
      return () => {
        socket.off(event, handler as SocketEventHandler);
      };
    },
    []
  );

  const joinRoom = useCallback((room: string) => {
    getSocket().emit('join', { room });
  }, []);

  const leaveRoom = useCallback((room: string) => {
    getSocket().emit('leave', { room });
  }, []);

  return { subscribe, joinRoom, leaveRoom };
}

export function useStreamEvents(
  streamId: string,
  handlers: {
    onStatus?: SocketEventHandler<{ status: string; timestamp: string }>;
    onAlert?: SocketEventHandler<{ category: string; confidence: number; timestamp: string }>;
    onFrame?: SocketEventHandler<{ frame_url: string; timestamp: string; sequence: number }>;
  }
) {
  const { subscribe, joinRoom, leaveRoom } = useWebSocket();

  useEffect(() => {
    if (!streamId) return;
    joinRoom(`stream:${streamId}`);

    const cleanups: Array<() => void> = [];

    if (handlers.onStatus) {
      cleanups.push(subscribe(`stream:${streamId}:status`, handlers.onStatus));
    }
    if (handlers.onAlert) {
      cleanups.push(subscribe(`stream:${streamId}:alert`, handlers.onAlert));
    }
    if (handlers.onFrame) {
      cleanups.push(subscribe(`stream:${streamId}:frame`, handlers.onFrame));
    }

    return () => {
      leaveRoom(`stream:${streamId}`);
      cleanups.forEach((c) => c());
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamId]);
}
