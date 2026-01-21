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

-- 创建 interview_db 数据库用于测试
CREATE DATABASE IF NOT EXISTS interview_db DEFAULT CHARACTER SET utf8mb4;

USE interview_db;

-- 创建面试相关的表
CREATE TABLE IF NOT EXISTS candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    position VARCHAR(100) NOT NULL,
    experience_years INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS interviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    interviewer VARCHAR(100) NOT NULL,
    interview_date DATE NOT NULL,
    score INT CHECK (score BETWEEN 0 AND 100),
    status ENUM('scheduled', 'completed', 'cancelled') DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 插入面试测试数据
INSERT INTO candidates (name, email, position, experience_years) VALUES
    ('Alice Wang', 'alice.wang@example.com', 'Senior Software Engineer', 5),
    ('Bob Chen', 'bob.chen@example.com', 'Frontend Developer', 3),
    ('Carol Li', 'carol.li@example.com', 'Backend Developer', 4),
    ('David Zhang', 'david.zhang@example.com', 'Full Stack Developer', 6)
ON DUPLICATE KEY UPDATE name=name;

INSERT INTO interviews (candidate_id, interviewer, interview_date, score, status, notes) VALUES
    (1, 'John Smith', '2026-01-25', 85, 'completed', '优秀的技术能力和沟通技巧'),
    (1, 'Jane Doe', '2026-01-26', 90, 'completed', '非常适合这个职位'),
    (2, 'Tom Brown', '2026-01-27', 75, 'completed', '前端技能扎实，需要提升后端能力'),
    (3, 'Sarah Wilson', '2026-01-28', 88, 'completed', '后端经验丰富，架构能力强'),
    (4, 'Mike Johnson', '2026-01-29', NULL, 'scheduled', '即将进行面试')
ON DUPLICATE KEY UPDATE score=score;

-- 切换回 testdb
USE testdb;
