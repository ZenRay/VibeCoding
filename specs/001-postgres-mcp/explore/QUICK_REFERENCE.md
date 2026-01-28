# SQL Security Validator - Quick Reference

Fast reference guide for common tasks and patterns.

---

## Installation

```bash
uv pip install "sqlglot>=25.29"
```

---

## Basic Usage

```python
from sql_validator import SQLValidator

validator = SQLValidator(dialect="postgres")
result = validator.validate("SELECT * FROM users")

if result.is_valid:
    # Execute query
    pass
else:
    # Block query
    print(f"Blocked: {result.error_message}")
```

---

## ValidationResult Fields

| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | bool | True if query passed validation |
| `error_message` | str \| None | Human-readable error description |
| `error_type` | str \| None | Error category (SYNTAX_ERROR, FORBIDDEN_STATEMENT, etc.) |
| `dangerous_elements` | list[str] \| None | List of specific violations found |

---

## Error Types

| Error Type | Meaning | Example |
|------------|---------|---------|
| `SYNTAX_ERROR` | Invalid SQL syntax | `SELECT FROM WHERE` |
| `FORBIDDEN_STATEMENT` | Root statement not allowed | `DELETE FROM users` |
| `FORBIDDEN_OPERATION` | Forbidden op in nested query | `SELECT * FROM (INSERT ...)` |
| `DANGEROUS_FUNCTION` | Dangerous function call | `SELECT pg_read_file(...)` |
| `PARSE_ERROR` | Failed to parse SQL | Malformed query |

---

## Blocked Operations

### DML (Data Manipulation)
- `INSERT` - Insert new rows
- `UPDATE` - Modify existing rows
- `DELETE` - Remove rows
- `MERGE` - Conditional insert/update

### DDL (Data Definition)
- `CREATE` - Create tables/indexes
- `ALTER` - Modify schema
- `DROP` - Remove tables/indexes
- `TRUNCATE` - Remove all rows

### Commands
- `COPY` - Copy data (can execute programs)
- `LOAD` - Load extensions
- `SET` - Set configuration
- `USE` - Switch database

---

## Dangerous Functions (PostgreSQL)

### File System Access
- `pg_read_file()` - Read files from server
- `pg_read_binary_file()` - Read binary files
- `pg_ls_dir()` - List directory contents
- `pg_stat_file()` - Get file statistics

### Administrative
- `pg_terminate_backend()` - Kill database connections
- `pg_cancel_backend()` - Cancel queries
- `pg_reload_conf()` - Reload configuration
- `pg_rotate_logfile()` - Rotate log files

### Untrusted Languages
- `plpython3u` - Untrusted Python
- `plperlu` - Untrusted Perl

---

## Common Patterns

### Pattern: Basic Validation

```python
validator = SQLValidator(dialect="postgres")
result = validator.validate(sql)

if not result.is_valid:
    raise ValueError(result.error_message)

# Execute safe query
execute_query(sql)
```

### Pattern: With Logging

```python
import logging

logger = logging.getLogger(__name__)
validator = SQLValidator(dialect="postgres")

result = validator.validate(sql)

if not result.is_valid:
    logger.warning(
        "Blocked unsafe SQL",
        extra={
            "error_type": result.error_type,
            "dangerous_elements": result.dangerous_elements,
        }
    )
    raise ValueError(result.error_message)
```

### Pattern: With Caching

```python
from functools import lru_cache

class CachedValidator(SQLValidator):
    @lru_cache(maxsize=1000)
    def validate(self, sql: str, strip_comments: bool = True):
        return super().validate(sql, strip_comments)

validator = CachedValidator(dialect="postgres")
```

### Pattern: Custom Dangerous Functions

```python
class CustomValidator(SQLValidator):
    DANGEROUS_FUNCTIONS = SQLValidator.DANGEROUS_FUNCTIONS | {
        "my_dangerous_func",
        "another_risky_func",
    }

validator = CustomValidator(dialect="postgres")
```

---

## FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from sql_validator import SQLValidator

app = FastAPI()
validator = SQLValidator(dialect="postgres")

@app.post("/query")
async def execute_query(sql: str):
    result = validator.validate(sql)

    if not result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": result.error_message,
                "type": result.error_type,
            }
        )

    # Execute safe query
    return await db.execute(sql)
```

---

## Testing Commands

```bash
# Run basic demo
python sql_validator.py

# Run test suite
pytest test_sql_validator.py -v

# Run with coverage
pytest test_sql_validator.py --cov=sql_validator --cov-report=html

# Run benchmarks
python benchmark_sql_validator.py

# Run FastAPI example
python integration_example.py
```

---

## Performance Characteristics

| Query Type | Validation Time | Throughput |
|------------|-----------------|------------|
| Simple SELECT | 1-2 ms | 500-1000 QPS |
| Complex JOIN | 3-5 ms | 200-300 QPS |
| Large CTE | 5-10 ms | 100-200 QPS |
| Very large | 10-20 ms | 50-100 QPS |

**Optimization**: Use LRU caching for repeated queries (10-100x speedup)

---

## Customization Examples

### Add Custom Forbidden Type

```python
from sqlglot import exp

class CustomValidator(SQLValidator):
    FORBIDDEN_TYPES = SQLValidator.FORBIDDEN_TYPES + (
        exp.Prepare,  # Block PREPARE
        exp.Execute,  # Block EXECUTE
    )
```

### Allow-list Functions (Stricter)

```python
class StrictValidator(SQLValidator):
    ALLOWED_FUNCTIONS = frozenset({
        "count", "sum", "avg", "max", "min",
        "upper", "lower", "trim",
    })

    def _find_dangerous_functions(self, parsed):
        dangerous = []
        for node in parsed.walk():
            if isinstance(node, (exp.Anonymous, exp.Func)):
                func_name = self._get_func_name(node).lower()
                if func_name not in self.ALLOWED_FUNCTIONS:
                    dangerous.append(func_name)
        return dangerous
```

---

## Troubleshooting

### Issue: SQLGlot not installed
**Solution**: `uv pip install "sqlglot>=25.29"`

### Issue: Valid queries blocked
**Possible causes**:
- Comments not being stripped correctly
- Dialect-specific syntax
- Function in dangerous list

**Solution**:
```python
# Try with explicit comment stripping
result = validator.validate(sql, strip_comments=True)

# Check which function is flagged
print(result.dangerous_elements)

# Customize dangerous function list if needed
```

### Issue: Performance too slow
**Solution**: Implement caching
```python
from functools import lru_cache

class CachedValidator(SQLValidator):
    @lru_cache(maxsize=1000)
    def validate(self, sql: str, strip_comments: bool = True):
        return super().validate(sql, strip_comments)
```

---

## Example Queries

### ✅ ALLOWED

```sql
-- Simple SELECT
SELECT * FROM users

-- With WHERE clause
SELECT id, name FROM users WHERE active = true

-- With JOINs
SELECT u.id, o.order_id
FROM users u
INNER JOIN orders o ON u.id = o.user_id

-- With subquery
SELECT * FROM users
WHERE id IN (SELECT user_id FROM orders)

-- With CTE
WITH active_users AS (
    SELECT id FROM users WHERE active = true
)
SELECT * FROM active_users

-- Aggregates
SELECT category, COUNT(*) FROM products GROUP BY category

-- Window functions
SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) FROM users

-- Set operations
SELECT id FROM customers UNION SELECT id FROM suppliers
```

### ❌ BLOCKED

```sql
-- DML operations
INSERT INTO users (name) VALUES ('hacker')
UPDATE users SET admin = true
DELETE FROM users WHERE id = 1

-- DDL operations
CREATE TABLE evil (data text)
DROP TABLE users
ALTER TABLE users ADD COLUMN evil text
TRUNCATE TABLE users

-- Dangerous functions
SELECT pg_read_file('/etc/passwd')
SELECT pg_terminate_backend(123)
SELECT pg_ls_dir('/etc')

-- Nested attacks
SELECT * FROM (INSERT INTO logs VALUES ('x') RETURNING *)
WITH cte AS (DELETE FROM users RETURNING *) SELECT * FROM cte
```

---

## File Structure

```
Week5/
├── README.md                          # Main documentation
├── QUICK_REFERENCE.md                 # This file
├── SETUP_GUIDE.md                     # Installation guide
├── ARCHITECTURE.md                    # Architecture overview
├── sqlglot_security_research.md       # Detailed research
├── sql_validator.py                   # Core implementation
├── test_sql_validator.py              # Test suite
├── benchmark_sql_validator.py         # Performance tests
└── integration_example.py             # FastAPI example
```

---

## Key Takeaways

1. **Always validate**: Never execute user SQL without validation
2. **Use caching**: LRU cache dramatically improves performance for repeated queries
3. **Log blocked queries**: Security monitoring is essential
4. **Test thoroughly**: Run the test suite before deploying
5. **Customize carefully**: Only add to dangerous functions list if you understand the risk
6. **Monitor performance**: Set up alerts for slow validation

---

## Resources

- **Detailed documentation**: `README.md`
- **Research paper**: `sqlglot_security_research.md`
- **Architecture diagram**: `ARCHITECTURE.md`
- **Setup instructions**: `SETUP_GUIDE.md`
- **Test examples**: `test_sql_validator.py`
- **FastAPI integration**: `integration_example.py`

---

**Quick Start**: `uv pip install "sqlglot>=25.29"` → `python sql_validator.py`
