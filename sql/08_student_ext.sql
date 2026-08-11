USE my_db_project;

-- ============================================================
-- 08_student_ext.sql  学生端扩展对象
-- 依赖：01~07 已执行
-- ============================================================

-- 学生扩展信息
CREATE TABLE IF NOT EXISTS stu_info (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL UNIQUE,
    grade_year INT NOT NULL,
    class_name VARCHAR(50) NULL,
    phone VARCHAR(30) NULL,
    email VARCHAR(120) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    CONSTRAINT fk_stu_info_user FOREIGN KEY (student_id) REFERENCES sys_users(id)
) ENGINE=InnoDB;

-- 课程先修关系（用于先修课检测）
CREATE TABLE IF NOT EXISTS stu_course_prereq (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course_id INT NOT NULL,
    pre_course_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    UNIQUE KEY uk_course_prereq (course_id, pre_course_id),
    CONSTRAINT fk_pr_course FOREIGN KEY (course_id) REFERENCES edu_courses(id),
    CONSTRAINT fk_pr_pre_course FOREIGN KEY (pre_course_id) REFERENCES edu_courses(id)
) ENGINE=InnoDB;

-- 考试安排（README 要求“考试查询”）
CREATE TABLE IF NOT EXISTS stu_exam_schedule (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course_id INT NOT NULL,
    semester VARCHAR(20) NOT NULL,
    exam_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    exam_room VARCHAR(50) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    UNIQUE KEY uk_exam (course_id, semester),
    CONSTRAINT fk_exam_course FOREIGN KEY (course_id) REFERENCES edu_courses(id)
) ENGINE=InnoDB;

-- 缓考申请（学生端新增）
CREATE TABLE IF NOT EXISTS stu_exam_defer_req (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    semester VARCHAR(20) NOT NULL,
    reason VARCHAR(500) NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    UNIQUE KEY uk_exam_defer (student_id, course_id, semester),
    CONSTRAINT fk_defer_student FOREIGN KEY (student_id) REFERENCES sys_users(id),
    CONSTRAINT fk_defer_course FOREIGN KEY (course_id) REFERENCES edu_courses(id)
) ENGINE=InnoDB;

-- 评教表
CREATE TABLE IF NOT EXISTS stu_evaluation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    semester VARCHAR(20) NOT NULL,
    eval_score INT NOT NULL,
    eval_comment VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    UNIQUE KEY uk_eval (student_id, course_id, semester),
    CONSTRAINT fk_eval_student FOREIGN KEY (student_id) REFERENCES sys_users(id),
    CONSTRAINT fk_eval_course FOREIGN KEY (course_id) REFERENCES edu_courses(id)
) ENGINE=InnoDB;

-- 强化唯一性，避免重复选课/重复候补
SET @has_col_sel_deleted_at = (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema='my_db_project'
      AND table_name='stu_selection'
      AND column_name='deleted_at'
);
SET @sql_sel_deleted_at = IF(
    @has_col_sel_deleted_at = 0,
    'ALTER TABLE stu_selection ADD COLUMN deleted_at BIGINT NOT NULL DEFAULT 0 COMMENT ''软删除时间戳(毫秒), 0=有效'' AFTER created_at',
    'SELECT ''stu_selection.deleted_at exists'' AS info'
);
PREPARE st_sel_deleted_at FROM @sql_sel_deleted_at;
EXECUTE st_sel_deleted_at;
DEALLOCATE PREPARE st_sel_deleted_at;

SET @has_col_wait_deleted_at = (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema='my_db_project'
      AND table_name='stu_waiting_list'
      AND column_name='deleted_at'
);
SET @sql_wait_deleted_at = IF(
    @has_col_wait_deleted_at = 0,
    'ALTER TABLE stu_waiting_list ADD COLUMN deleted_at BIGINT NOT NULL DEFAULT 0 COMMENT ''软删除时间戳(毫秒), 0=有效'' AFTER created_at',
    'SELECT ''stu_waiting_list.deleted_at exists'' AS info'
);
PREPARE st_wait_deleted_at FROM @sql_wait_deleted_at;
EXECUTE st_wait_deleted_at;
DEALLOCATE PREPARE st_wait_deleted_at;

SET @has_uk_sel = (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema='my_db_project'
      AND table_name='stu_selection'
      AND index_name='uk_selection_active'
);

SET @has_uk_sel_legacy = (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema='my_db_project'
      AND table_name='stu_selection'
      AND index_name='uk_selection_student_teaching'
);

SET @sql_sel = IF(
    @has_uk_sel = 0 AND @has_uk_sel_legacy = 0,
    'ALTER TABLE stu_selection ADD UNIQUE KEY uk_selection_active (student_id, teaching_id, deleted_at)',
    'SELECT ''stu_selection unique key exists'' AS info'
);
PREPARE st_sel FROM @sql_sel;
EXECUTE st_sel;
DEALLOCATE PREPARE st_sel;

SET @has_idx_sel_tis = (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema='my_db_project'
      AND table_name='stu_selection'
      AND index_name='idx_sel_teaching_del_student'
);
SET @sql_idx_sel_tis = IF(
    @has_idx_sel_tis = 0,
    'ALTER TABLE stu_selection ADD INDEX idx_sel_teaching_del_student (teaching_id, deleted_at, student_id)',
    'SELECT ''idx_sel_teaching_del_student exists'' AS info'
);
PREPARE st_idx_sel_tis FROM @sql_idx_sel_tis;
EXECUTE st_idx_sel_tis;
DEALLOCATE PREPARE st_idx_sel_tis;

SET @has_uk_wait = (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema='my_db_project'
      AND table_name='stu_waiting_list'
      AND index_name='uk_waiting_active'
);

SET @has_uk_wait_legacy = (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema='my_db_project'
      AND table_name='stu_waiting_list'
      AND index_name='uk_waiting_student_teaching'
);

SET @sql_wait = IF(
    @has_uk_wait = 0 AND @has_uk_wait_legacy = 0,
    'ALTER TABLE stu_waiting_list ADD UNIQUE KEY uk_waiting_active (student_id, teaching_id, deleted_at)',
    'SELECT ''stu_waiting_list unique key exists'' AS info'
);
PREPARE st_wait FROM @sql_wait;
EXECUTE st_wait;
DEALLOCATE PREPARE st_wait;

SET @has_idx_wait_tdq = (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema='my_db_project'
      AND table_name='stu_waiting_list'
      AND index_name='idx_wait_teaching_del_queue'
);
SET @sql_idx_wait_tdq = IF(
    @has_idx_wait_tdq = 0,
    'ALTER TABLE stu_waiting_list ADD INDEX idx_wait_teaching_del_queue (teaching_id, deleted_at, queue_no, id)',
    'SELECT ''idx_wait_teaching_del_queue exists'' AS info'
);
PREPARE st_idx_wait_tdq FROM @sql_idx_wait_tdq;
EXECUTE st_idx_wait_tdq;
DEALLOCATE PREPARE st_idx_wait_tdq;

-- 字段语义澄清：teaching_id = 教学班实例ID（非教师ID）
ALTER TABLE stu_selection
MODIFY COLUMN teaching_id INT NOT NULL COMMENT '教学班ID(edu_teaching.id)，非教师ID';

ALTER TABLE stu_waiting_list
MODIFY COLUMN teaching_id INT NOT NULL COMMENT '教学班ID(edu_teaching.id)，非教师ID';

ALTER TABLE edu_grades
MODIFY COLUMN teaching_id INT NOT NULL COMMENT '教学班ID(edu_teaching.id)，非教师ID';

-- ============================================================
-- 强化并发过程：按当前学期 teaching.max_count / enrolled_count 控制容量
-- ============================================================
DROP PROCEDURE IF EXISTS proc_attempt_enroll;
DELIMITER $$
CREATE PROCEDURE proc_attempt_enroll(
    IN p_student_id INT,
    IN p_teaching_id INT,
    OUT p_result_code INT,
    OUT p_result_msg VARCHAR(200)
)
proc: BEGIN
    DECLARE v_semester VARCHAR(20);
    DECLARE v_course_id INT;
    DECLARE v_max_count INT DEFAULT 0;
    DECLARE v_enrolled INT DEFAULT 0;
    DECLARE v_status VARCHAR(20);
    DECLARE v_exists INT DEFAULT 0;

    SELECT config_value INTO v_semester
    FROM sys_config
    WHERE config_key = 'current_semester' AND is_deleted = 0
    LIMIT 1;

    IF v_semester IS NULL THEN
        SET p_result_code = 500;
        SET p_result_msg = '系统未配置当前学期';
        LEAVE proc;
    END IF;

        SELECT t.course_id, t.max_count, t.status, t.semester
        INTO v_course_id, v_max_count, v_status, v_semester
    FROM edu_teaching t
    WHERE t.id = p_teaching_id
      AND t.is_deleted = 0
    LIMIT 1
    FOR UPDATE;

    IF v_course_id IS NULL THEN
        SET p_result_code = 404;
        SET p_result_msg = '教学班不存在';
        LEAVE proc;
    END IF;

    IF v_status = 'CLOSED' THEN
        SET p_result_code = 423;
        SET p_result_msg = '课程已截止';
        LEAVE proc;
    END IF;

    SELECT COUNT(*) INTO v_exists
    FROM stu_selection
    WHERE student_id = p_student_id
        AND teaching_id = p_teaching_id
        AND deleted_at = 0;
    IF v_exists > 0 THEN
        SET p_result_code = 208;
        SET p_result_msg = '已选过该课程';
        LEAVE proc;
    END IF;

    -- 容量判断以实时选课人数为准，避免 enrolled_count 被历史脚本写脏后失真
    SELECT COUNT(*) INTO v_enrolled
    FROM stu_selection
    WHERE teaching_id = p_teaching_id
            AND deleted_at = 0;

    IF v_enrolled >= v_max_count THEN
        SET p_result_code = 409;
        SET p_result_msg = '课程已满';
        LEAVE proc;
    END IF;

    INSERT INTO stu_selection(student_id, teaching_id, deleted_at, is_deleted)
    VALUES (p_student_id, p_teaching_id, 0, 0);

    UPDATE edu_teaching
    SET enrolled_count = (
            SELECT COUNT(*)
            FROM stu_selection s
            WHERE s.teaching_id = p_teaching_id
                            AND s.deleted_at = 0
        ),
        status = CASE
            WHEN (
                SELECT COUNT(*)
                FROM stu_selection s
                WHERE s.teaching_id = p_teaching_id
                                    AND s.deleted_at = 0
            ) >= max_count THEN 'FULL'
            ELSE 'OPEN'
        END
    WHERE id = p_teaching_id;

    SET p_result_code = 200;
    SET p_result_msg = '选课成功';
END $$
DELIMITER ;

-- ============================================================
-- 安全版触发器：仅处理人数与状态，不在触发器内写回 stu_selection
-- 说明：
-- 1) 递补逻辑改由服务层事务执行（避免触发器内二次写同表导致死锁/冲突）
-- 2) 触发器只做轻量同步，保证旧路径仍可用
-- ============================================================
DROP TRIGGER IF EXISTS trigger_auto_fill_vacancy;
DELIMITER $$
CREATE TRIGGER trigger_auto_fill_vacancy
AFTER UPDATE ON stu_selection
FOR EACH ROW
BEGIN
    DECLARE v_teaching_id INT;

    IF NEW.deleted_at <> 0 AND OLD.deleted_at = 0 THEN
        SET v_teaching_id = OLD.teaching_id;

        IF v_teaching_id IS NOT NULL THEN
            UPDATE edu_teaching
            SET enrolled_count = GREATEST(enrolled_count - 1, 0),
                status = 'OPEN'
            WHERE id = v_teaching_id;
        END IF;
    END IF;
END $$
DELIMITER ;

SELECT '08_student_ext.sql executed.' AS status;
