/**
 * CSV Exporter Service
 *
 * Exports query results to CSV format with RFC 4180 compliance
 */

import Papa from 'papaparse';
import type { QueryResult } from '@/types/query';
import type { CSVOutput, CSVOptions } from '@/types/export';
import { DEFAULT_CSV_OPTIONS } from '@/types/export';
import { convertToCSVString } from '@/utils/export/typeConverter';

/**
 * Export query results to CSV format
 */
export function exportToCSV(
  queryResult: QueryResult,
  options: CSVOptions = {}
): CSVOutput {
  const opts = { ...DEFAULT_CSV_OPTIONS, ...options };

  // Prepare column names
  const fields = queryResult.columns.map(col => col.name);

  // Convert rows to array of arrays (for PapaParse)
  const data = queryResult.rows.map(row =>
    fields.map(field => convertToCSVString(row[field]))
  );

  // Generate CSV using PapaParse
  const csv = Papa.unparse({
    fields,
    data,
  }, {
    quotes: opts.quoteAll || false,
    delimiter: opts.delimiter || ',',
    newline: opts.lineEnding || '\r\n',
    header: opts.includeHeaders !== false,
  });

  // Add UTF-8 BOM for Excel compatibility (if enabled)
  if (opts.includeBOM !== false) {
    return '\ufeff' + csv;
  }

  return csv;
}

/**
 * Validate query results before CSV export
 */
export function validateForCSVExport(queryResult: QueryResult): {
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

  // Check if rows exist (allow empty rows for headers-only export)
  if (!queryResult.rows) {
    errors.push('Rows array is missing');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
