#!/usr/bin/env python3
import random
from datetime import datetime, timedelta


def main():
    print("Generating large database (ERP) data...")

    with open("02_data.sql", "w") as f:
        f.write("-- Large DB Data\n")

        # 50 departments
        f.write("INSERT INTO departments (name, code) VALUES\n")
        depts = [f"('Department {i}', 'DEPT{i:03d}')" for i in range(50)]
        f.write(",\n".join(depts) + ";\n\n")

        # 1000 employees
        f.write(
            "INSERT INTO employees (employee_number, first_name, last_name, email, department_id, salary) VALUES\n"
        )
        emps = []
        for i in range(1000):
            emp_num = f"EMP{i:04d}"
            fname = f"FirstName{i}"
            lname = f"LastName{i}"
            email = f"emp{i}@company.com"
            dept = random.randint(1, 50)
            salary = round(random.uniform(40000, 150000), 2)
            emps.append(f"('{emp_num}', '{fname}', '{lname}', '{email}', {dept}, {salary})")
        f.write(",\n".join(emps) + ";\n\n")

        # 500 customers
        f.write("INSERT INTO customers (customer_number, company_name, email) VALUES\n")
        custs = [f"('CUST{i:04d}', 'Company {i}', 'cust{i}@example.com')" for i in range(500)]
        f.write(",\n".join(custs) + ";\n\n")

        # 2000 products
        f.write("INSERT INTO products (sku, name, unit_price, cost_price) VALUES\n")
        prods = []
        for i in range(2000):
            sku = f"SKU{i:05d}"
            name = f"Product {i}"
            price = round(random.uniform(10, 1000), 2)
            cost = round(price * 0.6, 2)
            prods.append(f"('{sku}', '{name}', {price}, {cost})")
        f.write(",\n".join(prods) + ";\n\n")

        # 5000 orders
        f.write(
            "INSERT INTO sales_orders (order_number, customer_id, order_date, status, total_amount) VALUES\n"
        )
        orders = []
        for i in range(5000):
            order_num = f"ORD{i:06d}"
            cust = random.randint(1, 500)
            order_date = datetime(2025, random.randint(1, 12), random.randint(1, 28)).date()
            status = random.choice(["confirmed", "shipped", "delivered"])
            total = round(random.uniform(100, 10000), 2)
            orders.append(f"('{order_num}', {cust}, '{order_date}', '{status}', {total})")
        f.write(",\n".join(orders) + ";\n")

    print("✓ Large database data generated")


if __name__ == "__main__":
    main()
