/**
 * Filename Generator Utility
 *
 * Generates safe, descriptive filenames for exported query results
 */

import type { FilenameContext, ExportFormat } from '@/types/export';

/**
 * Generate a safe filename from query context
 */
export function generateFilename(context: FilenameContext): string {
  const { database, table, format, timestamp } = context;

  // Build filename parts
  const parts: string[] = [];

  // Add database name if available
  if (database) {
    parts.push(sanitizeFilename(database));
  }

  // Add table name if available (simple queries)
  if (table) {
    parts.push(sanitizeFilename(table));
  }

  // Fallback to generic name
  if (parts.length === 0) {
    parts.push('query_results');
  }

  // Add timestamp
  const timestampStr = formatTimestamp(timestamp);
  parts.push(timestampStr);

  // Join parts and add extension
  const basename = parts.join('_');
  return `${basename}.${format.extension}`;
}

/**
 * Sanitize filename component (remove/replace invalid characters)
 */
export function sanitizeFilename(name: string): string {
  return (
    name
      // Replace invalid filesystem characters with underscores
      .replace(/[<>:"/\\|?*\x00-\x1f]/g, '_')
      // Replace spaces with underscores
      .replace(/\s+/g, '_')
      // Remove leading/trailing dots and underscores
      .replace(/^[._]+|[._]+$/g, '')
      // Limit length to 100 characters
      .slice(0, 100)
      // Ensure not empty
      || 'export'
  );
}

/**
 * Format timestamp for filename (compact ISO 8601 format)
 */
export function formatTimestamp(date: Date): string {
  return date
    .toISOString()
    .replace(/:/g, '-')        // Replace colons with dashes
    .replace(/\.\d{3}Z$/, '')  // Remove milliseconds and Z
    .replace('T', '_');        // Replace T with underscore
}

/**
 * Check if filename is a reserved Windows name
 */
export function isReservedWindowsName(name: string): boolean {
  const reserved = [
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
  ];

  const upper = name.toUpperCase();
  return reserved.includes(upper) || reserved.some(r => upper.startsWith(`${r}.`));
}

/**
 * Generate filename with fallback to default
 */
export function generateSafeFilename(context: Partial<FilenameContext>, format: ExportFormat): string {
  const fullContext: FilenameContext = {
    database: context.database,
    table: context.table,
    format,
    timestamp: context.timestamp || new Date(),
  };

  const filename = generateFilename(fullContext);

  // Check for reserved names
  const basename = filename.split('.')[0];
  if (basename && isReservedWindowsName(basename)) {
    return `export_${formatTimestamp(new Date())}.${format.extension}`;
  }

  return filename;
}
