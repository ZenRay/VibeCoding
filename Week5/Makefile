.PHONY: help up down clean rebuild test-small test-medium test-large test-all generate-data

# Default target
help:
	@echo "PostgreSQL MCP Test Database Management"
	@echo ""
	@echo "Available targets:"
	@echo "  make up              - Start all test databases"
	@echo "  make down            - Stop all test databases"
	@echo "  make clean           - Stop and remove all data"
	@echo "  make rebuild         - Clean and rebuild all databases"
	@echo "  make generate-data   - Generate sample data for all databases"
	@echo "  make test-small      - Test connection to small database"
	@echo "  make test-medium     - Test connection to medium database"
	@echo "  make test-large      - Test connection to large database"
	@echo "  make test-all        - Test all database connections"
	@echo "  make logs            - Show logs from all databases"
	@echo "  make stats           - Show database statistics"

# Start all databases
up:
	@echo "Starting test databases..."
	cd fixtures && docker compose up -d
	@echo "Waiting for databases to be ready..."
	@sleep 10
	@echo "✓ Databases started"
	@$(MAKE) test-all

# Stop databases
down:
	@echo "Stopping test databases..."
	cd fixtures && docker compose down
	@echo "✓ Databases stopped"

# Clean everything
clean:
	@echo "Cleaning test databases..."
	cd fixtures && docker compose down -v
	@echo "✓ All data removed"

# Rebuild from scratch
rebuild: clean
	@echo "Rebuilding test databases..."
	@$(MAKE) generate-data
	@$(MAKE) up
	@echo "✓ Rebuild complete"

# Generate sample data
generate-data:
	@echo "Generating test data..."
	cd fixtures/small && python3 generate_data.py
	cd fixtures/medium && python3 generate_data.py
	cd fixtures/large && python3 generate_data.py
	@echo "✓ Data generation complete"

# Test database connections
test-small:
	@echo "Testing small database connection..."
	@docker exec mcp-test-db psql -U testuser -d ecommerce_small -c "SELECT 'Small DB' as database, count(*) as table_count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" || echo "✗ Small DB not ready"

test-medium:
	@echo "Testing medium database connection..."
	@docker exec mcp-test-db psql -U testuser -d social_medium -c "SELECT 'Medium DB' as database, count(*) as table_count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" || echo "✗ Medium DB not ready"

test-large:
	@echo "Testing large database connection..."
	@docker exec mcp-test-db psql -U testuser -d erp_large -c "SELECT 'Large DB' as database, count(*) as table_count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" || echo "✗ Large DB not ready"

test-all: test-small test-medium test-large
	@echo ""
	@echo "✓ All database tests complete"

# Show logs
logs:
	cd fixtures && docker compose logs -f

# Show database statistics
stats:
	@echo "=== Database Statistics ==="
	@echo ""
	@echo "Small Database (ecommerce_small):"
	@docker exec mcp-test-db psql -U testuser -d ecommerce_small -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;" 2>/dev/null || echo "Small DB not available"
	@echo ""
	@echo "Medium Database (social_medium):"
	@docker exec mcp-test-db psql -U testuser -d social_medium -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;" 2>/dev/null || echo "Medium DB not available"
	@echo ""
	@echo "Large Database (erp_large):"
	@docker exec mcp-test-db psql -U testuser -d erp_large -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;" 2>/dev/null || echo "Large DB not available"
