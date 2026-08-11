"""创建存储过程和触发器"""
import mysql.connector

from core.config import load_db_config

config = load_db_config()

proc_submit_grades = """
CREATE PROCEDURE proc_submit_grades(IN p_teaching_id INT)
BEGIN
    DECLARE v_missing INT DEFAULT 0;
    DECLARE v_count   INT DEFAULT 0;

    SELECT COUNT(*) INTO v_missing
    FROM edu_grades
    WHERE teaching_id = p_teaching_id
      AND is_deleted  = 0
      AND exam_score IS NULL;

    IF v_missing > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '仍有学生卷面成绩未录入，无法提交';
    END IF;

    SELECT COUNT(*) INTO v_count
    FROM edu_grades
    WHERE teaching_id = p_teaching_id
      AND is_deleted  = 0;

    IF v_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '该班级尚无成绩记录，无法提交';
    END IF;

    UPDATE edu_teaching
    SET    is_submitted = 1
    WHERE  id = p_teaching_id AND is_deleted = 0;

    SELECT v_count AS submitted_count, p_teaching_id AS teaching_id;
END
"""

trigger_grade_submit = """
CREATE TRIGGER trg_after_grade_submit
AFTER UPDATE ON edu_teaching
FOR EACH ROW
BEGIN
    IF NEW.is_submitted = 1 AND OLD.is_submitted = 0 THEN
        INSERT INTO sys_audit_logs (user_id, action_type, detail)
        VALUES (
            NEW.teacher_id,
            'SUBMIT_GRADES',
            CONCAT('teaching_id=', NEW.id, ', semester=', NEW.semester)
        );
    END IF;
END
"""

def main():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DROP PROCEDURE IF EXISTS proc_submit_grades")
        print("[OK] 删除旧存储过程")
        
        cursor.execute(proc_submit_grades)
        conn.commit()
        print("[OK] 创建存储过程 proc_submit_grades")
        
    except Exception as e:
        print(f"[FAIL] 存储过程创建失败: {e}")
    
    try:
        cursor.execute("DROP TRIGGER IF EXISTS trg_after_grade_submit")
        print("[OK] 删除旧触发器")
        
        cursor.execute(trigger_grade_submit)
        conn.commit()
        print("[OK] 创建触发器 trg_after_grade_submit")
        
    except Exception as e:
        print(f"[FAIL] 触发器创建失败: {e}")
    
    cursor.close()
    conn.close()
    
    print("\n数据库对象创建完成！")

if __name__ == '__main__':
    main()
