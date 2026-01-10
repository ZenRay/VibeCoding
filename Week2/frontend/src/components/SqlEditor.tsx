/** SQL 编辑器组件（Monaco Editor 封装） */
import React from 'react';
import Editor from '@monaco-editor/react';

interface SqlEditorProps {
  value: string;
  onChange: (value: string | undefined) => void;
  height?: string;
  readOnly?: boolean;
}

const SqlEditor: React.FC<SqlEditorProps> = ({
  value,
  onChange,
  height = '200px',
  readOnly = false,
}) => {
  return (
    <Editor
      height={height}
      language="sql"
      value={value}
      onChange={onChange}
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: 'on',
        readOnly,
        scrollBeyondLastLine: false,
        wordWrap: 'on',
      }}
      theme="vs"
    />
  );
};

export default SqlEditor;
