# Data Model: Query Results Export

**Feature**: Query Results Export
**Date**: 2026-01-22
**Purpose**: Define data structures, types, and relationships for export functionality

## Overview

This document defines the TypeScript interfaces and data structures for exporting database query results to CSV and JSON formats. The export system operates entirely client-side on already-loaded query results.

## Core Entities

### Export Format

Represents an available export format (CSV or JSON).

```typescript
interface ExportFormat {
  /** Format identifier */
  type: 'csv' | 'json';

  /** Human-readable label for UI display */
  label: string;

  /** File extension (without dot) */
  extension: string;

  /** MIME type for Blob creation */
  mimeType: string;

  /** Optional description for format selection dialog */
  description?: string;
}
```

**Predefined Formats**:

```typescript
export const EXPORT_FORMATS: Record<'CSV' | 'JSON', ExportFormat> = {
  CSV: {
    type: 'csv',
    label: 'CSV (Spreadsheet)',
    extension: 'csv',
    mimeType: 'text/csv;charset=utf-8',
    description: 'Comma-separated values, compatible with Excel and Google Sheets'
  },
  JSON: {
    type: 'json',
    label: 'JSON (Data Format)',
    extension: 'json',
    mimeType: 'application/json;charset=utf-8',
    description: 'JavaScript Object Notation, ideal for programmatic use'
  }
};
```

---

### Export Options

Configuration for an export operation.

```typescript
interface ExportOptions {
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
```

**Default Options**:

```typescript
export const DEFAULT_EXPORT_OPTIONS: Partial<ExportOptions> = {
  includeMetadata: true,
  includeExcelBom: true,
  showProgress: true
};
```

---

### Export Progress

Tracks the status and progress of an ongoing export operation.

```typescript
interface ExportProgress {
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

type ExportStatus =
  | 'preparing'     // Initializing export
  | 'processing'    // Generating CSV/JSON
  | 'downloading'   // Triggering browser download
  | 'complete'      // Successfully completed
  | 'error'         // Failed with error
  | 'cancelled';    // User cancelled operation
```

**Status Flow**:
```
preparing → processing → downloading → complete
                            ↓
                          error
                            ↑
                        cancelled
```

---

### Query Result Structure

Re-uses existing data structures from feature 002 (query execution).

```typescript
/** Query result from database query execution */
interface QueryResult {
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

/** Metadata for a single column */
interface ColumnMetadata {
  /** Column name */
  name: string;

  /** Data type as string */
  dataType: DataType;
}

/** Supported data types */
type DataType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'date'
  | 'datetime'
  | 'null'
  | 'unknown';

/** Row data: column name → value */
type Row = Record<string, CellValue>;

/** Possible cell values */
type CellValue =
  | string
  | number
  | boolean
  | Date
  | null
  | undefined;
```

---

### CSV Output Structure

CSV export produces a plain string formatted according to RFC 4180.

```typescript
/** CSV output: plain text string with RFC 4180 formatting */
type CSVOutput = string;

/** CSV generation options */
interface CSVOptions {
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
```

**CSV Format Example**:
```csv
\ufeffid,name,email,age,created_at
1,"John Doe","john@example.com",30,2026-01-22T10:30:00Z
2,"Jane ""Doe""","jane@example.com",25,2026-01-22T11:00:00Z
3,"Bob Smith, Jr.","bob@example.com",35,
```

**RFC 4180 Rules Implemented**:
1. Fields containing commas, quotes, or newlines → enclosed in double-quotes
2. Double-quotes within fields → escaped by doubling (`"` becomes `""`)
3. Header row with column names
4. CRLF line endings (`\r\n`)
5. UTF-8 with BOM for Excel compatibility

---

### JSON Output Structure

JSON export can include optional metadata alongside row data.

```typescript
/** JSON export structure */
interface JSONExport {
  /** Optional metadata about the export */
  metadata?: ExportMetadata;

  /** Row data as array of objects */
  data: Row[];
}

/** Metadata included in JSON exports */
interface ExportMetadata {
  /** Column definitions */
  columns: ColumnMetadata[];

  /** ISO 8601 timestamp of export */
  exportedAt: string;

  /** Total number of rows */
  rowCount: number;

  /** Original SQL query (if available) */
  sql?: string;

  /** Database name (if available) */
  database?: string;
}

/** JSON generation options */
interface JSONOptions {
  /** Include metadata object (default: true) */
  includeMetadata?: boolean;

  /** Pretty-print with indentation (default: true) */
  prettyPrint?: boolean;

  /** Indentation spaces (default: 2) */
  indent?: number;

  /** Convert dates to ISO 8601 strings (default: true) */
  stringifyDates?: boolean;
}
```

**JSON Format Examples**:

**With Metadata** (default):
```json
{
  "metadata": {
    "columns": [
      { "name": "id", "dataType": "number" },
      { "name": "name", "dataType": "string" },
      { "name": "email", "dataType": "string" }
    ],
    "exportedAt": "2026-01-22T10:30:00Z",
    "rowCount": 3,
    "sql": "SELECT * FROM users LIMIT 3"
  },
  "data": [
    { "id": 1, "name": "John Doe", "email": "john@example.com" },
    { "id": 2, "name": "Jane Doe", "email": "jane@example.com" },
    { "id": 3, "name": "Bob Smith", "email": "bob@example.com" }
  ]
}
```

**Without Metadata** (minimal):
```json
[
  { "id": 1, "name": "John Doe", "email": "john@example.com" },
  { "id": 2, "name": "Jane Doe", "email": "jane@example.com" },
  { "id": 3, "name": "Bob Smith", "email": "bob@example.com" }
]
```

**Type Preservation in JSON**:
```json
{
  "id": 123,                    // number (not quoted)
  "name": "John Doe",           // string (quoted)
  "active": true,               // boolean (not quoted)
  "created_at": "2026-01-22T10:30:00Z",  // date (ISO 8601 string)
  "notes": null,                // null (JSON null)
  "metadata": {                 // object (nested structure)
    "verified": false
  }
}
```

---

## Export Operation Lifecycle

### State Machine

```typescript
/** Export operation state machine */
type ExportState =
  | { status: 'idle' }
  | { status: 'preparing'; options: ExportOptions }
  | { status: 'processing'; progress: ExportProgress }
  | { status: 'downloading'; fileSize: number }
  | { status: 'complete'; filename: string; fileSize: number }
  | { status: 'error'; error: ExportError }
  | { status: 'cancelled' };
```

### Transitions

```
idle
  → [User clicks Export] → preparing
                              → [Format selected] → processing
                                                      → [File generated] → downloading
                                                                             → [Download started] → complete
                                                      → [Error] → error
  → [User cancels] → cancelled
```

---

## Error Handling

### Export Errors

```typescript
interface ExportError {
  /** Error code for programmatic handling */
  code: ExportErrorCode;

  /** Human-readable error message */
  message: string;

  /** Optional underlying error details */
  details?: unknown;

  /** Timestamp of error occurrence */
  occurredAt: string;
}

enum ExportErrorCode {
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
  NETWORK_ERROR = 'NETWORK_ERROR'
}
```

**Error Message Examples**:

```typescript
const ERROR_MESSAGES: Record<ExportErrorCode, string> = {
  EXPORT_FAILED: 'Failed to export query results. Please try again.',
  MEMORY_LIMIT_EXCEEDED: 'Dataset too large for browser memory. Try exporting fewer rows.',
  PERMISSION_DENIED: 'Permission denied to save file. Check browser settings.',
  DISK_SPACE_FULL: 'Insufficient disk space. Free up space and try again.',
  INVALID_DATA_FORMAT: 'Invalid data format detected. Cannot export.',
  USER_CANCELLED: 'Export cancelled by user.',
  NETWORK_ERROR: 'Network error occurred during export.'
};
```

---

## Filename Generation

### Filename Pattern

```typescript
interface FilenameGenerator {
  /** Generate filename from query context */
  generate(context: FilenameContext): string;
}

interface FilenameContext {
  /** Database name (if available) */
  database?: string;

  /** Table name (if simple query) */
  table?: string;

  /** Query type (select, join, etc.) */
  queryType?: string;

  /** Export format */
  format: ExportFormat;

  /** Timestamp of export */
  timestamp: Date;
}
```

**Filename Examples**:

```typescript
// Simple table query
"users_2026-01-22_103045.csv"

// Complex query
"query_results_2026-01-22_103045.json"

// With database context
"interview_db_candidates_2026-01-22_103045.csv"
```

**Filename Rules**:
1. Sanitize special characters (replace with underscores)
2. Include timestamp for uniqueness (ISO 8601 compact format)
3. Add appropriate file extension
4. Limit length to 255 characters (filesystem limit)
5. Avoid reserved names (CON, PRN, AUX on Windows)

---

## Validation Rules

### Data Validation

```typescript
/** Validate query results before export */
interface ExportValidator {
  /** Check if results are exportable */
  validate(results: QueryResult): ValidationResult;
}

interface ValidationResult {
  /** Whether data is valid for export */
  valid: boolean;

  /** List of validation errors (if any) */
  errors: ValidationError[];

  /** List of warnings (non-blocking) */
  warnings: ValidationWarning[];
}

interface ValidationError {
  code: string;
  message: string;
  field?: string;
}

interface ValidationWarning {
  code: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
}
```

**Validation Checks**:
1. ✅ Results not empty (at least headers)
2. ✅ Column names are valid (not empty, unique)
3. ✅ Data types are supported
4. ✅ Row count within reasonable limits (<1M rows)
5. ⚠️ Warning for large datasets (>100,000 rows)
6. ⚠️ Warning for binary/blob data types (may not export correctly)

---

## Type Guards

```typescript
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
```

---

## Summary

**Key Data Structures**:
1. `ExportFormat` - Available export formats (CSV, JSON)
2. `ExportOptions` - Configuration for export operation
3. `ExportProgress` - Real-time export status tracking
4. `QueryResult` - Input data from query execution
5. `CSVOutput` / `JSONExport` - Output data structures
6. `ExportError` - Error handling

**Design Principles**:
- ✅ Strict TypeScript types for all data structures
- ✅ Immutable data patterns (no mutation of input)
- ✅ Clear separation of concerns (input, processing, output)
- ✅ Comprehensive error handling
- ✅ User-friendly defaults
- ✅ Extensible for future enhancements

**Next Steps**:
- Create TypeScript contract files in `contracts/`
- Generate test scenarios in `contracts/test-scenarios.md`
- Create integration guide in `quickstart.md`
