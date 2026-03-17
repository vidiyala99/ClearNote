import { useEffect, useRef } from "react";
import { useUser } from "@clerk/clerk-react";

export function useWebSocket(onMessage: (data: any) => void) {
  const { user } = useUser();
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!user) return;

    // derived from VITE_API_URL or config. But simple local bind for local tests
    const wsUrl = `ws://localhost:8000/api/v1/ws/notifications?user_id=${user.id}`;
    
    const connect = () => {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (e) {
          console.error("Failed to parse WebSocket message", e);
        }
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected. Retrying in 3s...");
        setTimeout(connect, 3000); // Simple auto-reconnect trigger
      };

      ws.onerror = (error) => {
        console.error("WebSocket error", error);
        ws.close();
      };
    };

    connect();

    return () => {
      if (socketRef.current) {
        // Remove onclose listner to prevent reconnect on unmount
        socketRef.current.onclose = null;
        socketRef.current.close();
      }
    };
  }, [user, onMessage]);
}
