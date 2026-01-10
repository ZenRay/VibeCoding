-- MySQL 测试数据库初始化脚本
-- 用于 docker-compose 自动初始化测试数据

-- 创建测试表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    age INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 插入测试数据
INSERT INTO users (name, email, age) VALUES
    ('张三', 'zhangsan@example.com', 25),
    ('李四', 'lisi@example.com', 30),
    ('王五', 'wangwu@example.com', 35),
    ('赵六', 'zhaoliu@example.com', 28)
ON DUPLICATE KEY UPDATE name=name;

INSERT INTO products (name, description, price, stock) VALUES
    ('产品A', '这是产品A的描述', 99.99, 100),
    ('产品B', '这是产品B的描述', 199.99, 50),
    ('产品C', '这是产品C的描述', 299.99, 25)
ON DUPLICATE KEY UPDATE name=name;

INSERT INTO orders (user_id, product_name, quantity, price) VALUES
    (1, '产品A', 2, 99.99),
    (1, '产品B', 1, 199.99),
    (2, '产品A', 3, 99.99),
    (3, '产品C', 1, 299.99)
ON DUPLICATE KEY UPDATE quantity=quantity;

-- 创建视图
CREATE OR REPLACE VIEW user_order_summary AS
SELECT
    u.id AS user_id,
    u.name AS user_name,
    u.email,
    COUNT(o.id) AS total_orders,
    COALESCE(SUM(o.price * o.quantity), 0) AS total_amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name, u.email;
