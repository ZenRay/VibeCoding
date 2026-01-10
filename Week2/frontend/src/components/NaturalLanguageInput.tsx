/** 自然语言输入组件 */
import React, { useState } from "react";
import { Input, Button, Space, message } from "antd";
import { ThunderboltOutlined } from "@ant-design/icons";

const { TextArea } = Input;

interface NaturalLanguageInputProps {
  onGenerate: (prompt: string) => Promise<string>;
  onSqlGenerated: (sql: string) => void;
  loading?: boolean;
}

const NaturalLanguageInput: React.FC<NaturalLanguageInputProps> = ({
  onGenerate,
  onSqlGenerated,
  loading = false,
}) => {
  const [prompt, setPrompt] = useState("");

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      message.warning("请输入查询描述");
      return;
    }

    try {
      const sql = await onGenerate(prompt);
      onSqlGenerated(sql);
      message.success("SQL 生成成功");
    } catch (err) {
      // 错误已在 onGenerate 中处理
    }
  };

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="middle">
      <TextArea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="例如: 查找所有年龄大于 30 的用户"
        rows={3}
        maxLength={1000}
        showCount
      />
      <Button
        type="primary"
        icon={<ThunderboltOutlined />}
        onClick={handleGenerate}
        loading={loading}
      >
        生成 SQL
      </Button>
    </Space>
  );
};

export default NaturalLanguageInput;
