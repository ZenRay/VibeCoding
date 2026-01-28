# Feature Specification: MySQL Database Support

**Feature Branch**: `002-mysql-support`
**Created**: 2026-01-22
**Status**: Draft
**Input**: User description: "参考backend中的PostgreSQL实现 MySQL的metadata提取和查询支持,同时自然语言生成sql也支持MySQL。数据库的服务需要一样放在 env 中的docker compose 服务中。支持查询 mysql 中的数据。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add MySQL Database Connection (Priority: P1)

A user wants to connect to a MySQL database and view its metadata (tables, columns, data types) just like they can currently do with PostgreSQL databases.

**Why this priority**: This is the foundational capability. Without being able to connect to and view MySQL database structure, no other MySQL functionality can work. It enables users to start exploring their MySQL databases immediately.

**Independent Test**: Can be fully tested by adding a MySQL connection string through the UI, successfully connecting, and viewing the database schema (tables and columns) in the metadata browser. Delivers immediate value by allowing users to explore MySQL database structure.

**Acceptance Scenarios**:

1. **Given** a user has access to a MySQL database, **When** they add a MySQL connection with valid credentials, **Then** the system successfully connects and displays the connection in the database list
2. **Given** a MySQL database is connected, **When** the user views the metadata, **Then** all tables, views, columns, and their data types are displayed correctly
3. **Given** a MySQL database connection exists, **When** the user refreshes metadata, **Then** any schema changes are reflected in the metadata view
4. **Given** invalid MySQL credentials are provided, **When** the user attempts to connect, **Then** a clear error message is displayed explaining the connection failure

---

### User Story 2 - Execute SQL Queries on MySQL (Priority: P2)

A user wants to write and execute SQL queries against their MySQL database and view the results in a formatted table, similar to the existing PostgreSQL query functionality.

**Why this priority**: This is the primary use case for the tool. Once users can connect to MySQL databases, they need to query them. This enables all manual SQL operations users need to perform.

**Independent Test**: Can be tested by connecting to a MySQL database, writing a SELECT query in the SQL editor, executing it, and viewing formatted results. Delivers value by enabling users to query their MySQL data directly.

**Acceptance Scenarios**:

1. **Given** a MySQL database is connected, **When** the user writes a SELECT query and executes it, **Then** the query results are displayed in a formatted table
2. **Given** a user executes a query without a LIMIT clause, **When** the query is a SELECT without aggregations, **Then** the system automatically adds LIMIT 1000 to prevent excessive results
3. **Given** a user executes a query with aggregation functions (COUNT, SUM, etc.), **When** the query runs, **Then** no automatic LIMIT is added and full aggregated results are returned
4. **Given** a user executes an invalid SQL query, **When** the query fails, **Then** the MySQL error message is clearly displayed to help debug the issue
5. **Given** a user executes a potentially dangerous query (DROP, DELETE without WHERE), **When** the query is submitted, **Then** the system blocks it and shows a security warning

---

### User Story 3 - Natural Language to MySQL SQL Generation (Priority: P3)

A user wants to describe what data they need in natural language and have the system generate a MySQL-compatible SQL query that they can review and execute.

**Why this priority**: This is an advanced productivity feature. While valuable for non-SQL experts or complex queries, it's not essential for basic database operations. Users can still manually write all queries without this feature.

**Independent Test**: Can be tested by typing a natural language request (e.g., "show me all users created in the last 7 days"), generating the SQL query, reviewing it for MySQL syntax correctness, and executing it. Delivers value by reducing SQL writing time and helping users learn MySQL syntax.

**Acceptance Scenarios**:

1. **Given** a MySQL database is connected with known schema, **When** the user enters a natural language query request, **Then** the system generates valid MySQL SQL syntax using the correct table and column names
2. **Given** a natural language request is processed, **When** MySQL-specific functions are needed (e.g., DATE_SUB, CONCAT), **Then** the generated SQL uses MySQL syntax, not PostgreSQL syntax
3. **Given** a natural language request could be dangerous (e.g., "delete all users"), **When** the SQL is generated, **Then** the system includes safeguards (WHERE clauses) or warns the user
4. **Given** the AI generates SQL, **When** the user reviews it, **Then** they can edit the SQL before executing it
5. **Given** a natural language request is ambiguous, **When** the schema context is insufficient, **Then** the system asks clarifying questions or makes reasonable assumptions documented in comments

---

### Edge Cases

- What happens when a MySQL connection is lost mid-query? System should detect connection failure and display clear error message allowing user to reconnect.
- How does the system handle MySQL databases with thousands of tables? Metadata extraction should be paginated or progressively loaded to avoid memory issues and long loading times.
- What happens when MySQL and PostgreSQL have different data type names (e.g., TEXT vs VARCHAR)? System should correctly map and display MySQL-specific data types without confusion.
- How does the system handle MySQL-specific features like AUTO_INCREMENT, UNSIGNED integers, or ENUM types? These should be properly displayed in metadata and preserved in query results.
- What happens when a user tries to execute MySQL-specific syntax (e.g., LIMIT with OFFSET) that differs from PostgreSQL? The system should support MySQL syntax variations correctly.
- How does the system handle MySQL's case sensitivity behavior (table names are case-sensitive on Linux, not on Windows)? System should respect the actual database's behavior and not impose artificial restrictions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support MySQL connection strings in the format `mysql://user:password@host:port/database`
- **FR-002**: System MUST extract and display metadata from MySQL databases including tables, views, columns, data types, and constraints
- **FR-003**: System MUST execute SELECT queries against MySQL databases and return results in a structured format
- **FR-004**: System MUST automatically add LIMIT 1000 to MySQL SELECT queries without LIMIT clauses, unless the query contains aggregation functions
- **FR-005**: System MUST block dangerous SQL operations on MySQL databases (DROP, TRUNCATE, DELETE without WHERE, UPDATE without WHERE)
- **FR-006**: System MUST validate MySQL connection strings before attempting connection
- **FR-007**: System MUST generate MySQL-compatible SQL from natural language requests using database schema context
- **FR-008**: System MUST use MySQL-specific syntax and functions (DATE_SUB, CONCAT, etc.) when generating SQL, not PostgreSQL equivalents
- **FR-009**: System MUST handle MySQL-specific data types (TINYINT, MEDIUMTEXT, ENUM, SET, etc.) correctly in metadata and results
- **FR-010**: System MUST provide clear error messages for MySQL connection failures, query errors, and validation failures
- **FR-011**: System MUST store MySQL connection information persistently so users can reconnect without re-entering credentials
- **FR-012**: System MUST allow users to test MySQL connections before saving them
- **FR-013**: System MUST timeout MySQL queries after a configurable period (default 30 seconds) to prevent hanging connections
- **FR-014**: System MUST cache MySQL metadata locally to improve performance and reduce database load
- **FR-015**: System MUST detect when MySQL schema has changed and allow users to refresh cached metadata

### Key Entities *(include if feature involves data)*

- **MySQL Database Connection**: Represents a connection to a MySQL database, including connection string, host, port, database name, credentials, and connection status
- **MySQL Table Metadata**: Represents structure of a MySQL table including table name, column names, column data types (MySQL-specific types), primary keys, indexes, and row count estimate
- **MySQL View Metadata**: Represents structure of a MySQL view including view name, column definitions, and view definition SQL
- **MySQL Query Result**: Represents data returned from a MySQL query execution including column names, data types, row data, execution time, and row count
- **Natural Language SQL Request**: Represents a user's natural language description of desired data, the MySQL database context, generated MySQL SQL query, and generation metadata

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully connect to MySQL databases and view metadata within 30 seconds of entering connection details
- **SC-002**: Users can execute SELECT queries on MySQL databases and see formatted results within 2 seconds for queries returning up to 1000 rows
- **SC-003**: System correctly handles 100% of standard MySQL data types (INT, VARCHAR, TEXT, DATE, DATETIME, DECIMAL, etc.) without data loss or misrepresentation
- **SC-004**: Natural language to SQL generation produces executable MySQL queries with 90% accuracy for common query patterns (simple SELECT, filtering, joins, aggregations)
- **SC-005**: System blocks 100% of dangerous SQL operations (DROP, TRUNCATE, DELETE/UPDATE without WHERE) on MySQL databases before execution
- **SC-006**: Users can manage (add, edit, delete, test) MySQL connections with the same ease as existing PostgreSQL connections, completing connection setup in under 1 minute
- **SC-007**: System handles MySQL connection failures gracefully with clear error messages in 100% of cases, allowing users to diagnose and fix connection issues
- **SC-008**: Metadata caching reduces repeated metadata queries to MySQL databases by 95%, improving performance and reducing database load

## Assumptions *(optional)*

### Technical Assumptions

- MySQL servers support version 5.7 or higher (industry standard for production deployments)
- MySQL databases use UTF-8 or UTF-8MB4 character encoding (standard practice)
- Users have sufficient permissions to query INFORMATION_SCHEMA tables for metadata extraction
- MySQL connection timeouts are acceptable at 30 seconds (standard web application timeout)

### User Assumptions

- Users understand basic MySQL concepts (databases, tables, columns)
- Users have valid MySQL connection credentials with appropriate permissions
- Users will use the same UI/UX patterns learned from PostgreSQL connections (no training needed)
- Users prefer seeing MySQL-native data types rather than genericized type names

### Infrastructure Assumptions

- MySQL database service runs in Docker Compose alongside PostgreSQL (as specified in requirements)
- MySQL test database initializes with sample data for testing purposes
- Network connectivity between application and MySQL databases is reliable
- MySQL databases are configured to accept remote connections (not localhost-only)

## Out of Scope *(optional)*

### Explicitly Excluded

- MySQL-specific administration features (user management, permission grants, table optimization)
- MySQL replication monitoring or management
- Migration tools to convert MySQL databases to PostgreSQL or vice versa
- MySQL stored procedure execution or management
- MySQL trigger management or debugging
- MySQL transaction management (BEGIN, COMMIT, ROLLBACK) - queries are auto-committed
- MySQL performance tuning or EXPLAIN plan analysis
- Support for MySQL versions older than 5.7
- MySQL-specific backup or restore functionality

### Future Considerations

- Support for MySQL 8.0 features (window functions, CTEs, JSON functions)
- MySQL query performance monitoring and optimization suggestions
- Comparison view showing schema differences between MySQL and PostgreSQL databases
- Bulk data export from MySQL to various formats (CSV, JSON, Excel)

## Dependencies *(optional)*

### External Dependencies

- MySQL Docker image (mysql:8.0) available in Docker registry
- MySQL Python driver (aiomysql) compatible with Python 3.12+
- OpenAI API for natural language to SQL generation (same as existing PostgreSQL feature)
- SQL parsing library (sqlglot) supporting MySQL syntax variations

### Internal Dependencies

- Existing database connection management UI (reused for MySQL)
- Existing metadata display components (adapted for MySQL data types)
- Existing SQL editor component (works with MySQL syntax)
- Existing query result display components (reused for MySQL results)
- Existing SQL security validation layer (extended for MySQL-specific patterns)
- Existing metadata caching infrastructure (extended for MySQL)

### Infrastructure Dependencies

- Docker Compose configuration in env/ directory
- MySQL initialization scripts for test data (env/init-scripts/mysql-init.sql)
- Network configuration allowing backend to reach MySQL container
- Persistent volume for MySQL data (mysql-data volume)
