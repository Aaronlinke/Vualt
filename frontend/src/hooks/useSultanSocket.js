import { useEffect, useRef, useState, useCallback } from "react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function wsUrl() {
  const url = new URL(BACKEND_URL);
  const proto = url.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${url.host}/api/ws`;
}

// Real-time link to the SultanOSVanta substrate.
export function useSultanSocket() {
  const [connected, setConnected] = useState(false);
  const [agents, setAgents] = useState([]);
  const [status, setStatus] = useState(null);
  const [mintFeed, setMintFeed] = useState([]);
  const socketRef = useRef(null);
  const reconnectRef = useRef(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(wsUrl());
      socketRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        reconnectRef.current = setTimeout(connect, 2000);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data);
          if (data.agents) setAgents(data.agents);
          if (data.status) setStatus(data.status);
          if (data.minted && data.minted.length) {
            setMintFeed((prev) => [...data.minted, ...prev].slice(0, 30));
          }
        } catch (e) {
          /* ignore malformed frame */
        }
      };
    } catch (e) {
      reconnectRef.current = setTimeout(connect, 2000);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (socketRef.current) {
        socketRef.current.onclose = null;
        socketRef.current.close();
      }
    };
  }, [connect]);

  return { connected, agents, status, mintFeed };
}
