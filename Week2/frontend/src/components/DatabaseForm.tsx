/** 数据库添加/编辑表单组件 */
import React, { useState } from 'react';
import { Form, Input, Button, Modal, message } from 'antd';

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
  initialName = '',
  initialUrl = '',
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await onSubmit(values.name, values.url);
      form.resetFields();
      onCancel();
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        // 表单验证错误，不需要处理
        return;
      }
      // 其他错误已在 onSubmit 中处理
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={initialName ? '编辑数据库连接' : '添加数据库连接'}
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={loading}
      destroyOnClose
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
            { required: true, message: '请输入连接名称' },
            {
              pattern: /^[a-zA-Z0-9_-]+$/,
              message: '连接名称仅允许字母、数字、下划线和连字符',
            },
            { min: 1, max: 100, message: '长度必须在 1-100 字符之间' },
          ]}
        >
          <Input placeholder="例如: my-postgres" disabled={!!initialName} />
        </Form.Item>
        <Form.Item
          label="连接 URL"
          name="url"
          rules={[
            { required: true, message: '请输入连接 URL' },
            {
              pattern:
                /^(postgresql|mysql|sqlite):\/\/.+/,
              message: 'URL 格式不正确，支持 postgresql://, mysql://, sqlite://',
            },
          ]}
        >
          <Input.TextArea
            placeholder="例如: postgresql://user:pass@localhost:5432/mydb"
            rows={3}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default DatabaseForm;
