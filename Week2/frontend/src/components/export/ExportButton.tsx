/**
 * Export Button Component
 *
 * Main export button with format selection dialog
 */

import { useState } from 'react';
import { Button } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { ExportFormatDialog } from './ExportFormatDialog';
import { useExport } from '@/hooks/useExport';
import type { QueryResult } from '@/types/query';
import type { ExportFormat } from '@/types/export';

interface ExportButtonProps {
  /** Query results to export */
  queryResult: QueryResult | null;

  /** Whether button is disabled */
  disabled?: boolean;

   /** Custom button text */
  buttonText?: string;

  /** Button size */
  size?: 'small' | 'middle' | 'large';
}

export function ExportButton({
  queryResult,
  disabled = false,
  buttonText = 'Export',
  size = 'middle',
}: ExportButtonProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const { handleExport, isExporting } = useExport();

  const handleFormatSelected = async (format: ExportFormat): Promise<void> => {
    if (!queryResult) return;

    await handleExport(queryResult, format);
    setIsDialogOpen(false);
  };

  // Button is disabled if:
  // - Explicitly disabled via prop
  // - No query results available
  // - Query results are empty (0 rows)
  // - Export is currently in progress
  const isButtonDisabled =
    disabled ||
    !queryResult ||
    queryResult.rowCount === 0 ||
    isExporting;

  return (
    <>
      <Button
        type="primary"
        icon={<DownloadOutlined />}
        onClick={() => setIsDialogOpen(true)}
        disabled={isButtonDisabled}
        loading={isExporting}
        size={size}
      >
        {buttonText}
      </Button>

      <ExportFormatDialog
        open={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        onFormatSelected={handleFormatSelected}
        isExporting={isExporting}
      />
    </>
  );
}
