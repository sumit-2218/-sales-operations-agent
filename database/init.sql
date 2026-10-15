-- Run once as the MySQL root/admin user (NOT used by the application at runtime):
--   mysql -u root -p < database/init.sql
-- 1) Replace CHANGE_ME_DB_PASSWORD below with a strong password of your own.
-- 2) Put the same password in DATABASE_URL in your .env file.
CREATE DATABASE IF NOT EXISTS sales_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'salesagent'@'localhost' IDENTIFIED BY '8857';
CREATE USER IF NOT EXISTS 'salesagent'@'127.0.0.1' IDENTIFIED BY '8857';
GRANT ALL PRIVILEGES ON sales_agent.* TO 'salesagent'@'localhost';
GRANT ALL PRIVILEGES ON sales_agent.* TO 'salesagent'@'127.0.0.1';
FLUSH PRIVILEGES;
