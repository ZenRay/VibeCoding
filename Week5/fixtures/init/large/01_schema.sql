-- Large Test Database: Enterprise ERP System
-- Tables: 30+ (simplified version)

CREATE TYPE order_status AS ENUM ('draft', 'confirmed', 'shipped', 'delivered', 'cancelled');
CREATE TYPE payment_status AS ENUM ('unpaid', 'paid', 'partial');

CREATE TABLE departments (department_id SERIAL PRIMARY KEY, name VARCHAR(100), code VARCHAR(20) UNIQUE);
CREATE TABLE employees (employee_id SERIAL PRIMARY KEY, employee_number VARCHAR(20) UNIQUE, first_name VARCHAR(50), last_name VARCHAR(50), email VARCHAR(255) UNIQUE, department_id INTEGER REFERENCES departments(department_id), manager_id INTEGER REFERENCES employees(employee_id), salary NUMERIC(12, 2));
CREATE TABLE customers (customer_id SERIAL PRIMARY KEY, customer_number VARCHAR(20) UNIQUE, company_name VARCHAR(255), email VARCHAR(255), phone VARCHAR(20), account_manager_id INTEGER REFERENCES employees(employee_id));
CREATE TABLE products (product_id SERIAL PRIMARY KEY, sku VARCHAR(50) UNIQUE, name VARCHAR(255), unit_price NUMERIC(12, 2), cost_price NUMERIC(12, 2));
CREATE TABLE warehouses (warehouse_id SERIAL PRIMARY KEY, code VARCHAR(20) UNIQUE, name VARCHAR(100));
CREATE TABLE inventory (inventory_id SERIAL PRIMARY KEY, product_id INTEGER REFERENCES products(product_id), warehouse_id INTEGER REFERENCES warehouses(warehouse_id), quantity INTEGER);
CREATE TABLE sales_orders (order_id SERIAL PRIMARY KEY, order_number VARCHAR(50) UNIQUE, customer_id INTEGER REFERENCES customers(customer_id), order_date DATE, status order_status, total_amount NUMERIC(15, 2));
CREATE TABLE order_lines (line_id SERIAL PRIMARY KEY, order_id INTEGER REFERENCES sales_orders(order_id), product_id INTEGER REFERENCES products(product_id), quantity INTEGER, unit_price NUMERIC(12, 2));
CREATE TABLE invoices (invoice_id SERIAL PRIMARY KEY, invoice_number VARCHAR(50) UNIQUE, order_id INTEGER REFERENCES sales_orders(order_id), customer_id INTEGER REFERENCES customers(customer_id), total_amount NUMERIC(15, 2), status payment_status);
CREATE TABLE suppliers (supplier_id SERIAL PRIMARY KEY, supplier_number VARCHAR(20) UNIQUE, name VARCHAR(255));
CREATE TABLE purchase_orders (po_id SERIAL PRIMARY KEY, po_number VARCHAR(50) UNIQUE, supplier_id INTEGER REFERENCES suppliers(supplier_id), order_date DATE, total_amount NUMERIC(15, 2));

CREATE INDEX idx_employees_dept ON employees(department_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_orders_customer ON sales_orders(customer_id);
