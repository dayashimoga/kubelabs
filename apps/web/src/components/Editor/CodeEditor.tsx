import React from 'react';
import Editor from '@monaco-editor/react';
import { Save, Code2 } from 'lucide-react';

interface CodeEditorProps {
  filename: string;
  initialContent: string;
  language?: string;
  onSave?: (newContent: string) => void;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  filename,
  initialContent,
  language = 'yaml',
  onSave,
}) => {
  const [content, setContent] = React.useState(initialContent);
  const [isSaved, setIsSaved] = React.useState(true);

  React.useEffect(() => {
    setContent(initialContent);
    setIsSaved(true);
  }, [initialContent]);

  const handleEditorChange = (value: string | undefined) => {
    setContent(value || '');
    setIsSaved(false);
  };

  const handleSave = () => {
    if (onSave) {
      onSave(content);
      setIsSaved(true);
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#07090e',
        borderRadius: '8px',
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
          <Code2 size={14} color="#3b82f6" />
          <span style={{ fontWeight: 600, color: '#f1f5f9', fontFamily: 'monospace' }}>{filename}</span>
          {!isSaved && (
            <span style={{ color: '#f59e0b', fontSize: '0.75rem', fontWeight: 600 }}>● Unsaved</span>
          )}
        </div>
        <button
          onClick={handleSave}
          className="btn btn-primary"
          style={{ padding: '4px 12px', fontSize: '0.75rem' }}
        >
          <Save size={12} /> Save File
        </button>
      </div>
      <div style={{ flex: 1 }}>
        <Editor
          height="100%"
          language={language}
          theme="vs-dark"
          value={content}
          onChange={handleEditorChange}
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily: "'JetBrains Mono', monospace",
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
          }}
        />
      </div>
    </div>
  );
};
