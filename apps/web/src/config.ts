/**
 * Global Configuration for API and WebSocket Base URLs.
 * Resolves the active backend target for local development, rootless container testing, and production.
 */

export const getApiBase = (): string => {
  if (typeof window !== 'undefined' && (window as any).__KUBELABS_API_BASE__ !== undefined) {
    return (window as any).__KUBELABS_API_BASE__;
  }
  const isExplicitOverride = typeof window !== 'undefined' && (window as any).__KUBELABS_FORCE_PORT_RESOLVE__;
  if (!isExplicitOverride) {
    const proc = (globalThis as any).process;
    if (proc?.env?.NODE_ENV === 'test') {
      return '';
    }
    try {
      if ((import.meta as any).env?.MODE === 'test') {
        return '';
      }
    } catch {}
  }
  try {
    const envUrl = (import.meta as any).env?.VITE_API_URL;
    if (envUrl) return envUrl;
  } catch {}
  if (typeof window !== 'undefined') {
    // When accessed in a browser on localhost:3000 (Podman web) or localhost:5173 (Vite dev)
    if (window.location.port === '3000' || window.location.port === '5173') {
      return `${window.location.protocol}//${window.location.hostname}:8000`;
    }
  }
  return '';
};

export const getWsBase = (): string => {
  if (typeof window !== 'undefined' && (window as any).__KUBELABS_WS_BASE__ !== undefined) {
    return (window as any).__KUBELABS_WS_BASE__;
  }
  const isExplicitOverride = typeof window !== 'undefined' && (window as any).__KUBELABS_FORCE_PORT_RESOLVE__;
  if (!isExplicitOverride) {
    const proc = (globalThis as any).process;
    if (proc?.env?.NODE_ENV === 'test') {
      const proto = (typeof window !== 'undefined' && window.location.protocol === 'https:') ? 'wss:' : 'ws:';
      return typeof window !== 'undefined' ? `${proto}//${window.location.host}` : 'ws://localhost';
    }
    try {
      if ((import.meta as any).env?.MODE === 'test') {
        const proto = (typeof window !== 'undefined' && window.location.protocol === 'https:') ? 'wss:' : 'ws:';
        return typeof window !== 'undefined' ? `${proto}//${window.location.host}` : 'ws://localhost';
      }
    } catch {}
  }
  try {
    const envUrl = (import.meta as any).env?.VITE_WS_URL;
    if (envUrl) return envUrl;
  } catch {}
  if (typeof window !== 'undefined') {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    if (window.location.port === '3000' || window.location.port === '5173') {
      return `${proto}//${window.location.hostname}:8000`;
    }
    return `${proto}//${window.location.host}`;
  }
  return 'ws://localhost:8000';
};
