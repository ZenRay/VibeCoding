/** 数据库添加/编辑表单组件 */
import React, { useState } from "react";
import { Form, Input, Button, Modal, message, Space } from "antd";
import {
  CheckCircleOutlined,
  SaveOutlined,
  ApiOutlined,
} from "@ant-design/icons";
import { databaseService } from "../services/databaseService";

interface DatabaseFormProps {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (name: string, url: string) => Promise<void>;
  initialName?: string;
  initialUrl?: string;
}

const DatabaseForm: React.FC<DatabaseFormProps> = ({
  visible,
  onCancel,
  onSubmit,
  initialName = "",
  initialUrl = "",
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const handleTestConnection = async () => {
    try {
      const values = await form.validateFields();
      setTestLoading(true);
      setTestResult(null);

      // 创建临时连接名测试
      const testName = `__test_${Date.now()}`;

      try {
        // 尝试添加连接（这会验证连接）
        await databaseService.upsert(testName, { url: values.url });

        // 测试成功，删除临时连接
        await databaseService.delete(testName);

        setTestResult({
          success: true,
          message: "连接测试成功！数据库可以正常访问。",
        });
        message.success("连接测试成功");
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "连接失败";
        setTestResult({
          success: false,
          message: `连接测试失败: ${errorMessage}`,
        });
        message.error("连接测试失败");

        // 确保清理临时连接
        try {
          await databaseService.delete(testName);
        } catch {
          // 忽略删除错误
        }
      }
    } catch (err) {
      if (err && typeof err === "object" && "errorFields" in err) {
        message.warning("请先填写完整的连接信息");
        return;
      }
    } finally {
      setTestLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await onSubmit(values.name, values.url);
      form.resetFields();
      setTestResult(null);
      onCancel();
    } catch (err) {
      if (err && typeof err === "object" && "errorFields" in err) {
        // 表单验证错误，不需要处理
        return;
      }
      // 其他错误已在 onSubmit 中处理
    } finally {
      setLoading(false);
    }
  };

  const handleModalCancel = () => {
    form.resetFields();
    setTestResult(null);
    onCancel();
  };

  return (
    <Modal
      title={initialName ? "编辑数据库连接" : "添加数据库连接"}
      open={visible}
      onCancel={handleModalCancel}
      footer={[
        <Button key="cancel" onClick={handleModalCancel}>
          取消
        </Button>,
        <Button
          key="test"
          icon={<ApiOutlined />}
          onClick={handleTestConnection}
          loading={testLoading}
        >
          测试连通性
        </Button>,
        <Button
          key="submit"
          type="primary"
          icon={<SaveOutlined />}
          onClick={handleSubmit}
          loading={loading}
        >
          保存
        </Button>,
      ]}
      destroyOnClose
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ name: initialName, url: initialUrl }}
      >
        <Form.Item
          label="连接名称"
          name="name"
          rules={[
            { required: true, message: "请输入连接名称" },
            {
              pattern: /^[a-zA-Z0-9_-]+$/,
              message: "连接名称仅允许字母、数字、下划线和连字符",
            },
            { min: 1, max: 100, message: "长度必须在 1-100 字符之间" },
          ]}
        >
          <Input placeholder="例如: my-postgres" disabled={!!initialName} />
        </Form.Item>
        <Form.Item
          label="连接 URL"
          name="url"
          rules={[
            { required: true, message: "请输入连接 URL" },
            {
              pattern: /^(postgresql|mysql|sqlite):\/\/.+/,
              message:
                "URL 格式不正确，支持 postgresql://, mysql://, sqlite://",
            },
          ]}
          extra={
            <div style={{ marginTop: "8px" }}>
              <div>示例:</div>
              <div>
                • PostgreSQL: postgresql://user:password@localhost:5432/dbname
              </div>
              <div>• MySQL: mysql://user:password@localhost:3306/dbname</div>
              <div>• SQLite: sqlite:///path/to/database.db</div>
            </div>
          }
        >
          <Input.TextArea
            placeholder="例如: postgresql://user:pass@localhost:5432/mydb"
            rows={3}
          />
        </Form.Item>

        {testResult && (
          <div
            style={{
              padding: "12px",
              borderRadius: "4px",
              backgroundColor: testResult.success ? "#f6ffed" : "#fff2e8",
              border: `1px solid ${testResult.success ? "#b7eb8f" : "#ffbb96"}`,
              marginBottom: "16px",
            }}
          >
            <Space>
              <CheckCircleOutlined
                style={{
                  color: testResult.success ? "#52c41a" : "#ff4d4f",
                  fontSize: "16px",
                }}
              />
              <span
                style={{ color: testResult.success ? "#52c41a" : "#ff4d4f" }}
              >
                {testResult.message}
              </span>
            </Space>
          </div>
        )}
      </Form>
    </Modal>
  );
};

export default DatabaseForm;
