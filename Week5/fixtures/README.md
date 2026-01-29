# PostgreSQL MCP Test Databases

This directory contains three test databases of varying complexity for testing the PostgreSQL MCP server.

## Database Overview

**Architecture**: Single PostgreSQL server with three databases

| Database | Name | Port | Tables | Records | Purpose |
|----------|------|------|--------|---------|---------|
| **Small** | `ecommerce_small` | 5432 | 5 | ~1,000 | E-commerce with products, orders, customers |
| **Medium** | `social_medium` | 5432 | 14 | ~10,000 | Social media platform with users, posts, comments |
| **Large** | `erp_large` | 5432 | 11 | ~50,000+ | Enterprise ERP with HR, Finance, Inventory, CRM |

**Note**: All three databases run on the same PostgreSQL server (localhost:5432), not separate servers.

## Quick Start

### 1. Generate Sample Data

```bash
cd ~/Documents/VibeCoding/Week5
make generate-data
```

### 2. Start Databases

```bash
make up
```

This will:
- Start all three PostgreSQL containers
- Initialize schemas
- Load sample data
- Run health checks

### 3. Test Connections

```bash
make test-all
```

## Database Details

### Small Database (ecommerce_small)

**Schema:**
- `customers` - Customer information
- `products` - Product catalog with categories
- `orders` - Sales orders
- `order_items` - Order line items
- `reviews` - Product reviews

**Features:**
- Basic relationships (1:N, N:M)
- Indexes on common query fields
- 2 views: `product_stats`, `customer_order_summary`
- 2 custom types: `order_status`, `payment_method`

**Connection:**
```bash
psql -h localhost -p 5432 -U testuser -d ecommerce_small
# Password: testpass123
```

### Medium Database (social_medium)

**Schema:**
- `users` - User profiles
- `posts` - User posts with content types
- `comments` - Hierarchical comments
- `reactions` - Polymorphic reactions (posts/comments)
- `follows` - User relationships
- `messages` - Direct messages
- `notifications` - User notifications
- `hashtags` - Hashtag system
- `groups` - User groups
- `group_members` - Group membership
- And more...

**Features:**
- Complex relationships (hierarchical, polymorphic)
- JSONB fields for metadata
- GIN indexes for full-text search
- 2 views: `user_stats`, `trending_posts`
- 4 custom types

**Connection:**
```bash
psql -h localhost -p 5432 -U testuser -d social_medium
# Password: testpass123
```

### Large Database (erp_large)

**Schema (30+ tables):**

**HR Module:**
- `departments`, `employees`, `attendance`, `leave_requests`

**Finance Module:**
- `chart_of_accounts`, `journal_entries`, `journal_lines`, `budgets`

**Inventory Module:**
- `warehouses`, `products`, `product_categories`, `inventory`, `stock_movements`

**CRM Module:**
- `customers`, `leads`, `opportunities`

**Sales Module:**
- `sales_orders`, `order_lines`, `invoices`, `payments`

**Purchasing Module:**
- `suppliers`, `purchase_orders`, `po_lines`

**Features:**
- Extensive foreign key relationships
- Hierarchical structures (departments, categories)
- Multiple indexes per table
- 5+ views for reporting
- 10+ custom ENUM types
- Generated columns (computed fields)

**Connection:**
```bash
psql -h localhost -p 5432 -U testuser -d erp_large
# Password: testpass123
```

## Makefile Commands

```bash
make help          # Show all available commands
make up            # Start all databases
make down          # Stop all databases
make clean         # Remove all data and volumes
make rebuild       # Clean and rebuild from scratch
make generate-data # Generate sample data
make test-small    # Test small database
make test-medium   # Test medium database
make test-large    # Test large database
make test-all      # Test all databases
make logs          # Show database logs
make stats         # Show database statistics
```

## Environment Configuration

For integration tests, set these environment variables:

```bash
# Small database
export TEST_DB_SMALL_HOST=localhost
export TEST_DB_SMALL_PORT=5432
export TEST_DB_SMALL_NAME=ecommerce_small
export TEST_DB_SMALL_USER=testuser
export TEST_DB_SMALL_PASSWORD=testpass123

# Medium database
export TEST_DB_MEDIUM_HOST=localhost
export TEST_DB_MEDIUM_PORT=5432
export TEST_DB_MEDIUM_NAME=social_medium
export TEST_DB_MEDIUM_USER=testuser
export TEST_DB_MEDIUM_PASSWORD=testpass123

# Large database
export TEST_DB_LARGE_HOST=localhost
export TEST_DB_LARGE_PORT=5432
export TEST_DB_LARGE_NAME=erp_large
export TEST_DB_LARGE_USER=testuser
export TEST_DB_LARGE_PASSWORD=testpass123
```

## Test Scenarios

### Small Database - Ideal For:
- Basic SQL generation testing
- Simple JOIN queries (2-3 tables)
- Basic aggregations (COUNT, SUM, AVG)
- Order by and LIMIT clauses
- Simple WHERE conditions

### Medium Database - Ideal For:
- Complex JOINs (4+ tables)
- Hierarchical queries (recursive CTEs)
- Full-text search with JSONB
- Polymorphic relationships
- Privacy/permission filters
- Social graph queries

### Large Database - Ideal For:
- Multi-module queries (cross-functional)
- Complex business logic
- Large schema with 30+ tables
- Performance testing
- Query optimization
- Enterprise reporting queries

## Docker Compose Services

The `docker-compose.yml` defines a single PostgreSQL 15 server with three databases:
- Single container (`mcp-test-db`)
- Health checks (5s interval)
- Persistent volume for all databases
- Init scripts auto-loaded from init/ directory
- Isolated network

## Data Generation

Each database has a Python script (`generate_data.py`) that creates realistic sample data:

```python
# Example: Generate small database data
cd fixtures/small
python3 generate_data.py
```

Generated files:
- `02_data_customers.sql` - Customer records
- `03_data_products.sql` - Product catalog
- `04_data_orders.sql` - Orders and order items
- `05_data_reviews.sql` - Product reviews

## Troubleshooting

### Databases not starting
```bash
# Check container logs
make logs

# Restart containers
make down
make up
```

### Port conflicts
Edit `fixtures/docker-compose.yml` to change port mappings:
```yaml
ports:
  - "5432:5432"  # Change first number to available port
```

### Data regeneration
```bash
# Clean all data and regenerate
make rebuild
```

### Permission errors
```bash
# Ensure script is executable
chmod +x fixtures/*/generate_data.py
```

## Integration with MCP Server

Update `Week5/config/config.yaml`:

```yaml
databases:
  - name: "small"
    host: "localhost"
    port: 5432
    database: "ecommerce_small"
    user: "testuser"
    password_env_var: "TEST_DB_SMALL_PASSWORD"
    
  - name: "medium"
    host: "localhost"
    port: 5433
    database: "social_medium"
    user: "testuser"
    password_env_var: "TEST_DB_MEDIUM_PASSWORD"
    
  - name: "large"
    host: "localhost"
    port: 5434
    database: "erp_large"
    user: "testuser"
    password_env_var: "TEST_DB_LARGE_PASSWORD"
```

## Schema Documentation

For detailed schema information:

```bash
# Small database
psql -h localhost -p 5432 -U testuser -d ecommerce_small -c "\d+"

# Medium database
psql -h localhost -p 5433 -U testuser -d social_medium -c "\d+"

# Large database
psql -h localhost -p 5434 -U testuser -d erp_large -c "\d+"
```

## Cleanup

```bash
# Stop and remove everything
make clean

# This will delete all volumes and data
# Re-run `make rebuild` to recreate
```
