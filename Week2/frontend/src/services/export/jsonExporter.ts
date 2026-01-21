/**
 * JSON Exporter Service
 *
 * Exports query results to JSON format with metadata and type preservation
 */

import type { QueryResult } from '@/types/query';
import type {
  JSONExport,
  JSONOptions,
  ExportMetadata,
  CellValue,
} from '@/types/export';
import { DEFAULT_JSON_OPTIONS } from '@/types/export';
import { convertToJSON } from '@/utils/export/typeConverter';

/**
 * Export query results to JSON format
 */
export function exportToJSON(
  queryResult: QueryResult,
  options: JSONOptions = {}
): string {
  const opts = { ...DEFAULT_JSON_OPTIONS, ...options };

  // Convert rows with type preservation
  const convertedRows = queryResult.rows.map(row => {
    const converted: Record<string, CellValue> = {};
    for (const [key, value] of Object.entries(row)) {
      converted[key] = convertToJSON(value) as CellValue;
    }
    return converted;
  });

  // Build JSON export structure
  const jsonExport: JSONExport = {
    ...(opts.includeMetadata && {
      metadata: buildMetadata(queryResult),
    }),
    data: convertedRows,
  };

  // Stringify with optional pretty-printing
  if (opts.prettyPrint) {
    return JSON.stringify(jsonExport, null, opts.indent || 2);
  }

  return JSON.stringify(jsonExport);
}

/**
 * Build metadata object for JSON export
 */
function buildMetadata(queryResult: QueryResult): ExportMetadata {
  return {
    columns: queryResult.columns,
    exportedAt: new Date().toISOString(),
    rowCount: queryResult.rowCount,
    ...(queryResult.sql && { sql: queryResult.sql }),
  };
}

/**
 * Export query results to minimal JSON (array only, no metadata)
 */
export function exportToMinimalJSON(
  queryResult: QueryResult,
  prettyPrint: boolean = false
): string {
  const convertedRows = queryResult.rows.map(row => {
    const converted: Record<string, CellValue> = {};
    for (const [key, value] of Object.entries(row)) {
      converted[key] = convertToJSON(value) as CellValue;
    }
    return converted;
  });

  if (prettyPrint) {
    return JSON.stringify(convertedRows, null, 2);
  }

  return JSON.stringify(convertedRows);
}

/**
 * Validate query results before JSON export
 */
export function validateForJSONExport(queryResult: QueryResult): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  // Check if results exist
  if (!queryResult) {
    errors.push('Query results are null or undefined');
  }

  // Check if columns exist
  if (!queryResult.columns || queryResult.columns.length === 0) {
    errors.push('No columns defined in query results');
  }

  // Check if rows exist
  if (!queryResult.rows) {
    errors.push('Rows array is missing');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
