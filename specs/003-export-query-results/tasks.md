# Tasks: Query Results Export

**Input**: Design documents from `/specs/003-export-query-results/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Unit and E2E tests included for comprehensive validation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/`, `frontend/tests/`
- **Backend**: Not required for this feature (client-side only)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies and create folder structure

- [X] T001 Install papaparse and file-saver dependencies in frontend/package.json
- [X] T002 [P] Install TypeScript type definitions @types/papaparse and @types/file-saver
- [X] T003 [P] Create export types folder structure: frontend/src/types/export.ts
- [X] T004 [P] Create export services folder: frontend/src/services/export/
- [X] T005 [P] Create export components folder: frontend/src/components/export/
- [X] T006 [P] Create export utils folder: frontend/src/utils/export/
- [X] T007 [P] Create export tests folder: frontend/tests/unit/export/

---

## Phase 2: Foundational (Core Export Infrastructure)

**Purpose**: Core types and utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Copy TypeScript type definitions from contracts/export-types.ts to frontend/src/types/export.ts
- [X] T009 [P] Create filename generator utility in frontend/src/utils/export/filenameGenerator.ts (sanitization, timestamps, extension handling)
- [X] T010 [P] Create file download helper in frontend/src/services/export/fileDownload.ts (FileSaver.js wrapper with error handling)
- [X] T011 [P] Create type converter utility in frontend/src/utils/export/typeConverter.ts (date to ISO 8601, null handling, type preservation)

**Checkpoint**: Foundation ready - user story implementation can now begin ✅

---

## Phase 3: User Story 1 - Export Query Results to Local File (Priority: P1) 🎯 MVP

**Goal**: Enable users to export query results to CSV or JSON with basic formatting

**Independent Test**: Execute a SQL query → Click Export button → Select CSV format → Verify downloaded file contains correct data with headers → Open in Excel and verify data displays correctly

### Implementation for User Story 1

- [X] T012 [P] [US1] Create CSV exporter service in frontend/src/services/export/csvExporter.ts (PapaParse integration, UTF-8 BOM, header generation)
- [X] T013 [P] [US1] Create JSON exporter service in frontend/src/services/export/jsonExporter.ts (JSON.stringify with metadata, type preservation)
- [X] T014 [US1] Create useExport hook in frontend/src/hooks/useExport.ts (format selection logic, file download orchestration, success/error notifications)
- [X] T015 [US1] Create ExportButton component in frontend/src/components/export/ExportButton.tsx (button UI, disabled states, loading indicator)
- [X] T016 [US1] Create ExportFormatDialog component in frontend/src/components/export/ExportFormatDialog.tsx (Ant Design Modal, CSV/JSON options with descriptions)
- [X] T017 [US1] Integrate ExportButton into query results tab/page (import component, pass queryResult prop, handle button states)
- [X] T018 [US1] Add success notification after export completion (show filename, row count, file size)
- [X] T019 [US1] Add error notification for export failures (permission denied, disk full, generic errors)

### E2E Tests for User Story 1

- [ ] T020 [US1] Create E2E test for CSV export workflow in frontend/tests/e2e/export.spec.ts (query → export → verify download)
- [ ] T021 [US1] Create E2E test for JSON export workflow in frontend/tests/e2e/export.spec.ts (query → export → verify JSON structure)
- [ ] T022 [US1] Create E2E test for export button disabled states in frontend/tests/e2e/export.spec.ts (no results, query running)

**Checkpoint**: User Story 1 complete - Users can export basic query results to CSV/JSON ✅

---

## Phase 4: User Story 2 - Automatic Format Detection and Optimization (Priority: P2)

**Goal**: Handle special characters and complex data types automatically without user configuration

**Independent Test**: Execute query with commas in text, quotes, newlines, various data types → Export to CSV → Verify all special characters are properly escaped → Open in Excel and verify data integrity → Export same query to JSON → Verify types preserved

### Implementation for User Story 2

- [ ] T023 [P] [US2] Create CSV escaper utility in frontend/src/utils/export/csvEscaper.ts (RFC 4180 escaping: commas, quotes, newlines, tabs)
- [ ] T024 [P] [US2] Create format detector utility in frontend/src/services/export/formatDetector.ts (detect special chars, auto-quote fields)
- [ ] T025 [US2] Add formula injection prevention in frontend/src/utils/export/csvEscaper.ts (prefix =, +, -, @ with single quote)
- [ ] T026 [US2] Enhance CSV exporter to use escaper and format detector in frontend/src/services/export/csvExporter.ts
- [ ] T027 [US2] Enhance JSON exporter with type preservation in frontend/src/services/export/jsonExporter.ts (numbers not quoted, booleans as JSON bool, nulls as JSON null, dates as ISO 8601)
- [ ] T028 [US2] Add NULL value handling for both CSV (empty field) and JSON (null) formats
- [ ] T029 [US2] Add date/datetime formatting to ISO 8601 strings in both formats

### Unit Tests for User Story 2

- [ ] T030 [P] [US2] Unit test CSV escaper with commas in frontend/tests/unit/export/csvEscaper.test.ts
- [ ] T031 [P] [US2] Unit test CSV escaper with quotes in frontend/tests/unit/export/csvEscaper.test.ts
- [ ] T032 [P] [US2] Unit test CSV escaper with newlines in frontend/tests/unit/export/csvEscaper.test.ts
- [ ] T033 [P] [US2] Unit test formula injection prevention in frontend/tests/unit/export/csvEscaper.test.ts
- [ ] T034 [P] [US2] Unit test JSON type preservation in frontend/tests/unit/export/jsonExporter.test.ts
- [ ] T035 [P] [US2] Unit test NULL handling in both formats in frontend/tests/unit/export/csvExporter.test.ts and jsonExporter.test.ts

### E2E Tests for User Story 2

- [ ] T036 [US2] E2E test for special characters export in frontend/tests/e2e/export.spec.ts (create test data with commas, quotes, newlines → export → verify)
- [ ] T037 [US2] E2E test for Unicode characters export in frontend/tests/e2e/export.spec.ts (Chinese, Arabic, emojis → export CSV → open in Excel → verify)
- [ ] T038 [US2] E2E test for type preservation in JSON in frontend/tests/e2e/export.spec.ts (numbers, booleans, nulls → export JSON → parse and verify types)

**Checkpoint**: User Story 2 complete - Special characters and data types handled automatically ✅

---

## Phase 5: User Story 3 - Export Large Result Sets (Priority: P3)

**Goal**: Support exporting 10,000+ rows without browser crashes or excessive delays

**Independent Test**: Execute query returning 10,000 rows → Click export → Verify progress indicator appears → Wait for completion → Verify export completes in <30 seconds → Verify browser remains responsive → Open exported file and verify all 10,000 rows present

### Implementation for User Story 3

- [ ] T039 [US3] Create ExportProgress component in frontend/src/components/export/ExportProgress.tsx (progress bar, percentage, cancel button)
- [ ] T040 [US3] Add progress tracking to useExport hook in frontend/src/hooks/useExport.ts (calculate percentage, update state)
- [ ] T041 [US3] Add progress indicator display logic (show for >2 second exports) in useExport hook
- [ ] T042 [US3] Implement export cancellation in useExport hook (cancel button handler, cleanup logic)
- [ ] T043 [US3] Add memory-efficient chunking for very large datasets (>50,000 rows) in csvExporter and jsonExporter
- [ ] T044 [US3] Add warning notification for extremely large exports (>100,000 rows) with user confirmation
- [ ] T045 [US3] Optimize CSV generation performance for large datasets (verify <30 seconds for 10,000 rows)

### Unit Tests for User Story 3

- [ ] T046 [P] [US3] Unit test progress calculation in frontend/tests/unit/export/useExport.test.ts
- [ ] T047 [P] [US3] Unit test export cancellation in frontend/tests/unit/export/useExport.test.ts
- [ ] T048 [P] [US3] Performance test for 10,000 row CSV export in frontend/tests/unit/export/csvExporter.test.ts
- [ ] T049 [P] [US3] Performance test for 10,000 row JSON export in frontend/tests/unit/export/jsonExporter.test.ts

### E2E Tests for User Story 3

- [ ] T050 [US3] E2E test for large dataset export (10,000 rows) in frontend/tests/e2e/export.spec.ts (verify completion time, browser responsiveness)
- [ ] T051 [US3] E2E test for progress indicator display in frontend/tests/e2e/export.spec.ts (verify shown for large exports)
- [ ] T052 [US3] E2E test for export cancellation in frontend/tests/e2e/export.spec.ts (click cancel button mid-export, verify cleanup)

**Checkpoint**: User Story 3 complete - Large datasets export efficiently ✅

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and cross-story enhancements

- [ ] T053 [P] Add JSDoc comments to all export functions and hooks
- [ ] T054 [P] Add error boundary around export components in case of unexpected errors
- [ ] T055 [P] Verify CSV files open correctly in Excel (manual test on Windows/Mac)
- [ ] T056 [P] Verify CSV files open correctly in Google Sheets (manual test)
- [ ] T057 [P] Test across browsers: Chrome, Firefox, Safari, Edge (manual compatibility test)
- [ ] T058 Run all E2E tests and verify all scenarios pass
- [ ] T059 Run all unit tests and verify code coverage for export module
- [ ] T060 Validate implementation against quickstart.md integration guide
- [ ] T061 Update project README with export feature documentation (if README exists)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) completion - Can run parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) completion - Can run parallel with US1/US2
- **Polish (Phase 6)**: Depends on all implemented user stories

### User Story Dependencies

```
Foundation (Phase 2)
        ↓
    ┌───┴───┬───────┐
    ↓       ↓       ↓
   US1     US2     US3
  (P1)    (P2)    (P3)
    │       │       │
    └───┬───┴───┬───┘
        ↓       ↓
      Polish (Phase 6)
```

**Dependency Matrix**:

| Story | Depends On | Can Start After | Blocks |
|-------|------------|-----------------|--------|
| US1 (P1) | Foundation | Phase 2 complete | None (independent) |
| US2 (P2) | Foundation, optionally US1 | Phase 2 complete | None (independent) |
| US3 (P3) | Foundation, US1 | Phase 2 complete | None (independent) |

**Notes**:
- User Story 2 and 3 build on US1 but should remain independently testable
- All three stories can be developed in parallel after Foundation is complete
- Recommended sequence for solo dev: US1 → US2 → US3 (priority order)

### Within Each User Story

**Execution Order per Story**:
1. Tests FIRST (write and verify they fail)
2. Utilities and services (marked [P] can run parallel)
3. Components (may depend on services)
4. Integration (depends on components)
5. Validation (verify story works independently)

### Parallel Opportunities

**Phase 1 (Setup)** - All 7 tasks can run in parallel

**Phase 2 (Foundational)** - Tasks T009-T011 can run in parallel (different files)

**User Story 1**:
- T012 (CSV exporter) and T013 (JSON exporter) can run in parallel
- T015 (ExportButton) and T016 (ExportFormatDialog) can run in parallel
- E2E tests T020-T022 can run in parallel

**User Story 2**:
- T023 (CSV escaper), T024 (format detector), T025 (formula injection) can run in parallel
- Unit tests T030-T035 can run in parallel
- E2E tests T036-T038 can run in parallel

**User Story 3**:
- Unit tests T046-T049 can run in parallel

**Polish Phase**:
- All documentation and manual test tasks (T053-T057) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all parallel tasks for US1 together:

# Services (parallel)
Task T012: "Create CSV exporter service in frontend/src/services/export/csvExporter.ts"
Task T013: "Create JSON exporter service in frontend/src/services/export/jsonExporter.ts"

# Components (parallel - after T014 useExport hook is done)
Task T015: "Create ExportButton component in frontend/src/components/export/ExportButton.tsx"
Task T016: "Create ExportFormatDialog component in frontend/src/components/export/ExportFormatDialog.tsx"

# E2E Tests (parallel - after integration complete)
Task T020: "E2E test for CSV export workflow"
Task T021: "E2E test for JSON export workflow"
Task T022: "E2E test for button states"
```

---

## Parallel Example: User Story 2

```bash
# Launch all utilities in parallel:
Task T023: "Create CSV escaper utility"
Task T024: "Create format detector utility"
Task T025: "Add formula injection prevention"

# Launch all unit tests in parallel (after utilities complete):
Task T030: "Unit test CSV escaper with commas"
Task T031: "Unit test CSV escaper with quotes"
Task T032: "Unit test CSV escaper with newlines"
Task T033: "Unit test formula injection prevention"
Task T034: "Unit test JSON type preservation"
Task T035: "Unit test NULL handling"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Minimum Viable Product Path**:
1. ✅ Complete Phase 1: Setup (install dependencies, create folders)
2. ✅ Complete Phase 2: Foundational (core types and utilities)
3. ✅ Complete Phase 3: User Story 1 (basic export with CSV/JSON)
4. **STOP and VALIDATE**: Test export works end-to-end
5. **DEMO READY**: Users can export query results!

**Deliverable**: Basic export functionality with:
- Export button on results tab
- Format selection (CSV/JSON)
- File download with suggested filename
- UTF-8 encoding
- Success/error notifications

**Estimated Time**: ~12-16 tasks (Phase 1 + Phase 2 + Phase 3)

### Incremental Delivery

**Iteration 1: MVP (P1 only)**
- Phases 1-3 → Basic export works → Deploy ✅

**Iteration 2: Add Special Character Handling (P2)**
- Phase 4 → Special chars and types handled → Deploy ✅

**Iteration 3: Add Large Dataset Support (P3)**
- Phase 5 → Large exports optimized → Deploy ✅

**Iteration 4: Polish**
- Phase 6 → Production-ready → Final Deploy ✅

Each iteration is independently deployable and adds value!

### Parallel Team Strategy

**With 2-3 developers after Foundation (Phase 2) completes**:

- **Developer A**: User Story 1 (P1) - Core export
- **Developer B**: User Story 2 (P2) - Format optimization
- **Developer C**: User Story 3 (P3) - Large datasets

All stories complete and integrate independently without conflicts.

---

## Validation Checkpoints

### After Phase 1 (Setup)
- ✅ Dependencies installed (verify package.json updated)
- ✅ Folder structure created (verify all folders exist)
- ✅ Type definitions copied (verify export.ts exists)

### After Phase 2 (Foundational)
- ✅ Core utilities compile without errors
- ✅ Type definitions imported successfully
- ✅ Filename generator produces valid filenames
- ✅ File download helper works with sample data

### After Phase 3 (US1 - MVP)
- ✅ Export button visible on results tab
- ✅ Format dialog shows CSV/JSON options
- ✅ CSV export downloads file
- ✅ JSON export downloads file
- ✅ File opens correctly in Excel/text editor
- ✅ Success notification appears
- ✅ **INDEPENDENT TEST PASSED**: User can complete full export workflow

### After Phase 4 (US2 - Format Optimization)
- ✅ Query with commas in text exports correctly
- ✅ Query with quotes exports correctly
- ✅ Query with Unicode exports correctly
- ✅ Formula injection prevented (=, +, -, @ prefixed)
- ✅ JSON preserves types (numbers, booleans, nulls)
- ✅ CSV opens in Excel without corruption
- ✅ **INDEPENDENT TEST PASSED**: Complex data exports correctly

### After Phase 5 (US3 - Large Datasets)
- ✅ 10,000 row export completes in <30 seconds
- ✅ Progress indicator shows for large exports
- ✅ Export can be cancelled mid-operation
- ✅ Browser remains responsive during export
- ✅ Warning shown for >100,000 rows
- ✅ **INDEPENDENT TEST PASSED**: Large exports work efficiently

### After Phase 6 (Polish)
- ✅ All E2E tests pass
- ✅ All unit tests pass
- ✅ Browser compatibility verified
- ✅ Documentation complete
- ✅ Code review passed

---

## Task Summary

**Total Tasks**: 61

**By Phase**:
- Phase 1 (Setup): 7 tasks
- Phase 2 (Foundational): 4 tasks
- Phase 3 (US1 - P1): 11 tasks (9 implementation + 2 E2E tests)
- Phase 4 (US2 - P2): 16 tasks (7 implementation + 6 unit tests + 3 E2E tests)
- Phase 5 (US3 - P3): 14 tasks (7 implementation + 4 unit tests + 3 E2E tests)
- Phase 6 (Polish): 9 tasks

**By User Story**:
- User Story 1 (MVP): 11 tasks - Basic export functionality
- User Story 2: 16 tasks - Automatic format handling
- User Story 3: 14 tasks - Large dataset optimization

**Parallel Opportunities**:
- Phase 1: 6 out of 7 tasks can run in parallel
- Phase 2: 3 out of 4 tasks can run in parallel
- User Story 1: 6 tasks can run in parallel (services, components, tests)
- User Story 2: 9 tasks can run in parallel (utilities, unit tests)
- User Story 3: 4 tasks can run in parallel (unit tests)
- Polish: 5 tasks can run in parallel

**MVP Scope** (Recommended first delivery):
- Complete Phases 1-3 only (22 tasks)
- Delivers working export functionality
- Can deploy and gather feedback before implementing P2/P3

---

## Notes

- **[P] tasks**: Different files, no dependencies - safe to run in parallel
- **[Story] labels**: Map tasks to specific user stories for traceability
- **Each user story**: Independently completable and testable
- **File paths**: Exact paths provided for clarity
- **Tests included**: Full test coverage with unit and E2E tests
- **MVP-first**: Can stop after Phase 3 and have working feature
- **Incremental**: Each phase adds value without breaking previous work

---

**Status**: ✅ Tasks generated - Ready for implementation with `/speckit.implement`
