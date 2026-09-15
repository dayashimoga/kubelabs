import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { getApiBase, getWsBase } from '../config';

describe('config helper tests', () => {
  const origProcess = (globalThis as any).process;
  const origLocation = window.location;

  beforeEach(() => {
    delete (window as any).__KUBELABS_API_BASE__;
    delete (window as any).__KUBELABS_WS_BASE__;
    delete (window as any).__KUBELABS_FORCE_PORT_RESOLVE__;
  });

  afterEach(() => {
    (globalThis as any).process = origProcess;
    delete (window as any).location;
    (window as any).location = origLocation;
    delete (window as any).__KUBELABS_FORCE_PORT_RESOLVE__;
  });

  it('returns custom __KUBELABS_API_BASE__ if set', () => {
    (window as any).__KUBELABS_API_BASE__ = 'https://custom-api.kubelabs.internal';
    expect(getApiBase()).toBe('https://custom-api.kubelabs.internal');
  });

  it('returns custom __KUBELABS_WS_BASE__ if set', () => {
    (window as any).__KUBELABS_WS_BASE__ = 'wss://custom-ws.kubelabs.internal';
    expect(getWsBase()).toBe('wss://custom-ws.kubelabs.internal');
  });

  it('returns empty string in test environment for getApiBase', () => {
    expect(getApiBase()).toBe('');
  });

  it('resolves port 3000 to backend port 8000 when not in test mode', () => {
    (window as any).__KUBELABS_FORCE_PORT_RESOLVE__ = true;
    delete (window as any).location;
    (window as any).location = {
      protocol: 'http:',
      hostname: 'localhost',
      port: '3000',
      host: 'localhost:3000',
    };
    expect(getApiBase()).toBe('http://localhost:8000');
    expect(getWsBase()).toBe('ws://localhost:8000');
  });

  it('resolves port 5173 to backend port 8000 with wss on https', () => {
    (window as any).__KUBELABS_FORCE_PORT_RESOLVE__ = true;
    delete (window as any).location;
    (window as any).location = {
      protocol: 'https:',
      hostname: '127.0.0.1',
      port: '5173',
      host: '127.0.0.1:5173',
    };
    expect(getApiBase()).toBe('https://127.0.0.1:8000');
    expect(getWsBase()).toBe('wss://127.0.0.1:8000');
  });

  it('resolves default relative host when port is 80 or empty in production', () => {
    (window as any).__KUBELABS_FORCE_PORT_RESOLVE__ = true;
    delete (window as any).location;
    (window as any).location = {
      protocol: 'http:',
      hostname: 'demo.kubelabs.io',
      port: '',
      host: 'demo.kubelabs.io',
    };
    expect(getApiBase()).toBe('');
    expect(getWsBase()).toBe('ws://demo.kubelabs.io');
  });
});
