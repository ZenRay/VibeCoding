/**
 * TypeScript Type Definitions for Query Results Export
 *
 * This file contains all type definitions, interfaces, and enums
 * for the export functionality.
 *
 * @module export-types
 */

// ============================================================================
// Export Formats
// ============================================================================

/** Available export format types */
export type ExportFormatType = 'csv' | 'json';

/** Export format configuration */
export interface ExportFormat {
  /** Format identifier */
  type: ExportFormatType;

  /** Human-readable label for UI display */
  label: string;

  /** File extension (without dot) */
  extension: string;

  /** MIME type for Blob creation */
  mimeType: string;

  /** Optional description for format selection dialog */
  description?: string;
}

/** Predefined export formats */
export const EXPORT_FORMATS = {
  CSV: {
    type: 'csv' as const,
    label: 'CSV (Spreadsheet)',
    extension: 'csv',
    mimeType: 'text/csv;charset=utf-8',
    description: 'Comma-separated values, compatible with Excel and Google Sheets',
  },
  JSON: {
    type: 'json' as const,
    label: 'JSON (Data Format)',
    extension: 'json',
    mimeType: 'application/json;charset=utf-8',
    description: 'JavaScript Object Notation, ideal for programmatic use',
  },
} as const;

// ============================================================================
// Export Options
// ============================================================================

/** Configuration for an export operation */
export interface ExportOptions {
  /** Selected export format */
  format: ExportFormat;

  /** Suggested filename (without extension) */
  filename: string;

  /** Include column metadata in JSON exports (default: true) */
  includeMetadata?: boolean;

  /** Include UTF-8 BOM for Excel compatibility in CSV (default: true) */
  includeExcelBom?: boolean;

  /** Show progress indicator for exports >2 seconds (default: true) */
  showProgress?: boolean;
}

/** Default export options */
export const DEFAULT_EXPORT_OPTIONS: Partial<ExportOptions> = {
  includeMetadata: true,
  includeExcelBom: true,
  showProgress: true,
};

// ============================================================================
// Export Progress
// ============================================================================

/** Export operation status */
export type ExportStatus =
  | 'preparing'     // Initializing export
  | 'processing'    // Generating CSV/JSON
  | 'downloading'   // Triggering browser download
  | 'complete'      // Successfully completed
  | 'error'         // Failed with error
  | 'cancelled';    // User cancelled operation

/** Progress tracking for export operations */
export interface ExportProgress {
  /** Total number of rows to export */
  totalRows: number;

  /** Number of rows processed so far */
  processedRows: number;

  /** Completion percentage (0-100) */
  percentage: number;

  /** Current status of export operation */
  status: ExportStatus;

  /** Error message if status is 'error' */
  errorMessage?: string;

  /** Start time of export (ISO 8601 string) */
  startedAt?: string;

  /** Estimated time remaining in seconds */
  estimatedSecondsRemaining?: number;
}

// ============================================================================
// Query Result Structures (from feature 002)
// ============================================================================

/** Supported data types */
export type DataType = string;

/** Possible cell values */
export type CellValue =
  | string
  | number
  | boolean
  | Date
  | null
  | undefined;

/** Row data: column name → value */
export type Row = Record<string, CellValue>;

/** Metadata for a single column */
export interface ColumnMetadata {
  /** Column name */
  name: string;

  /** Data type as string */
  dataType: DataType;
}

/** Query result from database query execution */
export interface QueryResult {
  /** Column metadata (names and types) */
  columns: ColumnMetadata[];

  /** Row data (array of objects) */
  rows: Row[];

  /** Total number of rows returned */
  rowCount: number;

  /** Query execution time in milliseconds */
  executionTimeMs?: number;

  /** SQL query that produced this result */
  sql?: string;

  /** Whether results were truncated */
  truncated?: boolean;
}

// ============================================================================
// CSV Output
// ============================================================================

/** CSV output: plain text string with RFC 4180 formatting */
export type CSVOutput = string;

/** CSV generation options */
export interface CSVOptions {
  /** Include header row with column names (default: true) */
  includeHeaders?: boolean;

  /** Quote all fields (default: false, quotes added only when needed) */
  quoteAll?: boolean;

  /** Field delimiter (default: comma) */
  delimiter?: string;

  /** Line ending (default: \r\n per RFC 4180) */
  lineEnding?: string;

  /** Include UTF-8 BOM for Excel (default: true) */
  includeBOM?: boolean;
}

/** Default CSV options */
export const DEFAULT_CSV_OPTIONS = {
  includeHeaders: true,
  quoteAll: false,
  delimiter: ',',
  lineEnding: '\r\n',
  includeBOM: true,
} as const;

// ============================================================================
// JSON Output
// ============================================================================

/** Metadata included in JSON exports */
export interface ExportMetadata {
  /** Column definitions */
  columns: Array<{ name: string; dataType: string }>;

  /** ISO 8601 timestamp of export */
  exportedAt: string;

  /** Total number of rows */
  rowCount: number;

  /** Original SQL query (if available) */
  sql?: string;

  /** Database name (if available) */
  database?: string;
}

/** JSON export structure */
export interface JSONExport {
  /** Optional metadata about the export */
  metadata?: ExportMetadata;

  /** Row data as array of objects */
  data: Row[];
}

/** JSON generation options */
export interface JSONOptions {
  /** Include metadata object (default: true) */
  includeMetadata?: boolean;

  /** Pretty-print with indentation (default: true) */
  prettyPrint?: boolean;

  /** Indentation spaces (default: 2) */
  indent?: number;

  /** Convert dates to ISO 8601 strings (default: true) */
  stringifyDates?: boolean;
}

/** Default JSON options */
export const DEFAULT_JSON_OPTIONS = {
  includeMetadata: true,
  prettyPrint: true,
  indent: 2,
  stringifyDates: true,
} as const;

// ============================================================================
// Error Handling
// ============================================================================

/** Export error codes */
export enum ExportErrorCode {
  /** Generic export failure */
  EXPORT_FAILED = 'EXPORT_FAILED',

  /** Browser memory limit exceeded */
  MEMORY_LIMIT_EXCEEDED = 'MEMORY_LIMIT_EXCEEDED',

  /** File system permission denied */
  PERMISSION_DENIED = 'PERMISSION_DENIED',

  /** Disk space insufficient */
  DISK_SPACE_FULL = 'DISK_SPACE_FULL',

  /** Invalid data format */
  INVALID_DATA_FORMAT = 'INVALID_DATA_FORMAT',

  /** User cancelled operation */
  USER_CANCELLED = 'USER_CANCELLED',

  /** Network error (if fetching remote data) */
  NETWORK_ERROR = 'NETWORK_ERROR',
}

/** Export error structure */
export interface ExportError {
  /** Error code for programmatic handling */
  code: ExportErrorCode;

  /** Human-readable error message */
  message: string;

  /** Optional underlying error details */
  details?: unknown;

  /** Timestamp of error occurrence */
  occurredAt: string;
}

/** Error message templates */
export const ERROR_MESSAGES: Record<ExportErrorCode, string> = {
  [ExportErrorCode.EXPORT_FAILED]: 'Failed to export query results. Please try again.',
  [ExportErrorCode.MEMORY_LIMIT_EXCEEDED]: 'Dataset too large for browser memory. Try exporting fewer rows.',
  [ExportErrorCode.PERMISSION_DENIED]: 'Permission denied to save file. Check browser settings.',
  [ExportErrorCode.DISK_SPACE_FULL]: 'Insufficient disk space. Free up space and try again.',
  [ExportErrorCode.INVALID_DATA_FORMAT]: 'Invalid data format detected. Cannot export.',
  [ExportErrorCode.USER_CANCELLED]: 'Export cancelled by user.',
  [ExportErrorCode.NETWORK_ERROR]: 'Network error occurred during export.',
};

// ============================================================================
// Filename Generation
// ============================================================================

/** Context for generating filenames */
export interface FilenameContext {
  /** Database name (if available) */
  database: string | undefined;

  /** Table name (if simple query) */
  table: string | undefined;

  /** Export format */
  format: ExportFormat;

  /** Timestamp of export */
  timestamp: Date;
}

// ============================================================================
// Validation
// ============================================================================

/** Validation error */
export interface ValidationError {
  code: string;
  message: string;
  field?: string;
}

/** Validation warning */
export interface ValidationWarning {
  code: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
}

/** Validation result */
export interface ValidationResult {
  /** Whether data is valid for export */
  valid: boolean;

  /** List of validation errors (if any) */
  errors: ValidationError[];

  /** List of warnings (non-blocking) */
  warnings: ValidationWarning[];
}

// ============================================================================
// Type Guards
// ============================================================================

/** Type guard for ExportFormat */
export function isExportFormat(value: unknown): value is ExportFormat {
  return (
    typeof value === 'object' &&
    value !== null &&
    'type' in value &&
    'label' in value &&
    'extension' in value &&
    'mimeType' in value
  );
}

/** Type guard for QueryResult */
export function isQueryResult(value: unknown): value is QueryResult {
  return (
    typeof value === 'object' &&
    value !== null &&
    'columns' in value &&
    'rows' in value &&
    'rowCount' in value &&
    Array.isArray((value as QueryResult).columns) &&
    Array.isArray((value as QueryResult).rows)
  );
}

/** Check if export is in progress */
export function isExportInProgress(status: ExportStatus): boolean {
  return status === 'preparing' || status === 'processing' || status === 'downloading';
}

/** Check if export status is final */
export function isExportComplete(status: ExportStatus): boolean {
  return status === 'complete' || status === 'error' || status === 'cancelled';
}
