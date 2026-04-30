-- ============================================================
-- 06_teacher_ext.sql  [组员A] 教师端扩展
-- 依赖: 01~05 已执行完毕
-- 执行方式: SOURCE sql/06_teacher_ext.sql;
-- ============================================================
USE my_db_project;

-- ------------------------------------------------------------
-- 1. ALTER edu_teaching — 成绩提交锁定字段
-- ------------------------------------------------------------
-- 检查并添加 is_submitted 字段
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'my_db_project' 
      AND TABLE_NAME = 'edu_teaching' 
      AND COLUMN_NAME = 'is_submitted'
);

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE edu_teaching ADD COLUMN is_submitted TINYINT NOT NULL DEFAULT 0 COMMENT ''0=未提交 1=已提交(锁定)''',
    'SELECT ''Column is_submitted already exists'' AS info'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ------------------------------------------------------------
-- 2. ALTER edu_grades — 卷面成绩字段
--    score 字段继续存储最终成绩（Python层计算后写入）
-- ------------------------------------------------------------
-- 检查并添加 exam_score 字段
SET @col_exists2 = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'my_db_project' 
      AND TABLE_NAME = 'edu_grades' 
      AND COLUMN_NAME = 'exam_score'
);

SET @sql2 = IF(@col_exists2 = 0, 
    'ALTER TABLE edu_grades ADD COLUMN exam_score DECIMAL(5,2) NULL COMMENT ''卷面成绩(0-100)，最终成绩 = exam_score*0.7 + daily_score(最高30)''',
    'SELECT ''Column exam_score already exists'' AS info'
);

PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- ------------------------------------------------------------
-- 3. 新表 edu_daily_records — 平时表现记录
--    记录每次签到/作业/章节测验的完成情况
--    平时分 = 30 × (已完成数 / 总记录数)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS edu_daily_records (
    id          INT          PRIMARY KEY AUTO_INCREMENT,
    teaching_id INT          NOT NULL,
    student_id  INT          NOT NULL,
    record_date DATE         NOT NULL,
    record_type ENUM('SIGNIN','HOMEWORK','CHAPTER_TEST') NOT NULL
                COMMENT '类型: 签到/作业/章节测验',
    completed   TINYINT      NOT NULL DEFAULT 0 COMMENT '是否完成: 1=完成 0=未完成',
    note        VARCHAR(200) NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted  TINYINT      NOT NULL DEFAULT 0,
    UNIQUE KEY uk_dr (teaching_id, student_id, record_date, record_type),
    INDEX idx_dr_teaching (teaching_id),
    CONSTRAINT fk_dr_teaching FOREIGN KEY (teaching_id) REFERENCES edu_teaching(id),
    CONSTRAINT fk_dr_student  FOREIGN KEY (student_id)  REFERENCES sys_users(id)
) ENGINE=InnoDB COMMENT='平时表现记录（签到/作业/章节测验）';

-- ------------------------------------------------------------
-- 4. 新表 edu_schedule_change_req — 调课申请
--    教师提交申请，管理员审批（组长在管理员端实现审批UI）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS edu_schedule_change_req (
    id             INT          PRIMARY KEY AUTO_INCREMENT,
    teaching_id    INT          NOT NULL,
    teacher_id     INT          NOT NULL,
    reason         VARCHAR(500) NOT NULL COMMENT '申请原因',
    original_time  VARCHAR(100) NULL     COMMENT '原上课时间',
    requested_time VARCHAR(100) NULL     COMMENT '申请调整到的时间',
    status         ENUM('PENDING','APPROVED','REJECTED') NOT NULL DEFAULT 'PENDING',
    admin_comment  VARCHAR(300) NULL     COMMENT '管理员审批意见',
    processed_by   INT          NULL     COMMENT '审批人 sys_users.id（组长接口）',
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted     TINYINT      NOT NULL DEFAULT 0,
    INDEX idx_req_teacher (teacher_id),
    INDEX idx_req_status  (status),
    INDEX idx_req_status_del_created (status, is_deleted, created_at),
    CONSTRAINT fk_req_teaching FOREIGN KEY (teaching_id) REFERENCES edu_teaching(id),
    CONSTRAINT fk_req_teacher  FOREIGN KEY (teacher_id)  REFERENCES sys_users(id)
) ENGINE=InnoDB COMMENT='调课申请（教师提交，管理员审批）';

-- ------------------------------------------------------------
-- 4.1 兼容补丁：为已存在库补复合索引与值域约束
-- ------------------------------------------------------------
SET @has_idx_req_sdc = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = 'my_db_project'
      AND table_name = 'edu_schedule_change_req'
      AND index_name = 'idx_req_status_del_created'
);

SET @sql_idx_req_sdc = IF(
    @has_idx_req_sdc = 0,
    'ALTER TABLE edu_schedule_change_req ADD INDEX idx_req_status_del_created (status, is_deleted, created_at)',
    'SELECT ''idx_req_status_del_created exists'' AS info'
);

PREPARE stmt_idx_req_sdc FROM @sql_idx_req_sdc;
EXECUTE stmt_idx_req_sdc;
DEALLOCATE PREPARE stmt_idx_req_sdc;

SET @has_idx_grades_tis = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = 'my_db_project'
      AND table_name = 'edu_grades'
      AND index_name = 'idx_grades_teaching_del_student'
);

SET @sql_idx_grades_tis = IF(
    @has_idx_grades_tis = 0,
    'ALTER TABLE edu_grades ADD INDEX idx_grades_teaching_del_student (teaching_id, is_deleted, student_id)',
    'SELECT ''idx_grades_teaching_del_student exists'' AS info'
);

PREPARE stmt_idx_grades_tis FROM @sql_idx_grades_tis;
EXECUTE stmt_idx_grades_tis;
DEALLOCATE PREPARE stmt_idx_grades_tis;

SET @has_ck_teaching_max = (
    SELECT COUNT(*)
    FROM information_schema.table_constraints
    WHERE constraint_schema = 'my_db_project'
      AND table_name = 'edu_teaching'
      AND constraint_name = 'ck_teaching_max_count_pos'
      AND constraint_type = 'CHECK'
);

SET @sql_ck_teaching_max = IF(
    @has_ck_teaching_max = 0,
    'ALTER TABLE edu_teaching ADD CONSTRAINT ck_teaching_max_count_pos CHECK (max_count > 0)',
    'SELECT ''ck_teaching_max_count_pos exists'' AS info'
);

PREPARE stmt_ck_teaching_max FROM @sql_ck_teaching_max;
EXECUTE stmt_ck_teaching_max;
DEALLOCATE PREPARE stmt_ck_teaching_max;

SET @has_ck_grade_exam = (
    SELECT COUNT(*)
    FROM information_schema.table_constraints
    WHERE constraint_schema = 'my_db_project'
      AND table_name = 'edu_grades'
      AND constraint_name = 'ck_grade_exam_score_range'
      AND constraint_type = 'CHECK'
);

SET @sql_ck_grade_exam = IF(
    @has_ck_grade_exam = 0,
    'ALTER TABLE edu_grades ADD CONSTRAINT ck_grade_exam_score_range CHECK (exam_score IS NULL OR (exam_score >= 0 AND exam_score <= 100))',
    'SELECT ''ck_grade_exam_score_range exists'' AS info'
);

PREPARE stmt_ck_grade_exam FROM @sql_ck_grade_exam;
EXECUTE stmt_ck_grade_exam;
DEALLOCATE PREPARE stmt_ck_grade_exam;

SET @has_ck_grade_score = (
    SELECT COUNT(*)
    FROM information_schema.table_constraints
    WHERE constraint_schema = 'my_db_project'
      AND table_name = 'edu_grades'
      AND constraint_name = 'ck_grade_score_range'
      AND constraint_type = 'CHECK'
);

SET @sql_ck_grade_score = IF(
    @has_ck_grade_score = 0,
    'ALTER TABLE edu_grades ADD CONSTRAINT ck_grade_score_range CHECK (score IS NULL OR (score >= 0 AND score <= 100))',
    'SELECT ''ck_grade_score_range exists'' AS info'
);

PREPARE stmt_ck_grade_score FROM @sql_ck_grade_score;
EXECUTE stmt_ck_grade_score;
DEALLOCATE PREPARE stmt_ck_grade_score;

-- ------------------------------------------------------------
-- 5. 视图 view_teacher_schedule — 教师完整课表
--    注意：依赖 edu_teaching.is_submitted，须在 ALTER 之后执行
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW view_teacher_schedule AS
SELECT
    t.id             AS teaching_id,
    t.teacher_id,
    u.real_name      AS teacher_name,
    c.course_code,
    c.course_name,
    c.credits,
    t.classroom,
    t.timeslot,
    t.semester,
    t.enrolled_count,
    t.max_count,
    t.status,
    t.is_submitted,
    d.dept_name
FROM edu_teaching  t
JOIN edu_courses   c ON t.course_id  = c.id AND c.is_deleted = 0
JOIN sys_users     u ON t.teacher_id = u.id AND u.is_deleted = 0
JOIN base_dept     d ON c.dept_id    = d.id AND d.is_deleted = 0
WHERE t.is_deleted = 0;

-- ------------------------------------------------------------
-- 6. 视图 view_daily_score — 按学生汇总平时分
--    平时分 = 30 × (已完成记录数 / 总记录数)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW view_daily_score AS
SELECT
    teaching_id,
    student_id,
    COUNT(*)                                                AS total_records,
    SUM(completed)                                          AS completed_records,
    ROUND(SUM(completed) * 100.0 / NULLIF(COUNT(*), 0), 1) AS completion_rate,
    ROUND(SUM(completed) * 30.0  / NULLIF(COUNT(*), 0), 2) AS daily_score
FROM edu_daily_records
WHERE is_deleted = 0
GROUP BY teaching_id, student_id;

-- ------------------------------------------------------------
-- 7. 存储过程 proc_submit_grades(p_teaching_id)
--    提交锁定指定班级成绩：
--      - 若仍有 exam_score IS NULL 则 SIGNAL 报错
--      - 若无成绩记录则 SIGNAL 报错
--      - 成功则 SET is_submitted=1 并返回提交数量
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS proc_submit_grades;

DELIMITER $$

CREATE PROCEDURE proc_submit_grades(IN p_teaching_id INT)
BEGIN
    DECLARE v_missing INT DEFAULT 0;
    DECLARE v_count   INT DEFAULT 0;

    -- 检查是否有未录入卷面成绩的学生
    SELECT COUNT(*) INTO v_missing
    FROM edu_grades
    WHERE teaching_id = p_teaching_id
      AND is_deleted  = 0
      AND exam_score IS NULL;

    IF v_missing > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '仍有学生卷面成绩未录入，无法提交';
    END IF;

    -- 检查是否存在任何成绩记录
    SELECT COUNT(*) INTO v_count
    FROM edu_grades
    WHERE teaching_id = p_teaching_id
      AND is_deleted  = 0;

    IF v_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '该班级尚无成绩记录，无法提交';
    END IF;

    -- 锁定成绩
    UPDATE edu_teaching
    SET    is_submitted = 1
    WHERE  id = p_teaching_id AND is_deleted = 0;

    -- 返回结果集（Python层通过 fetchone() 读取）
    SELECT v_count AS submitted_count, p_teaching_id AS teaching_id;
END $$

DELIMITER ;

-- ------------------------------------------------------------
-- 8. 触发器 trg_after_grade_submit
--    成绩提交锁定时自动写审计日志
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_after_grade_submit;

DELIMITER $$

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
END $$

DELIMITER ;

SELECT 'Teacher extension SQL executed successfully.' AS status;
