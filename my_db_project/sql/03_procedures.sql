USE my_db_project;

-- 注意：proc_attempt_enroll 的最终定义统一放在 sql/08_student_ext.sql。
-- 本文件仅保留通用过程，避免同名对象在多文件重复定义带来的初始化顺序漂移。

-- ============================================================
-- [组员A] proc_archive_grades
-- 将指定学期的成绩迁移至归档表 edu_archives（软删除主表记录）
-- 使用方式: CALL proc_archive_grades('2024-1');
-- ============================================================

DELIMITER $$

DROP PROCEDURE IF EXISTS proc_archive_grades $$
CREATE PROCEDURE proc_archive_grades(IN p_semester VARCHAR(20))
BEGIN
    DECLARE v_archived INT DEFAULT 0;

    -- 将尚未归档的成绩插入归档表
    INSERT INTO edu_archives (
        original_grade_id, student_id, teaching_id, score
    )
    SELECT
        g.id, g.student_id, g.teaching_id, g.score
    FROM edu_grades  g
    JOIN edu_teaching t ON g.teaching_id = t.id
    WHERE t.semester  = p_semester
      AND g.is_deleted = 0
      AND NOT EXISTS (
          SELECT 1 FROM edu_archives a WHERE a.original_grade_id = g.id
      );

    SET v_archived = ROW_COUNT();

    -- 软删除主表对应记录，保持主表轻量
    UPDATE edu_grades g
    JOIN   edu_teaching t ON g.teaching_id = t.id
    SET    g.is_deleted = 1
    WHERE  t.semester   = p_semester
      AND  g.is_deleted = 0;

    SELECT v_archived AS archived_rows, p_semester AS semester;
END $$

DELIMITER ;
