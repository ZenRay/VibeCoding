# Quick Start Guide: Export Query Results

**Feature**: Query Results Export
**Date**: 2026-01-22
**Audience**: Developers integrating export functionality

## Overview

This guide shows how to integrate the export functionality into the existing database query tool. The export feature is 100% client-side and extends the query results display from feature 002.

## Prerequisites

- ✅ Feature 002 (MySQL database support) completed
- ✅ Query results tab displaying data
- ✅ Notification system available
- ✅ React 18+ with TypeScript
- ✅ Ant Design 5 components

## Installation

### 1. Install Dependencies

```bash
cd frontend
npm install papaparse file-saver
npm install -D @types/papaparse @types/file-saver
```

**Dependencies**:
- `papaparse@^5.5.3` - RFC 4180 compliant CSV generation (~7.58 kB gzipped)
- `file-saver@^2.0.5` - Cross-browser file downloads (~2.5 kB gzipped)

**Total bundle impact**: ~10 kB gzipped

### 2. Copy Type Definitions

```bash
# Copy TypeScript types to your frontend src/types directory
cp specs/003-export-query-results/contracts/export-types.ts \
   frontend/src/types/export.ts
```

## Integration Steps

### Step 1: Create Export Services

Create the export utility files in `frontend/src/services/export/`:

**File: `frontend/src/services/export/csvExporter.ts`**

```typescript
import Papa from 'papaparse';
import type { QueryResult, CSVOutput } from '@/types/export';

export function exportToCSV(queryResult: QueryResult): CSVOutput {
  // Generate CSV using PapaParse
  const csv = Papa.unparse({
    fields: queryResult.columns.map(c => c.name),
    data: queryResult.rows
  });

  // Add UTF-8 BOM for Excel compatibility
  return '\ufeff' + csv;
}
```

**File: `frontend/src/services/export/jsonExporter.ts`**

```typescript
import type { QueryResult, JSONExport } from '@/types/export';

export function exportToJSON(
  queryResult: QueryResult,
  includeMetadata: boolean = true
): string {
  const jsonExport: JSONExport = {
    ...(includeMetadata && {
      metadata: {
        columns: queryResult.columns,
        exportedAt: new Date().toISOString(),
        rowCount: queryResult.rowCount,
        sql: queryResult.sql
      }
    }),
    data: queryResult.rows
  };

  return JSON.stringify(jsonExport, null, 2);
}
```

**File: `frontend/src/services/export/fileDownload.ts`**

```typescript
import { saveAs } from 'file-saver';

export function downloadFile(
  content: string,
  filename: string,
  mimeType: string
): void {
  const blob = new Blob([content], { type: mimeType });
  saveAs(blob, filename);
}
```

### Step 2: Create Export Hook

**File: `frontend/src/hooks/useExport.ts`**

```typescript
import { useState } from 'react';
import { notification } from 'antd';
import { exportToCSV } from '@/services/export/csvExporter';
import { exportToJSON } from '@/services/export/jsonExporter';
import { downloadFile } from '@/services/export/fileDownload';
import type { QueryResult, ExportFormat, ExportOptions } from '@/types/export';

export function useExport() {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (
    queryResult: QueryResult,
    options: ExportOptions
  ) => {
    setIsExporting(true);

    try {
      let content: string;

      // Generate export content
      if (options.format.type === 'csv') {
        content = exportToCSV(queryResult);
      } else {
        content = exportToJSON(queryResult, options.includeMetadata);
      }

      // Generate filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const filename = `${options.filename}_${timestamp}.${options.format.extension}`;

      // Trigger download
      downloadFile(content, filename, options.format.mimeType);

      // Success notification
      notification.success({
        message: 'Export Complete',
        description: `${queryResult.rowCount} rows exported to ${filename}`,
        duration: 4
      });

    } catch (error) {
      // Error notification
      notification.error({
        message: 'Export Failed',
        description: error instanceof Error ? error.message : 'An error occurred during export',
        duration: 6
      });

    } finally {
      setIsExporting(false);
    }
  };

  return { handleExport, isExporting };
}
```

### Step 3: Create Export Button Component

**File: `frontend/src/components/export/ExportButton.tsx`**

```typescript
import { useState } from 'react';
import { Button, Modal } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { useExport } from '@/hooks/useExport';
import { EXPORT_FORMATS } from '@/types/export';
import type { QueryResult } from '@/types/export';

interface ExportButtonProps {
  queryResult: QueryResult | null;
  disabled?: boolean;
}

export function ExportButton({ queryResult, disabled }: ExportButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { handleExport, isExporting } = useExport();

  const onExport = async (formatType: 'csv' | 'json') => {
    if (!queryResult) return;

    const format = formatType === 'csv' ? EXPORT_FORMATS.CSV : EXPORT_FORMATS.JSON;

    await handleExport(queryResult, {
      format,
      filename: 'query_results',
      includeMetadata: true,
      includeExcelBom: true,
      showProgress: true
    });

    setIsModalOpen(false);
  };

  return (
    <>
      <Button
        type="primary"
        icon={<DownloadOutlined />}
        onClick={() => setIsModalOpen(true)}
        disabled={disabled || !queryResult || queryResult.rowCount === 0}
        loading={isExporting}
      >
        Export
      </Button>

      <Modal
        title="Export Query Results"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <Button
            size="large"
            block
            onClick={() => onExport('csv')}
            loading={isExporting}
          >
            <div>
              <strong>{EXPORT_FORMATS.CSV.label}</strong>
              <div style={{ fontSize: '12px', color: '#666' }}>
                {EXPORT_FORMATS.CSV.description}
              </div>
            </div>
          </Button>

          <Button
            size="large"
            block
            onClick={() => onExport('json')}
            loading={isExporting}
          >
            <div>
              <strong>{EXPORT_FORMATS.JSON.label}</strong>
              <div style={{ fontSize: '12px', color: '#666' }}>
                {EXPORT_FORMATS.JSON.description}
              </div>
            </div>
          </Button>
        </div>
      </Modal>
    </>
  );
}
```

### Step 4: Integrate into Query Results Page

**File: `frontend/src/pages/QueryResultsPage.tsx` (example integration)**

```typescript
import { ExportButton } from '@/components/export/ExportButton';

export function QueryResultsPage() {
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [isQueryRunning, setIsQueryRunning] = useState(false);

  return (
    <div>
      {/* Query editor and other UI */}

      {/* Results tab with export button */}
      <Tabs defaultActiveKey="results">
        <TabPane tab="Results" key="results">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              {queryResult && (
                <span>{queryResult.rowCount} rows returned</span>
              )}
            </div>

            {/* Export Button */}
            <ExportButton
              queryResult={queryResult}
              disabled={isQueryRunning}
            />
          </div>

          {/* Results table */}
          {queryResult && (
            <Table
              columns={queryResult.columns.map(col => ({
                title: col.name,
                dataIndex: col.name,
                key: col.name
              }))}
              dataSource={queryResult.rows}
            />
          )}
        </TabPane>
      </Tabs>
    </div>
  );
}
```

## Verification

### 1. CSV Export Test

```typescript
// Test data
const testQueryResult: QueryResult = {
  columns: [
    { name: 'id', dataType: 'number' },
    { name: 'name', dataType: 'string' },
    { name: 'email', dataType: 'string' }
  ],
  rows: [
    { id: 1, name: 'John Doe', email: 'john@example.com' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
  ],
  rowCount: 2
};

// Export and verify
handleExport(testQueryResult, {
  format: EXPORT_FORMATS.CSV,
  filename: 'test',
  includeExcelBom: true
});

// Expected file: test_2026-01-22T10-30-00.csv
// Content should include UTF-8 BOM and proper CSV formatting
```

### 2. Open CSV in Excel

1. Export query results to CSV
2. Open file in Microsoft Excel
3. Verify:
   - ✅ UTF-8 characters display correctly (Chinese, emojis, accents)
   - ✅ Columns aligned properly
   - ✅ No corruption

### 3. Validate JSON Export

```bash
# Export query results to JSON
# Validate with jq
cat query_results_2026-01-22T10-30-00.json | jq .

# Verify metadata present
cat query_results_2026-01-22T10-30-00.json | jq '.metadata'

# Verify data array
cat query_results_2026-01-22T10-30-00.json | jq '.data | length'
```

## Testing

### E2E Test (Playwright)

```typescript
// frontend/tests/e2e/export.spec.ts
import { test, expect } from '@playwright/test';

test('should export query results to CSV', async ({ page }) => {
  // Navigate to query page
  await page.goto('/');

  // Execute query
  await page.fill('[data-testid="sql-editor"]', 'SELECT * FROM users LIMIT 10');
  await page.click('[data-testid="execute-query"]');

  // Wait for results
  await page.waitForSelector('[data-testid="query-results"]');

  // Click export button
  await page.click('button:has-text("Export")');

  // Select CSV format
  await page.click('button:has-text("CSV")');

  // Verify download started
  const download = await page.waitForEvent('download');
  expect(download.suggestedFilename()).toMatch(/query_results_.*\.csv/);
});
```

### Unit Test (Vitest)

```typescript
// frontend/tests/unit/export/csvExporter.test.ts
import { describe, test, expect } from 'vitest';
import { exportToCSV } from '@/services/export/csvExporter';

describe('CSV Exporter', () => {
  test('should include UTF-8 BOM', () => {
    const result = exportToCSV({
      columns: [{ name: 'id', dataType: 'number' }],
      rows: [{ id: 1 }],
      rowCount: 1
    });

    expect(result.startsWith('\ufeff')).toBe(true);
  });

  test('should handle commas in fields', () => {
    const result = exportToCSV({
      columns: [{ name: 'name', dataType: 'string' }],
      rows: [{ name: 'Smith, John' }],
      rowCount: 1
    });

    expect(result).toContain('"Smith, John"');
  });
});
```

## Troubleshooting

### Issue: CSV doesn't open correctly in Excel

**Solution**: Ensure UTF-8 BOM is included:

```typescript
// In csvExporter.ts, make sure BOM is prepended
return '\ufeff' + csv;  // \ufeff is UTF-8 BOM
```

### Issue: Special characters corrupted

**Solution**: Verify Blob MIME type includes UTF-8:

```typescript
const blob = new Blob([content], { type: 'text/csv;charset=utf-8' });
```

### Issue: Large exports freeze browser

**Solution**: For >50,000 rows, implement Web Worker:

```typescript
// See research.md Phase 1 for Web Worker implementation
// Or warn users about large exports
if (rowCount > 50000) {
  notification.warning({
    message: 'Large Dataset',
    description: 'This export may take some time. Browser may become temporarily unresponsive.'
  });
}
```

### Issue: File doesn't download in Safari

**Solution**: FileSaver.js automatically handles Safari quirks. Ensure library is properly imported:

```typescript
import { saveAs } from 'file-saver';  // Not 'FileSaver'
```

## Performance Benchmarks

| Rows | Columns | CSV Time | JSON Time | File Size |
|------|---------|----------|-----------|-----------|
| 100 | 10 | <50ms | <30ms | ~10 KB |
| 1,000 | 10 | ~100ms | ~80ms | ~100 KB |
| 10,000 | 10 | ~500ms | ~400ms | ~1 MB |
| 50,000 | 10 | ~2s | ~1.5s | ~5 MB |

## Browser Compatibility

| Browser | CSV Export | JSON Export | Notes |
|---------|------------|-------------|-------|
| Chrome 131+ | ✅ | ✅ | Full support |
| Firefox 132+ | ✅ | ✅ | Full support |
| Safari 18+ | ✅ | ✅ | May show save dialog |
| Edge 145+ | ✅ | ✅ | Full support |
| Mobile Safari | ✅ | ✅ | Works on iOS 15+ |

## Next Steps

1. **Add Progress Indicator**: Implement `ExportProgress.tsx` for large datasets
2. **Add Filename Customization**: Allow users to edit filename before export
3. **Add Export History**: Track recent exports (localStorage)
4. **Add Web Worker**: Optimize for very large datasets (>50,000 rows)
5. **Add Export Preview**: Show first 10 rows before download

## References

- [Feature Specification](./spec.md)
- [Technical Research](./research.md)
- [Data Model](./data-model.md)
- [Type Definitions](./contracts/export-types.ts)
- [Test Scenarios](./contracts/test-scenarios.md)

---

**Questions?** Refer to the research.md document for technical decisions and alternatives considered.

**Status**: Integration guide complete - ready for implementation
