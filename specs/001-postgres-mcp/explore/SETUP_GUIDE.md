# Setup Guide for SQL Security Validator

This guide walks you through setting up and testing the SQL security validator.

---

## Prerequisites

- Python 3.11+
- UV package manager (or pip)

---

## Installation Steps

### Step 1: Install SQLGlot

```bash
# Navigate to project directory
cd ~/Documents/VibeCoding/Week5

# Install SQLGlot using UV (recommended)
uv pip install "sqlglot>=25.29"

# Or using pip
pip install "sqlglot>=25.29"
```

### Step 2: Verify Installation

```bash
# Test the validator
python sql_validator.py
```

**Expected Output**: You should see a test suite running with multiple test cases showing which queries are allowed and which are blocked.

Example output:
```
======================================================================
SQL SECURITY VALIDATION TEST SUITE
======================================================================

✓ PASS
SQL: SELECT * FROM users
Result: Valid=True (Expected=True)

✓ PASS
SQL: SELECT id, name FROM users WHERE active = true
Result: Valid=True (Expected=True)

✗ FAIL
SQL: INSERT INTO users (name) VALUES ('hacker')
Result: Valid=False (Expected=False)
Error Type: FORBIDDEN_STATEMENT
Message: Statement type not allowed: Insert. Only SELECT queries are permitted.

...

======================================================================
SUMMARY: 25 passed, 0 failed
======================================================================
```

---

## Step 3: Run Tests

```bash
# Install test dependencies
uv pip install pytest pytest-cov

# Run the comprehensive test suite
pytest test_sql_validator.py -v

# Run with coverage report
pytest test_sql_validator.py -v --cov=sql_validator --cov-report=html --cov-report=term
```

**Expected Result**: All 50+ tests should pass with >95% code coverage.

---

## Step 4: Run Performance Benchmark

```bash
python benchmark_sql_validator.py
```

**Expected Output**: Performance statistics showing validation times for different query types.

Example output:
```
================================================================================
SQL SECURITY VALIDATOR PERFORMANCE BENCHMARK
================================================================================

Simple SELECT
--------------------------------------------------------------------------------
Query: SELECT * FROM users
Query length: 21 characters

Timing (1000 iterations):
  Mean:   1.234 ms
  Median: 1.189 ms
  Min:    0.987 ms
  Max:    3.456 ms
  Std:    0.234 ms
  P95:    1.567 ms
  P99:    2.123 ms

Theoretical throughput: 810 queries/second

...

================================================================================
SUMMARY
================================================================================

Validation time by query complexity:
Query Type                               Mean (ms)    P95 (ms)     QPS
--------------------------------------------------------------------------------
Simple SELECT                            1.234        1.567        810
SELECT with WHERE                        1.456        1.789        687
SELECT with JOIN                         2.345        2.890        426
...

================================================================================
OVERALL STATISTICS
================================================================================
Average mean validation time: 3.456 ms
Median mean validation time: 2.123 ms
Average throughput: 289 queries/second

================================================================================
PERFORMANCE ASSESSMENT
================================================================================
✓ EXCELLENT: Validation time < 5ms
  Suitable for high-throughput APIs (>1000 QPS)
```

---

## Step 5: Try the FastAPI Integration (Optional)

```bash
# Install FastAPI dependencies
uv pip install fastapi uvicorn pydantic

# Run the example server
python integration_example.py
```

The server will start on http://localhost:8000

### Test with curl

**Valid query (allowed)**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users WHERE active = true"}'
```

Expected response:
```json
{
  "data": [
    {"id": 1, "name": "User 1", "active": true},
    {"id": 2, "name": "User 2", "active": true}
  ],
  "row_count": 2,
  "execution_time_ms": 5.2
}
```

**Invalid query (blocked)**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "DELETE FROM users WHERE id = 1"}'
```

Expected response (HTTP 400):
```json
{
  "error": "Query validation failed",
  "message": "Statement type not allowed: Delete. Only SELECT queries are permitted.",
  "error_type": "FORBIDDEN_STATEMENT",
  "dangerous_elements": null,
  "timestamp": "2026-01-28T12:34:56.789012"
}
```

**View security metrics**:
```bash
curl http://localhost:8000/metrics
```

Expected response:
```json
{
  "total_validations": 42,
  "validated_queries": 30,
  "blocked_queries": 12,
  "validation_errors": 0,
  "blocked_by_type": {
    "FORBIDDEN_STATEMENT": 8,
    "DANGEROUS_FUNCTION": 3,
    "FORBIDDEN_OPERATION": 1
  }
}
```

---

## Quick Usage Example

Create a test file `test_usage.py`:

```python
from sql_validator import SQLValidator

# Initialize validator
validator = SQLValidator(dialect="postgres")

# Test some queries
queries = [
    "SELECT * FROM users",
    "INSERT INTO users (name) VALUES ('hacker')",
    "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)",
    "DELETE FROM users",
    "SELECT pg_read_file('/etc/passwd')",
]

print("Testing SQL Validator")
print("=" * 60)

for sql in queries:
    result = validator.validate(sql)
    status = "✓ ALLOWED" if result.is_valid else "✗ BLOCKED"
    print(f"\n{status}")
    print(f"SQL: {sql}")
    if not result.is_valid:
        print(f"Reason: {result.error_message}")
```

Run it:
```bash
python test_usage.py
```

---

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'sqlglot'

**Solution**: Install SQLGlot
```bash
uv pip install "sqlglot>=25.29"
```

### Issue: ImportError about Python version

**Solution**: Ensure you're using Python 3.11+
```bash
python3 --version  # Should be 3.11 or higher
```

### Issue: Tests fail to import pytest

**Solution**: Install pytest
```bash
uv pip install pytest pytest-cov
```

### Issue: FastAPI example fails to start

**Solution**: Install FastAPI dependencies
```bash
uv pip install fastapi uvicorn pydantic
```

---

## Next Steps

1. **Review the research document**: Read `sqlglot_security_research.md` for detailed information about:
   - SQLGlot AST architecture
   - Security validation strategies
   - PostgreSQL dangerous functions
   - Performance optimization techniques

2. **Customize for your project**:
   - Add project-specific dangerous functions to the blacklist
   - Adjust forbidden expression types if needed
   - Implement caching if you have repetitive query patterns

3. **Integration**:
   - Review `integration_example.py` for FastAPI integration patterns
   - Adapt the validator to your existing application
   - Set up logging and monitoring for blocked queries

4. **Testing**:
   - Run the full test suite: `pytest test_sql_validator.py -v --cov`
   - Add project-specific test cases
   - Run performance benchmarks with your typical queries

---

## File Structure

```
Week5/
├── README.md                          # Main documentation
├── SETUP_GUIDE.md                     # This file
├── sqlglot_security_research.md       # Detailed research document
├── sql_validator.py                   # Core validator implementation
├── test_sql_validator.py              # Comprehensive test suite (50+ tests)
├── benchmark_sql_validator.py         # Performance benchmarking
└── integration_example.py             # FastAPI integration example
```

---

## Getting Help

1. **Read the documentation**:
   - `README.md` - Overview and quick start
   - `sqlglot_security_research.md` - Detailed technical documentation
   - `integration_example.py` - Production integration patterns

2. **Run the examples**:
   - `python sql_validator.py` - See basic validation in action
   - `python benchmark_sql_validator.py` - Check performance
   - `pytest test_sql_validator.py -v` - See comprehensive test cases

3. **Check the test suite**:
   - `test_sql_validator.py` contains 50+ examples of valid and invalid queries
   - Each test is well-documented and shows expected behavior

---

## Production Deployment Checklist

Before deploying to production:

- [ ] Install SQLGlot: `uv pip install "sqlglot>=25.29"`
- [ ] Run all tests: `pytest test_sql_validator.py -v`
- [ ] Run benchmarks with your typical query workload
- [ ] Customize dangerous function list for your PostgreSQL version
- [ ] Implement logging for blocked queries
- [ ] Set up monitoring and alerting
- [ ] Configure query size limits (e.g., 50KB max)
- [ ] Consider LRU caching for high-traffic applications
- [ ] Test with your specific PostgreSQL version and extensions
- [ ] Document allowed SQL patterns for your API users
- [ ] Implement rate limiting to prevent DoS attacks

---

**Ready to start?** Run `uv pip install "sqlglot>=25.29"` and then `python sql_validator.py`!
