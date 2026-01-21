/**
 * Export Format Dialog Component
 *
 * Modal dialog for selecting export format (CSV or JSON)
 */

import { Modal, Button, Space } from 'antd';
import { FileTextOutlined, CodeOutlined } from '@ant-design/icons';
import { EXPORT_FORMATS } from '@/types/export';
import type { ExportFormat } from '@/types/export';

interface ExportFormatDialogProps {
  /** Whether dialog is open */
  open: boolean;

  /** Close dialog callback */
  onClose: () => void;

  /** Format selected callback */
  onFormatSelected: (format: ExportFormat) => void;

  /** Whether export is in progress */
  isExporting?: boolean;
}

export function ExportFormatDialog({
  open,
  onClose,
  onFormatSelected,
  isExporting = false,
}: ExportFormatDialogProps) {
  const handleCSVClick = () => {
    onFormatSelected(EXPORT_FORMATS.CSV);
  };

  const handleJSONClick = () => {
    onFormatSelected(EXPORT_FORMATS.JSON);
  };

  return (
    <Modal
      title="Export Query Results"
      open={open}
      onCancel={onClose}
      footer={null}
      width={480}
    >
      <p style={{ marginBottom: 16, color: '#666' }}>
        Choose export format for your query results:
      </p>

      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* CSV Export Option */}
        <Button
          size="large"
          block
          onClick={handleCSVClick}
          loading={isExporting}
          style={{
            height: 'auto',
            padding: '16px',
            textAlign: 'left',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
            <FileTextOutlined style={{ fontSize: 24, marginTop: 2 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                {EXPORT_FORMATS.CSV.label}
              </div>
              <div style={{ fontSize: 13, color: '#666', fontWeight: 'normal' }}>
                {EXPORT_FORMATS.CSV.description}
              </div>
            </div>
          </div>
        </Button>

        {/* JSON Export Option */}
        <Button
          size="large"
          block
          onClick={handleJSONClick}
          loading={isExporting}
          style={{
            height: 'auto',
            padding: '16px',
            textAlign: 'left',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
            <CodeOutlined style={{ fontSize: 24, marginTop: 2 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                {EXPORT_FORMATS.JSON.label}
              </div>
              <div style={{ fontSize: 13, color: '#666', fontWeight: 'normal' }}>
                {EXPORT_FORMATS.JSON.description}
              </div>
            </div>
          </div>
        </Button>
      </Space>

      <div style={{ marginTop: 16, fontSize: 12, color: '#999' }}>
        The file will be saved to your default downloads folder.
      </div>
    </Modal>
  );
}
