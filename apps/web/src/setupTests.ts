import React from 'react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Polyfill window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Polyfill ResizeObserver
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
window.ResizeObserver = MockResizeObserver as any;

// Mock @monaco-editor/react using pure React.createElement
vi.mock('@monaco-editor/react', () => {
  return {
    default: ({ value, onChange }: { value: string; onChange: (v: string) => void }) =>
      React.createElement(
        'div',
        { 'data-testid': 'monaco-editor' },
        React.createElement('textarea', {
          'data-testid': 'monaco-textarea',
          value: value || '',
          onChange: (e: any) => onChange(e.target.value),
        })
      ),
  };
});

// Mock @xterm/xterm
vi.mock('@xterm/xterm', () => {
  class MockTerminal {
    open = vi.fn();
    write = vi.fn();
    writeln = vi.fn();
    clear = vi.fn();
    dispose = vi.fn();
    loadAddon = vi.fn();
    _onDataCallback: ((data: string) => void) | null = null;
    constructor() {
      (window as any).__lastTerminalInstance = this;
    }
    onData = vi.fn((cb: (data: string) => void) => {
      this._onDataCallback = cb;
      return { dispose: vi.fn() };
    });
  }
  return { Terminal: MockTerminal };
});

// Mock @xterm/addon-fit
vi.mock('@xterm/addon-fit', () => {
  class MockFitAddon {
    fit = vi.fn();
  }
  return { FitAddon: MockFitAddon };
});

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1;
  static CLOSED = 3;
  readyState = MockWebSocket.OPEN;
  url: string;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: { data: any }) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    (window as any).__lastWebSocketInstance = this;
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 0);
  }

  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) this.onclose();
  });
}
(window as any).WebSocket = MockWebSocket;
