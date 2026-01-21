/**
 * File Download Helper
 *
 * Wrapper around FileSaver.js for browser file downloads with error handling
 */

import { saveAs } from 'file-saver';

/**
 * Download file to user's local filesystem
 */
export function downloadFile(
  content: string,
  filename: string,
  mimeType: string
): void {
  try {
    const blob = new Blob([content], { type: mimeType });
    saveAs(blob, filename);
  } catch (error) {
    // Re-throw with more context
    const message = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Failed to download file: ${message}`);
  }
}

/**
 * Download file with size information
 */
export function downloadFileWithSize(
  content: string,
  filename: string,
  mimeType: string
): { filename: string; fileSize: number } {
  const blob = new Blob([content], { type: mimeType });
  const fileSize = blob.size;

  saveAs(blob, filename);

  return { filename, fileSize };
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`;
}

/**
 * Check if browser supports file downloads
 */
export function isDownloadSupported(): boolean {
  try {
    return typeof Blob !== 'undefined' && typeof saveAs === 'function';
  } catch {
    return false;
  }
}
