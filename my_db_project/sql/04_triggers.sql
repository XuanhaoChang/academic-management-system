USE my_db_project;

DELIMITER $$

DROP TRIGGER IF EXISTS trigger_audit_log_sys_users_update $$
CREATE TRIGGER trigger_audit_log_sys_users_update
AFTER UPDATE ON sys_users
FOR EACH ROW
BEGIN
    INSERT INTO sys_audit_logs(user_id, action_type, detail)
    VALUES (NEW.id, 'USER_UPDATED', CONCAT('username=', NEW.username, ', is_deleted=', NEW.is_deleted));
END $$

DROP TRIGGER IF EXISTS trigger_audit_log_sys_users_insert $$
CREATE TRIGGER trigger_audit_log_sys_users_insert
AFTER INSERT ON sys_users
FOR EACH ROW
BEGIN
    INSERT INTO sys_audit_logs(user_id, action_type, detail)
    VALUES (NEW.id, 'USER_CREATED', CONCAT('username=', NEW.username));
END $$

-- 注意：trigger_auto_fill_vacancy 的最终定义统一放在 sql/08_student_ext.sql。
-- 本文件仅保留系统级审计触发器，避免同名触发器在多文件重复定义。

DELIMITER ;
