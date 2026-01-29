# Research Summary: Query Templates & JSONL Logging

**Date**: 2026-01-28
**Status**: Complete
**Full Research**: [query_template_and_logging_research.md](./query_template_and_logging_research.md)

---

## Quick Reference

### 1. Query Template Library

**Purpose**: Provide fallback when OpenAI API fails, covering 20% of common queries (SC-006)

#### Key Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Format** | YAML | Human-readable, easy to maintain, supports comments |
| **Template Count** | 15 templates | Covers basic SELECT, COUNT, GROUP BY, JOIN, ORDER BY patterns |
| **Matching Algorithm** | Multi-stage scoring (keyword + entity + priority + context) | Balances accuracy and performance |
| **Performance Target** | <100ms | Ensures responsive user experience |
| **Parameter Validation** | Type system with regex patterns | Prevents SQL injection |

#### Template Categories

1. **Basic SELECT** (6 templates): select_all, select_with_condition, select_columns, select_order_by, select_recent, select_distinct
2. **Aggregate** (4 templates): count_all, count_with_condition, select_group_by, select_aggregate_stats
3. **Advanced** (5 templates): select_join_inner, select_between, select_like, select_null_check, select_in_list

#### Matching Score Components

- Keyword matching: 40 points max
- Entity extraction: 30 points max
- Template priority: 20 points max
- Context relevance: 10 points max
- **Threshold**: 40 points minimum

#### Parameter Types

- `identifier`: Table/column names (validated with regex)
- `column_list`: Comma-separated columns
- `expression`: WHERE conditions (operator whitelist)
- `keyword`: SQL keywords (enum validation)
- `value`, `value_list`, `string`, `integer`: Literals

---

### 2. JSONL Logging System

**Purpose**: Record query history for analysis, debugging, and compliance (NFR-010: 30-day retention)

#### Key Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Format** | JSONL (JSON Lines) | One JSON object per line, jq-friendly, streamable |
| **Write Strategy** | Async buffered (5s interval) | <1ms overhead, 10K+ writes/sec throughput |
| **Rotation** | Daily at midnight UTC | Predictable filenames, manageable file sizes |
| **Retention** | 30 days automatic cleanup | Meets NFR-010, prevents disk full |
| **File Naming** | `YYYY-MM-DD.jsonl` | Sortable, parseable, standard format |

#### Log Entry Schema

**Required Fields**:
- `timestamp`: ISO 8601 UTC (e.g., `2026-01-28T10:30:00.123Z`)
- `request_id`: UUID v4
- `natural_language`: User input (max 1000 chars)
- `sql`: Generated/manual SQL (max 10000 chars)
- `status`: `success` | `validation_error` | `execution_error` | `timeout` | `cancelled`

**Optional Fields**:
- `database`, `user_id`, `sql_source` (`manual` | `openai` | `template`)
- `template_id`, `execution_time_ms`, `row_count`
- `error_message`, `error_type`, `metadata`

#### Performance Characteristics

| Write Strategy | Throughput | Latency | Durability |
|----------------|-----------|---------|------------|
| Immediate fsync | ~100/sec | 5-10ms | Highest |
| **Buffered (5s)** | **~10K/sec** | **<1ms** | **High** (recommended) |
| Buffered (60s) | ~50K/sec | <1ms | Medium |

---

## Implementation Checklist

### Template Library

- [ ] Create `templates/postgres.yaml` with 15 templates
- [ ] Implement `TemplateLoader` class (YAML parsing + validation)
- [ ] Implement `TemplateMatcher` class (multi-stage scoring)
- [ ] Implement `TemplateEngine` class (SQL generation)
- [ ] Write unit tests (90%+ coverage)
- [ ] Benchmark matching performance (<100ms requirement)
- [ ] Integrate with `NLQueryService` (OpenAI fallback)
- [ ] Test coverage evaluation (>20% common queries)

### JSONL Logging

- [ ] Implement `QueryLogEntry` dataclass (Pydantic model)
- [ ] Implement `JSONLWriter` class (async buffered writes)
- [ ] Implement rotation logic (daily at midnight UTC)
- [ ] Implement cleanup logic (30-day retention)
- [ ] Add background tasks for periodic flush and cleanup
- [ ] Write unit tests (rotation, cleanup, concurrency)
- [ ] Benchmark write performance (target: <1ms overhead)
- [ ] Create jq query examples documentation
- [ ] Integrate with FastAPI middleware
- [ ] Set up systemd timer for cleanup (production)

---

## Code Files to Create

### Template Library

```
Week5/
├── templates/
│   └── postgres.yaml                    # 15 query templates
├── src/nl_query/
│   ├── template_loader.py              # YAML loading
│   ├── template_matcher.py             # Matching algorithm
│   ├── template_engine.py              # SQL generation
│   └── template_coverage.py            # Coverage analysis
└── tests/
    └── test_templates.py                # Template tests
```

### JSONL Logging

```
Week5/
├── src/logging/
│   ├── jsonl_writer.py                 # Async writer
│   ├── log_models.py                   # QueryLogEntry
│   └── log_middleware.py               # FastAPI middleware
├── tests/
│   └── test_logging.py                 # Logging tests
└── docs/
    └── jq_query_examples.md            # Query cookbook
```

---

## Example Usage

### Query Template

```python
# Load templates
templates = TemplateLoader.load_from_file(Path("templates/postgres.yaml"))
matcher = TemplateMatcher(templates, metadata=db_metadata)

# Match natural language
result = matcher.match("显示所有用户")
# MatchResult(template_id="select_all", score=85, extracted_params={"table_name": "users"})

# Generate SQL
engine = TemplateEngine(templates)
success, sql, error = engine.generate_sql("select_all", {"table_name": "users"})
# (True, "SELECT * FROM users", None)
```

### JSONL Logging

```python
# Initialize writer
writer = JSONLWriter(log_dir=Path("/var/log/db-query-tool"), retention_days=30)
await writer.start()

# Log query
await writer.write(QueryLogEntry(
    timestamp=get_current_timestamp(),
    request_id=generate_request_id(),
    database="production",
    natural_language="显示所有用户",
    sql="SELECT * FROM users LIMIT 1000",
    sql_source="template",
    template_id="select_all",
    status="success",
    execution_time_ms=45.2,
    row_count=234
))

# Query logs with jq
# jq 'select(.status != "success")' 2026-01-28.jsonl
# jq -s 'map(.execution_time_ms // 0) | add / length' 2026-01-28.jsonl
```

---

## Testing Strategy

### Template Library Tests

1. **Template Loading**: Validate YAML structure, required fields
2. **Parameter Validation**: Test regex patterns, type checks, enum validation
3. **Matching Algorithm**: Test keyword matching, entity extraction, scoring
4. **SQL Generation**: Test parameterization, default values, error handling
5. **Coverage**: Test against 100+ natural language examples

### JSONL Logging Tests

1. **Write Operations**: Test single write, batch writes, concurrent writes
2. **Rotation**: Test date change triggers new file
3. **Cleanup**: Test old file deletion (>30 days)
4. **Performance**: Benchmark throughput (>10K writes/sec)
5. **Error Handling**: Test write failures, disk full scenarios

---

## Performance Targets

| Component | Metric | Target | Measurement |
|-----------|--------|--------|-------------|
| Template Matching | Latency | <100ms | `time.perf_counter()` |
| Template Coverage | Success Rate | >20% | Common query test set |
| JSONL Write | Latency | <1ms | Async overhead |
| JSONL Write | Throughput | >10K/sec | Benchmark test |
| Log Rotation | Interruption | 0ms | Atomic file switch |
| Log Cleanup | Frequency | Daily 01:00 UTC | Systemd timer |

---

## Production Deployment

### Environment Variables

```bash
# Template configuration
TEMPLATE_FILE=/etc/db-query-tool/templates/postgres.yaml

# Logging configuration
LOG_DIR=/var/log/db-query-tool
LOG_RETENTION_DAYS=30
LOG_FLUSH_INTERVAL=5.0
LOG_BUFFER_SIZE=100
```

### Systemd Timer

```ini
# /etc/systemd/system/db-query-tool-cleanup.timer
[Unit]
Description=DB Query Tool Log Cleanup Timer

[Timer]
OnCalendar=daily
Unit=db-query-tool-cleanup.service

[Install]
WantedBy=timers.target
```

### Monitoring

```python
# Prometheus metrics
template_match_duration_seconds = Histogram('template_match_duration_seconds', 'Template matching time')
template_match_success_total = Counter('template_match_success_total', 'Successful template matches')
template_match_failure_total = Counter('template_match_failure_total', 'Failed template matches')

query_log_write_duration_seconds = Histogram('query_log_write_duration_seconds', 'Log write time')
query_log_size_bytes = Gauge('query_log_size_bytes', 'Current log file size')
query_log_entries_total = Counter('query_log_entries_total', 'Total log entries written')
```

---

## Next Steps

1. **Review Full Research**: Read [query_template_and_logging_research.md](./query_template_and_logging_research.md)
2. **Create YAML Templates**: Define 15 query templates in `templates/postgres.yaml`
3. **Implement Core Classes**: `TemplateMatcher`, `TemplateEngine`, `JSONLWriter`
4. **Write Tests**: Achieve 90%+ coverage for both components
5. **Benchmark Performance**: Validate <100ms matching, <1ms logging overhead
6. **Integration**: Add to `NLQueryService` and FastAPI middleware
7. **Documentation**: Create jq query cookbook for log analysis

---

**Status**: ✅ Research Complete - Ready for Implementation

**Estimated Implementation Time**:
- Template Library: 8-12 hours
- JSONL Logging: 6-8 hours
- Testing: 6-8 hours
- Total: 20-28 hours

**Dependencies**: None (both components are independent)

**Blockers**: None

---

**Author**: Claude Code
**Date**: 2026-01-28
**Version**: 1.0
