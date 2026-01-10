/** SQL 编辑器组件（Monaco Editor 封装） */
import React, { useEffect } from "react";
import Editor, { OnMount } from "@monaco-editor/react";

interface SqlEditorProps {
  value: string;
  onChange: (value: string | undefined) => void;
  height?: string;
  readOnly?: boolean;
}

const SqlEditor: React.FC<SqlEditorProps> = ({
  value,
  onChange,
  height = "200px",
  readOnly = false,
}) => {
  const handleEditorDidMount: OnMount = (editor, monaco) => {
    // 定义自定义主题
    monaco.editor.defineTheme("sqlDark", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#1e1e1e",
      },
    });

    // 应用主题
    monaco.editor.setTheme("sqlDark");
  };

  return (
    <Editor
      height={height}
      language="sql"
      value={value}
      onChange={onChange}
      onMount={handleEditorDidMount}
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: "on",
        readOnly,
        scrollBeyondLastLine: false,
        wordWrap: "on",
      }}
      theme="sqlDark"
    />
  );
};

export default SqlEditor;
