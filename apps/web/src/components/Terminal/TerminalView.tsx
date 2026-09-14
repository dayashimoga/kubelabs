import React, { useEffect, useRef } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { Maximize2, Minimize2, Terminal as TerminalIcon, RefreshCw } from 'lucide-react';

interface TerminalViewProps {
  sessionId: string;
  isContainer?: boolean;
  onCommandRun?: (cmd: string) => void;
}

export const TerminalView: React.FC<TerminalViewProps> = ({ sessionId, isContainer = false, onCommandRun }) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermInstance = useRef<Terminal | null>(null);
  const fitAddonInstance = useRef<FitAddon | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const [isFullscreen, setIsFullscreen] = React.useState(false);

  useEffect(() => {
    if (!terminalRef.current) return;

    // Initialize xterm
    const term = new Terminal({
      cursorBlink: true,
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 13,
      lineHeight: 1.2,
      theme: {
        background: '#07090e',
        foreground: '#f1f5f9',
        cursor: '#00f2fe',
        selectionBackground: 'rgba(0, 242, 254, 0.3)',
        black: '#141b2d',
        red: '#f43f5e',
        green: '#10b981',
        yellow: '#f59e0b',
        blue: '#3b82f6',
        magenta: '#a855f7',
        cyan: '#00f2fe',
        white: '#ffffff',
      },
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(terminalRef.current);
    fitAddon.fit();

    xtermInstance.current = term;
    fitAddonInstance.current = fitAddon;

    // WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/terminal/${sessionId}`;

    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      term.writeln('\x1b[32m[Connected to KubeLabs Sandbox Terminal]\x1b[0m');
    };

    ws.onmessage = (event) => {
      term.write(event.data);
    };

    ws.onerror = () => {
      // Local fallback emulator mode
      term.writeln('\r\n\x1b[33m[Sandbox connected in client-side interactive mode]\x1b[0m');
      term.write('\r\nsre-engineer@kubelabs-sandbox:~$ ');
    };

    let inputBuffer = '';

    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data);
      } else {
        // Fallback local echo
        if (data === '\r') {
          term.writeln('');
          const trimmed = inputBuffer.trim();
          if (trimmed) {
            if (onCommandRun) onCommandRun(trimmed);
            if (trimmed === 'clear') {
              term.write('\x1b[2J\x1b[H');
            } else if (trimmed === 'df -h') {
              term.writeln('Filesystem      Size  Used Avail Use% Mounted on');
              term.writeln('/dev/root        20G   14G  5.2G  73% /');
              term.writeln('/dev/nvme0n1p1   50G   48G  1.2G  98% /var/spool/clientmqueue');
            } else if (trimmed === 'df -i') {
              term.writeln('Filesystem       Inodes   IUsed   IFree IUse% Mounted on');
              term.writeln('/dev/root       1310720  421000  889720   33% /');
              term.writeln('/dev/nvme0n1p1  3276800 3276800       0  100% /var/spool/clientmqueue');
            } else if (trimmed.startsWith('kubectl get pods')) {
              term.writeln('NAME                                READY   STATUS             RESTARTS   AGE');
              term.writeln('api-worker-7b89f-21                0/1     CrashLoopBackOff   6          12m');
            } else {
              term.writeln(`Executing: ${trimmed}`);
            }
          }
          inputBuffer = '';
          term.write('sre-engineer@kubelabs-sandbox:~$ ');
        } else if (data === '\x7f' || data === '\x08') {
          if (inputBuffer.length > 0) {
            inputBuffer = inputBuffer.slice(0, -1);
            term.write('\b \b');
          }
        } else {
          inputBuffer += data;
          term.write(data);
        }
      }
    });

    const handleResize = () => {
      fitAddon.fit();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      ws.close();
      term.dispose();
    };
  }, [sessionId]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: isFullscreen ? '100vh' : '100%',
        position: isFullscreen ? 'fixed' : 'relative',
        top: isFullscreen ? 0 : undefined,
        left: isFullscreen ? 0 : undefined,
        width: isFullscreen ? '100vw' : '100%',
        zIndex: isFullscreen ? 9999 : 1,
        backgroundColor: '#07090e',
        borderRadius: isFullscreen ? 0 : '8px',
        border: '1px solid rgba(255,255,255,0.08)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 14px',
          backgroundColor: '#0d121d',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.8rem', color: '#94a3b8' }}>
          <TerminalIcon size={14} color="#00f2fe" />
          <span style={{ fontWeight: 600, color: '#f1f5f9' }}>
            {isContainer ? 'Podman Container Shell' : 'Deterministic SRE PTY'}
          </span>
          <span className="badge badge-intermediate" style={{ fontSize: '0.65rem' }}>
            Active
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <button
            onClick={() => xtermInstance.current?.clear()}
            className="btn btn-secondary"
            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
            title="Clear Terminal"
          >
            <RefreshCw size={12} />
          </button>
          <button
            onClick={() => {
              setIsFullscreen(!isFullscreen);
              setTimeout(() => fitAddonInstance.current?.fit(), 100);
            }}
            className="btn btn-secondary"
            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
          </button>
        </div>
      </div>
      <div ref={terminalRef} style={{ flex: 1, padding: 8, overflow: 'hidden' }} />
    </div>
  );
};
