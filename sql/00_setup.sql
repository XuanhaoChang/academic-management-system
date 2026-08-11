-- ============================================================
-- 00_setup.sql  以 root 身份执行一次
-- 用法: mysql -u root -p123456 < sql/00_setup.sql
-- 功能: 清空并重建数据库, 创建应用专用账户 dbadmin（本地+远程）
-- ============================================================

DROP DATABASE IF EXISTS my_db_project;
CREATE DATABASE my_db_project
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

DROP USER IF EXISTS 'dbadmin'@'localhost';
DROP USER IF EXISTS 'dbadmin'@'%';

CREATE USER 'dbadmin'@'localhost' IDENTIFIED BY 'DbAdmin2024';
CREATE USER 'dbadmin'@'%' IDENTIFIED BY 'DbAdmin2024';

-- localhost 用于本机开发
GRANT ALL PRIVILEGES ON my_db_project.* TO 'dbadmin'@'localhost';
-- % 用于远程客户端连接（建议在生产环境改为固定网段）
GRANT ALL PRIVILEGES ON my_db_project.* TO 'dbadmin'@'%';

FLUSH PRIVILEGES;

SELECT 'Database and local/remote users created successfully.' AS status;
