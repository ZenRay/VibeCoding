/**
 * Type Converter Utility
 *
 * Handles data type preservation and conversion for exports
 */

import type { CellValue } from '@/types/export';

/**
 * Convert cell value to string for CSV export
 */
export function convertToCSVString(value: unknown): string {
  // Handle null and undefined
  if (value === null || value === undefined) {
    return '';
  }

  // Handle Date objects
  if (value instanceof Date) {
    return value.toISOString();
  }

  // Handle booleans
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }

  // Handle numbers
  if (typeof value === 'number') {
    return String(value);
  }

  // Handle strings
  return String(value);
}

/**
 * Convert cell value for JSON export (preserving types)
 */
export function convertToJSON(value: unknown): unknown {
  // Handle null and undefined
  if (value === null) {
    return null;
  }

  if (value === undefined) {
    return null;
  }

  // Handle Date objects - convert to ISO 8601 string
  if (value instanceof Date) {
    return value.toISOString();
  }

  // Preserve other types as-is (number, boolean, string)
  return value;
}

/**
 * Convert ISO date string to Date object
 */
export function parseISODate(value: string): Date | null {
  try {
    const date = new Date(value);
    return isNaN(date.getTime()) ? null : date;
  } catch {
    return null;
  }
}

/**
 * Detect if a value is a date-like string
 */
export function isDateLike(value: unknown): boolean {
  if (typeof value !== 'string') {
    return false;
  }

  // ISO 8601 pattern
  const iso8601Pattern = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d{3})?(Z|[+-]\d{2}:\d{2})?)?$/;
  return iso8601Pattern.test(value);
}

/**
 * Infer data type from value
 */
export function inferDataType(value: CellValue): string {
  if (value === null || value === undefined) {
    return 'null';
  }

  if (value instanceof Date) {
    return 'date';
  }

  if (typeof value === 'boolean') {
    return 'boolean';
  }

  if (typeof value === 'number') {
    return 'number';
  }

  if (typeof value === 'string') {
    if (isDateLike(value)) {
      return 'date';
    }
    return 'string';
  }

  return 'unknown';
}
