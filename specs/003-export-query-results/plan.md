# Implementation Plan: Query Results Export

**Branch**: `003-export-query-results` | **Date**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-export-query-results/spec.md`

## Summary

Add client-side export functionality to the database query tool, allowing users to export query results to CSV or JSON formats. The export will be entirely frontend-based, building on the existing query results display from feature 002 (MySQL support). The system will automatically handle format-specific requirements (RFC 4180 CSV, proper JSON encoding, special character escaping) and support exporting up to 10,000+ rows efficiently without browser performance degradation.

## Technical Context

**Language/Version**: TypeScript 5.0+ (frontend only - no backend changes required)
**Primary Dependencies**: React 18+, Ant Design 5, Browser File APIs (Blob, download attribute)
**Storage**: N/A (client-side file download only)
**Testing**: Playwright (E2E), Vitest (unit tests for formatters)
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend-only feature)
**Performance Goals**: Export 10,000 rows in <30s (CSV), <45s (JSON); maintain browser responsiveness
**Constraints**: <100MB memory for typical exports; support RFC 4180 CSV; UTF-8 encoding with BOM for CSV
**Scale/Scope**: Single feature module with ~5-8 new files (components, hooks, utilities, tests)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Frontend Standards (All ✅ PASS)

- ✅ **TypeScript strict mode**: All export utilities, hooks, and components will use strict TypeScript with full type annotations
- ✅ **Functional components with hooks**: Export button component and format dialog will use functional React patterns
- ✅ **Type-safe interfaces**: Export format types, query result types, and export options will have explicit TypeScript interfaces
- ✅ **No authentication**: Feature operates on already-loaded query results; no auth required
- ✅ **camelCase JSON**: If any configuration is serialized, will use camelCase (though export formats are CSV/JSON data, not API responses)
- ✅ **Ergonomic code**: Clear naming (e.g., `exportToCSV`, `formatCellValue`, `generateFilename`)

### Compliance Notes

- **No backend changes required**: Feature is 100% client-side, leveraging existing query result data structure
- **No new API endpoints**: Export operates entirely in browser memory
- **Follows existing patterns**: Integrates with existing query results tab, notification system, and UI components

**Gate Status**: ✅ **PASS** - All constitution principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/003-export-query-results/
├── plan.md              # This file
├── research.md          # Phase 0: Technology research (CSV/JSON libraries, browser APIs)
├── data-model.md        # Phase 1: Export data structures and types
├── quickstart.md        # Phase 1: Integration guide for export feature
├── contracts/           # Phase 1: TypeScript interfaces, format specifications
│   ├── export-types.ts      # Export format types, options, result types
│   └── test-scenarios.md    # Test cases for formatters and edge cases
└── tasks.md             # Phase 2: Step-by-step implementation tasks
```

### Source Code (Week2 directory structure)

```text
frontend/src/
├── components/
│   └── export/
│       ├── ExportButton.tsx         # Main export button component
│       ├── ExportFormatDialog.tsx   # Format selection modal
│       └── ExportProgress.tsx       # Progress indicator for large exports
│
├── hooks/
│   └── useExport.ts                 # Export logic hook (format selection, file download)
│
├── services/
│   └── export/
│       ├── csvExporter.ts           # CSV format generation (RFC 4180)
│       ├── jsonExporter.ts          # JSON format generation
│       ├── formatDetector.ts        # Auto-detect delimiters, special chars
│       └── fileDownload.ts          # Browser download helper (Blob + download link)
│
├── types/
│   └── export.ts                    # TypeScript interfaces for export
│
└── utils/
    └── export/
        ├── filenameGenerator.ts     # Generate default filenames
        ├── csvEscaper.ts            # CSV field escaping (quotes, commas, newlines)
        └── typeConverter.ts         # Data type preservation for JSON

frontend/tests/e2e/
└── export.spec.ts                   # Playwright E2E tests for export workflows

frontend/tests/unit/
└── export/
    ├── csvExporter.test.ts          # Unit tests for CSV formatter
    ├── jsonExporter.test.ts         # Unit tests for JSON formatter
    ├── formatDetector.test.ts       # Unit tests for format detection
    └── csvEscaper.test.ts           # Unit tests for CSV escaping logic
```

**Structure Decision**: Frontend-only implementation since export operates on already-loaded query results. No backend endpoints required. Components follow existing Ant Design patterns. Services follow existing separation (export logic separate from UI).

## Complexity Tracking

> **No constitution violations detected** - This feature aligns with all established principles.

---

## Phase 0: Research & Technology Selection

### Research Tasks

1. **CSV Generation Libraries vs Manual Implementation**
   - **Research**: Evaluate papaparse, csv-stringify-browser, vs custom RFC 4180 implementation
   - **Decision criteria**: Bundle size, RFC 4180 compliance, special character handling, performance on large datasets
   - **Outcome**: Document selected approach with rationale

2. **Browser File Download Mechanisms**
   - **Research**: File System Access API vs download attribute vs FileSaver.js
   - **Decision criteria**: Browser compatibility (Chrome, Firefox, Safari, Edge), user experience, permissions required
   - **Outcome**: Document primary method and fallback strategy

3. **Large Dataset Performance Patterns**
   - **Research**: Chunking strategies, Web Workers for processing, streaming vs in-memory generation
   - **Decision criteria**: 10,000 row target, browser memory limits, UI responsiveness requirements
   - **Outcome**: Document performance optimization approach

4. **CSV Encoding Standards**
   - **Research**: UTF-8 with BOM for Excel compatibility, RFC 4180 compliance, special character handling
   - **Decision criteria**: Excel/Google Sheets compatibility, data integrity, international characters
   - **Outcome**: Document encoding strategy and edge case handling

### Output: research.md

Document covering:
- CSV library selection (or custom implementation decision)
- File download API choice with browser compatibility matrix
- Performance optimization strategy for large exports
- Encoding and special character handling approach
- Alternative solutions considered and why rejected

---

## Phase 1: Design & Contracts

### Data Models

**File**: `data-model.md`

#### Export Configuration

```typescript
interface ExportFormat {
  type: 'csv' | 'json';
  label: string;
  extension: string;
  mimeType: string;
}

interface ExportOptions {
  format: ExportFormat;
  filename: string;
  includeMetadata: boolean; // For JSON exports
}

interface ExportProgress {
  totalRows: number;
  processedRows: number;
  percentage: number;
  status: 'preparing' | 'processing' | 'downloading' | 'complete' | 'error' | 'cancelled';
  errorMessage?: string;
}
```

#### Query Result Structure (from existing feature 002)

```typescript
interface QueryResult {
  columns: ColumnMetadata[];
  rows: Row[];
  rowCount: number;
  executionTimeMs: number;
}

interface ColumnMetadata {
  name: string;
  dataType: string; // 'string' | 'number' | 'boolean' | 'date' | 'null'
}

type Row = Record<string, unknown>; // Column name → value
```

#### CSV/JSON Output Structures

```typescript
// CSV: string with RFC 4180 formatting
type CSVOutput = string;

// JSON: array of objects with optional metadata
interface JSONExport {
  metadata?: {
    columns: ColumnMetadata[];
    exportedAt: string;
    rowCount: number;
  };
  data: Row[];
}
```

### API Contracts

**File**: `contracts/export-types.ts`

Complete TypeScript type definitions for:
- Export format enum and type guards
- Export options validation
- Progress tracking interface
- Error types for export failures (disk full, permissions, etc.)
- Browser compatibility checks

**File**: `contracts/test-scenarios.md`

Test scenarios covering:
- Standard data types (strings, numbers, dates, booleans, nulls)
- Special characters (commas, quotes, newlines, tabs, Unicode)
- Edge cases (empty results, single row, 50+ columns, binary data)
- Large datasets (10,000+ rows)
- Error conditions (user cancels, disk full, browser memory limit)

### Integration Guide

**File**: `quickstart.md`

Integration steps:
1. Import `ExportButton` component into query results tab
2. Pass `queryResults` prop from existing state
3. Configure notification system for success/error messages
4. Add E2E test scenarios to existing Playwright suite
5. Verify CSV files open correctly in Excel/Google Sheets
6. Verify JSON files parse correctly with standard JSON parsers

### Agent Context Update

Run: `.specify/scripts/bash/update-agent-context.sh claude`

Add to context:
- Browser File APIs (Blob, URL.createObjectURL, download attribute)
- RFC 4180 CSV standard
- UTF-8 encoding with BOM
- React hooks for file download
- Ant Design Modal patterns

---

## Next Steps

After completing Phase 1, run:
```bash
/speckit.tasks
```

This will generate `tasks.md` with step-by-step implementation tasks organized by:
- Setup: TypeScript types, folder structure, test scaffolding
- Tests: Unit tests for formatters, E2E tests for workflows
- Core: Export components, hooks, formatters (CSV/JSON)
- Integration: Query results tab integration, notifications
- Polish: Performance optimization, browser compatibility, documentation

**Status**: Plan complete - ready for Phase 0 research
