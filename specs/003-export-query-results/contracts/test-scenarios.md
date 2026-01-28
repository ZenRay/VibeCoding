# Test Scenarios: Query Results Export

**Feature**: Query Results Export
**Date**: 2026-01-22
**Purpose**: Comprehensive test scenarios for export functionality

## Test Coverage Matrix

| Category | CSV Tests | JSON Tests | Coverage |
|----------|-----------|------------|----------|
| Standard Data Types | ✅ 8 tests | ✅ 8 tests | 100% |
| Special Characters | ✅ 6 tests | ✅ 4 tests | 100% |
| Edge Cases | ✅ 10 tests | ✅ 8 tests | 100% |
| Large Datasets | ✅ 4 tests | ✅ 4 tests | 100% |
| Error Conditions | ✅ 6 tests | ✅ 6 tests | 100% |
| **Total** | **34 tests** | **30 tests** | **64 total** |

---

## 1. Standard Data Types

### 1.1 CSV: String Values

**Input**:
```typescript
{
  columns: [{ name: 'name', dataType: 'string' }],
  rows: [
    { name: 'John Doe' },
    { name: 'Jane Smith' }
  ]
}
```

**Expected Output**:
```csv
\ufeffname
John Doe
Jane Smith
```

**Validation**:
- ✅ UTF-8 BOM present (`\ufeff`)
- ✅ Header row with column name
- ✅ String values not quoted (no special chars)

---

### 1.2 CSV: Number Values

**Input**:
```typescript
{
  columns: [
    { name: 'id', dataType: 'number' },
    { name: 'price', dataType: 'number' }
  ],
  rows: [
    { id: 1, price: 99.99 },
    { id: 2, price: 149.50 }
  ]
}
```

**Expected Output**:
```csv
\ufeffid,price
1,99.99
2,149.50
```

**Validation**:
- ✅ Numbers not quoted
- ✅ Decimal precision preserved

---

### 1.3 CSV: Boolean Values

**Input**:
```typescript
{
  columns: [{ name: 'active', dataType: 'boolean' }],
  rows: [
    { active: true },
    { active: false }
  ]
}
```

**Expected Output**:
```csv
\ufeffactive
true
false
```

**Validation**:
- ✅ Booleans rendered as `true`/`false`
- ✅ Not quoted

---

### 1.4 CSV: Date Values

**Input**:
```typescript
{
  columns: [{ name: 'created_at', dataType: 'date' }],
  rows: [
    { created_at: new Date('2026-01-22T10:30:00Z') },
    { created_at: new Date('2026-01-23T15:45:00Z') }
  ]
}
```

**Expected Output**:
```csv
\ufeffcreated_at
2026-01-22T10:30:00.000Z
2026-01-23T15:45:00.000Z
```

**Validation**:
- ✅ Dates formatted as ISO 8601
- ✅ Timezone preserved (Z suffix)

---

### 1.5 CSV: NULL Values

**Input**:
```typescript
{
  columns: [{ name: 'notes', dataType: 'string' }],
  rows: [
    { notes: 'Some text' },
    { notes: null },
    { notes: undefined }
  ]
}
```

**Expected Output**:
```csv
\ufeffnotes
Some text


```

**Validation**:
- ✅ NULL rendered as empty field
- ✅ undefined rendered as empty field
- ✅ No quotes around empty fields

---

### 1.6 JSON: String Values

**Input**: Same as 1.1

**Expected Output**:
```json
{
  "metadata": {
    "columns": [{ "name": "name", "dataType": "string" }],
    "exportedAt": "2026-01-22T10:30:00Z",
    "rowCount": 2
  },
  "data": [
    { "name": "John Doe" },
    { "name": "Jane Smith" }
  ]
}
```

**Validation**:
- ✅ Strings quoted
- ✅ Valid JSON structure
- ✅ Metadata included

---

### 1.7 JSON: Number Values

**Input**: Same as 1.2

**Expected Output**:
```json
{
  "data": [
    { "id": 1, "price": 99.99 },
    { "id": 2, "price": 149.50 }
  ]
}
```

**Validation**:
- ✅ Numbers not quoted
- ✅ Decimal precision preserved

---

### 1.8 JSON: Boolean Values

**Input**: Same as 1.3

**Expected Output**:
```json
{
  "data": [
    { "active": true },
    { "active": false }
  ]
}
```

**Validation**:
- ✅ Booleans as JSON true/false
- ✅ Not quoted

---

### 1.9 JSON: NULL Values

**Input**: Same as 1.5

**Expected Output**:
```json
{
  "data": [
    { "notes": "Some text" },
    { "notes": null },
    { "notes": null }
  ]
}
```

**Validation**:
- ✅ NULL as JSON null
- ✅ undefined converted to null

---

## 2. Special Characters

### 2.1 CSV: Comma in Field

**Input**:
```typescript
{
  rows: [{ name: 'Smith, John' }]
}
```

**Expected Output**:
```csv
\ufeffname
"Smith, John"
```

**Validation**:
- ✅ Field with comma enclosed in quotes (RFC 4180)

---

### 2.2 CSV: Double Quote in Field

**Input**:
```typescript
{
  rows: [{ description: 'He said "hello"' }]
}
```

**Expected Output**:
```csv
\ufefdescription
"He said ""hello"""
```

**Validation**:
- ✅ Field with quotes enclosed in quotes
- ✅ Internal quotes doubled (RFC 4180)

---

### 2.3 CSV: Newline in Field

**Input**:
```typescript
{
  rows: [{ address: '123 Main St\nApt 4' }]
}
```

**Expected Output**:
```csv
\ufeffaddress
"123 Main St
Apt 4"
```

**Validation**:
- ✅ Field with newline enclosed in quotes
- ✅ Newline preserved inside quotes

---

### 2.4 CSV: Tab Character

**Input**:
```typescript
{
  rows: [{ data: 'Column1\tColumn2' }]
}
```

**Expected Output**:
```csv
\ufeffdata
"Column1	Column2"
```

**Validation**:
- ✅ Tab character preserved
- ✅ Field quoted

---

### 2.5 CSV: Unicode Characters

**Input**:
```typescript
{
  rows: [
    { name: '张三' },
    { name: 'José García' },
    { name: '日本語' }
  ]
}
```

**Expected Output**:
```csv
\ufeffname
张三
José García
日本語
```

**Validation**:
- ✅ UTF-8 encoding with BOM
- ✅ All Unicode characters preserved
- ✅ Opens correctly in Excel

---

### 2.6 CSV: Formula Injection Prevention

**Input**:
```typescript
{
  rows: [
    { formula: '=SUM(A1:A10)' },
    { formula: '+1+1' },
    { formula: '-1' },
    { formula: '@SUM(A1)' }
  ]
}
```

**Expected Output**:
```csv
\ufeffformula
'=SUM(A1:A10)
'+1+1
'-1
'@SUM(A1)
```

**Validation**:
- ✅ Leading `=`, `+`, `-`, `@` prefixed with single quote
- ✅ Prevents CSV formula injection attacks

---

### 2.7 JSON: Special Characters (No Escaping Needed)

**Input**:
```typescript
{
  rows: [{ text: 'Comma, quote", newline\n, tab\t' }]
}
```

**Expected Output**:
```json
{
  "data": [
    { "text": "Comma, quote\", newline\\n, tab\\t" }
  ]
}
```

**Validation**:
- ✅ JSON escaping automatic (newline as `\\n`)
- ✅ Quotes escaped (`\"`)

---

## 3. Edge Cases

### 3.1 Empty Result Set (0 rows)

**CSV**:
```csv
\ufeffid,name,email
```

**JSON**:
```json
{
  "metadata": { "rowCount": 0, ... },
  "data": []
}
```

**Validation**:
- ✅ CSV has headers only
- ✅ JSON has empty array
- ✅ No errors thrown

---

### 3.2 Single Row

**Input**: 1 row

**Validation**:
- ✅ CSV header + 1 data row
- ✅ JSON array with 1 object
- ✅ Formatted correctly

---

### 3.3 Single Column

**Input**: 1 column, multiple rows

**CSV**:
```csv
\ufeffid
1
2
3
```

**Validation**:
- ✅ Single column CSV valid
- ✅ No trailing commas

---

### 3.4 Wide Result (50+ Columns)

**Input**: 50 columns, 100 rows

**Validation**:
- ✅ All columns included
- ✅ CSV maintains structure
- ✅ JSON objects have all properties
- ✅ Export completes in <2 seconds

---

### 3.5 Long Column Names

**Input**:
```typescript
{
  columns: [{
    name: 'this_is_a_very_long_column_name_that_exceeds_normal_limits',
    dataType: 'string'
  }]
}
```

**Validation**:
- ✅ Column name not truncated
- ✅ Quoted if contains special chars

---

### 3.6 Column Names with Special Characters

**Input**:
```typescript
{
  columns: [
    { name: 'First Name', dataType: 'string' },
    { name: 'Email@Address', dataType: 'string' },
    { name: 'Total ($)', dataType: 'number' }
  ]
}
```

**CSV**:
```csv
\ufeffFirst Name,Email@Address,Total ($)
```

**Validation**:
- ✅ Spaces preserved
- ✅ Special chars allowed in headers

---

### 3.7 Duplicate Column Names

**Input**:
```typescript
{
  columns: [
    { name: 'id', dataType: 'number' },
    { name: 'id', dataType: 'string' }  // duplicate
  ]
}
```

**Validation**:
- ⚠️ Warning issued: "Duplicate column names detected"
- ✅ Export proceeds (column names kept as-is)
- ✅ Data integrity maintained

---

### 3.8 Mixed Data Types in Same Column

**Input**:
```typescript
{
  columns: [{ name: 'value', dataType: 'unknown' }],
  rows: [
    { value: 'text' },
    { value: 123 },
    { value: true },
    { value: null }
  ]
}
```

**CSV**:
```csv
\ufeffvalue
text
123
true

```

**JSON**:
```json
{
  "data": [
    { "value": "text" },
    { "value": 123 },
    { "value": true },
    { "value": null }
  ]
}
```

**Validation**:
- ✅ CSV renders all as strings
- ✅ JSON preserves types

---

## 4. Large Datasets

### 4.1 Exactly 10,000 Rows

**Input**: 10,000 rows, 10 columns

**Validation**:
- ✅ Export completes in <30 seconds
- ✅ File size ~10-15MB
- ✅ Browser remains responsive
- ✅ No memory errors

---

### 4.2 50,000 Rows

**Input**: 50,000 rows, 10 columns

**Validation**:
- ✅ Export completes in <60 seconds
- ✅ Progress indicator shown
- ✅ File size ~50-75MB
- ✅ Browser remains responsive

---

### 4.3 100,000 Rows (Warning Threshold)

**Input**: 100,000 rows

**Validation**:
- ⚠️ Warning displayed: "Large dataset may take time to export"
- ✅ User can proceed or cancel
- ✅ Export completes successfully (if user proceeds)

---

### 4.4 Very Wide (100 columns)

**Input**: 1,000 rows, 100 columns

**Validation**:
- ✅ All columns exported
- ✅ CSV structure maintained
- ✅ JSON objects complete

---

## 5. Error Conditions

### 5.1 User Cancels File Dialog

**Scenario**: User clicks Export → Selects format → Cancels save dialog

**Expected**:
- ✅ Export status: `'cancelled'`
- ✅ No error message
- ✅ No file created
- ✅ UI returns to normal state

---

### 5.2 Invalid Data Format

**Input**:
```typescript
{
  columns: [],  // Empty columns
  rows: [{ data: 'value' }]
}
```

**Expected**:
- ❌ ValidationError: "No columns defined"
- ❌ Export blocked
- ✅ User-friendly error message

---

### 5.3 Browser Memory Limit

**Scenario**: Export dataset larger than available memory

**Expected**:
- ❌ ExportError: `MEMORY_LIMIT_EXCEEDED`
- ✅ Error message: "Dataset too large for browser memory"
- ✅ Suggestion: "Try exporting fewer rows"

---

### 5.4 Permission Denied

**Scenario**: User denies file save permission

**Expected**:
- ❌ ExportError: `PERMISSION_DENIED`
- ✅ Error message explains permission issue
- ✅ Suggestion to check browser settings

---

### 5.5 Network Error (if remote data)

**Scenario**: Network interruption during data fetch (future enhancement)

**Expected**:
- ❌ ExportError: `NETWORK_ERROR`
- ✅ Clear error message
- ✅ Retry option

---

### 5.6 Disk Space Full

**Scenario**: Insufficient disk space for file

**Expected**:
- ❌ ExportError: `DISK_SPACE_FULL`
- ✅ Error message: "Insufficient disk space"
- ✅ Suggestion to free up space

---

## 6. File Compatibility Tests

### 6.1 CSV: Excel Compatibility

**Test**: Export CSV → Open in Microsoft Excel

**Validation**:
- ✅ File opens without errors
- ✅ UTF-8 characters display correctly (Chinese, Arabic, emojis)
- ✅ Columns aligned properly
- ✅ No corrupted data

---

### 6.2 CSV: Google Sheets Compatibility

**Test**: Export CSV → Import to Google Sheets

**Validation**:
- ✅ Import succeeds
- ✅ All data visible
- ✅ Data types recognized correctly

---

### 6.3 CSV: LibreOffice Calc Compatibility

**Test**: Export CSV → Open in LibreOffice Calc

**Validation**:
- ✅ File opens correctly
- ✅ UTF-8 BOM handled
- ✅ Data integrity maintained

---

### 6.4 JSON: Parser Compatibility

**Test**: Export JSON → Parse with `JSON.parse()`

**Validation**:
- ✅ Valid JSON structure
- ✅ No syntax errors
- ✅ Data types correct

---

### 6.5 JSON: jq Compatibility

**Test**: Export JSON → Process with `jq` command-line tool

**Validation**:
- ✅ `jq` can parse file
- ✅ Queries work (`jq '.data[]'`)
- ✅ No formatting issues

---

## 7. Browser Compatibility Tests

### 7.1 Chrome/Edge

**Validation**:
- ✅ Export works
- ✅ File downloads to default location
- ✅ Performance: <30s for 10k rows

---

### 7.2 Firefox

**Validation**:
- ✅ Export works
- ✅ File downloads correctly
- ✅ Performance comparable to Chrome

---

### 7.3 Safari (macOS/iOS)

**Validation**:
- ✅ Export works
- ✅ File downloads (may need user confirmation)
- ✅ UTF-8 BOM handled correctly

---

### 7.4 Mobile Safari (iOS)

**Validation**:
- ✅ Export works on mobile
- ✅ File save dialog appears
- ✅ Performance acceptable on iPhone

---

## 8. UI/UX Tests

### 8.1 Export Button Visibility

**Validation**:
- ✅ Button visible when results present
- ✅ Button disabled when no results
- ✅ Button disabled during query execution

---

### 8.2 Format Selection Dialog

**Validation**:
- ✅ Modal opens on button click
- ✅ CSV and JSON options displayed
- ✅ Descriptions visible
- ✅ User can select format and proceed

---

### 8.3 Progress Indicator

**Validation**:
- ✅ Shown for exports >2 seconds
- ✅ Percentage updates correctly
- ✅ Can be cancelled mid-export

---

### 8.4 Success Notification

**Validation**:
- ✅ Notification shown on success
- ✅ Includes filename and row count
- ✅ Includes file size

---

### 8.5 Error Notification

**Validation**:
- ✅ Clear error message displayed
- ✅ Actionable suggestions provided
- ✅ User can dismiss and retry

---

## Test Execution Checklist

### Unit Tests (Required)
- [ ] CSV escaper (special characters, quotes, commas, newlines)
- [ ] JSON formatter (type preservation, metadata)
- [ ] Filename generator (sanitization, timestamps)
- [ ] Format detector (delimiters, special chars)
- [ ] Type converter (dates, nulls, booleans)

### Integration Tests (Required)
- [ ] Export button integration with query results
- [ ] Format selection dialog workflow
- [ ] File download trigger
- [ ] Progress tracking
- [ ] Error handling

### E2E Tests (Required with Playwright)
- [ ] Complete export workflow (query → export → download)
- [ ] CSV export with special characters
- [ ] JSON export with metadata
- [ ] Large dataset export (10,000 rows)
- [ ] User cancellation
- [ ] Error scenarios

### Manual Tests (Recommended)
- [ ] Excel compatibility (open CSV files)
- [ ] Google Sheets compatibility
- [ ] Browser compatibility (Chrome, Firefox, Safari, Edge)
- [ ] Mobile device testing (iOS Safari, Chrome Mobile)
- [ ] File size verification
- [ ] Performance benchmarks

---

**Total Test Scenarios**: 64
**Priority P1 (Must Pass)**: 40
**Priority P2 (Should Pass)**: 16
**Priority P3 (Nice to Have)**: 8
