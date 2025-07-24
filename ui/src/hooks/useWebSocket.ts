import { useEffect, useRef, useState, useCallback } from 'react';
import type { TickData, WebSocketMessage } from '../types';

interface UseWebSocketOptions {
  onMessage?: (data: TickData) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
  data: TickData | null;
  isConnected: boolean;
  error: string | null;
  reconnectCount: number;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (message: WebSocketMessage) => void;
}

export const useWebSocket = (
  worldId: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    onMessage,
    onError,
    onConnect,
    onDisconnect,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [data, setData] = useState<TickData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnect = useRef(true);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/worlds/${worldId}`;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log(`WebSocket connected to world ${worldId}`);
        setIsConnected(true);
        setError(null);
        setReconnectCount(0);
        onConnect?.();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const tickData: TickData = JSON.parse(event.data);
          setData(tickData);
          onMessage?.(tickData);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
        onError?.(event);
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        onDisconnect?.();

        // Attempt to reconnect if not manually closed
        if (shouldReconnect.current && reconnectCount < maxReconnectAttempts) {
          setReconnectCount(prev => prev + 1);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [worldId, onMessage, onError, onConnect, onDisconnect, reconnectInterval, maxReconnectAttempts, reconnectCount]);

  const disconnect = useCallback(() => {
    shouldReconnect.current = false;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();

    return () => {
      disconnect();
    };
  }, [worldId, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldReconnect.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    data,
    isConnected,
    error,
    reconnectCount,
    connect,
    disconnect,
    sendMessage,
  };
};