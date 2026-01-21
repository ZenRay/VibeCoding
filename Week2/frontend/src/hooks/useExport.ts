/**
 * useExport Hook
 *
 * React hook for handling query result exports
 */

import { useState } from 'react';
import { notification } from 'antd';
import { exportToCSV } from '@/services/export/csvExporter';
import { exportToJSON } from '@/services/export/jsonExporter';
import { downloadFileWithSize, formatFileSize } from '@/services/export/fileDownload';
import { generateSafeFilename } from '@/utils/export/filenameGenerator';
import type { QueryResult } from '@/types/query';
import type { ExportFormat } from '@/types/export';

export function useExport() {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (
    queryResult: QueryResult,
    format: ExportFormat
  ): Promise<void> => {
    setIsExporting(true);

    try {
      // Generate export content
      let content: string;

      if (format.type === 'csv') {
        content = exportToCSV(queryResult, {
          includeHeaders: true,
          includeBOM: true,
        });
      } else {
        content = exportToJSON(queryResult, {
          includeMetadata: true,
          prettyPrint: true,
          indent: 2,
        });
      }

      // Generate filename
      const filename = generateSafeFilename(
        {
          timestamp: new Date(),
        },
        format
      );

      // Download file
      const { filename: downloadedFilename, fileSize } = downloadFileWithSize(
        content,
        filename,
        format.mimeType
      );

      // Success notification
      notification.success({
        message: 'Export Successful',
        description: `${queryResult.rowCount} rows exported to ${downloadedFilename} (${formatFileSize(fileSize)})`,
        duration: 4,
      });

    } catch (error) {
      // Error notification
      const message = error instanceof Error ? error.message : 'Unknown error occurred';

      notification.error({
        message: 'Export Failed',
        description: message,
        duration: 6,
      });

      console.error('Export error:', error);

    } finally {
      setIsExporting(false);
    }
  };

  return {
    handleExport,
    isExporting,
  };
}
