-- 如果数据库不存在就创建
CREATE DATABASE IF NOT EXISTS edu_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 如需新用户可以加:
-- CREATE USER 'some_user'@'%' IDENTIFIED BY 'some_pass';
-- GRANT ALL PRIVILEGES ON edu_db.* TO 'some_user'@'%';
-- FLUSH PRIVILEGES;
