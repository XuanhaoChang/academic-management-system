USE my_db_project;

START TRANSACTION;

-- ============================================================
-- 学生端选课 mock 对齐注入（仅数据，不改结构）
-- 目标：让学生端“可选/已选/候补/考试/评教”有可演示数据，且与教师端课程一致
-- ============================================================

SET @sem = (
    SELECT config_value
    FROM sys_config
    WHERE config_key = 'current_semester' AND is_deleted = 0
    LIMIT 1
);

SET @sem_year = CAST(SUBSTRING_INDEX(@sem, '-', 1) AS UNSIGNED);

SET @stu1 = (SELECT id FROM sys_users WHERE username = 'stu001' AND role_id = 3 AND is_deleted = 0 LIMIT 1);
SET @stu2 = (SELECT id FROM sys_users WHERE username = 'stu002' AND role_id = 3 AND is_deleted = 0 LIMIT 1);

DROP TEMPORARY TABLE IF EXISTS tmp_sem_teaching_ids;
CREATE TEMPORARY TABLE tmp_sem_teaching_ids (
    teaching_id INT PRIMARY KEY
) ENGINE=MEMORY;

INSERT INTO tmp_sem_teaching_ids(teaching_id)
SELECT id
FROM edu_teaching
WHERE semester = @sem
  AND is_deleted = 0;

-- ------------------------------------------------------------
-- 1) 学生资料对齐：确保两个演示账号可见当前学年课程
-- ------------------------------------------------------------
INSERT INTO stu_info(student_id, grade_year, class_name, phone, email, is_deleted)
SELECT @stu1, @sem_year, '计科01班', '13800000001', 'stu001@campus.edu', 0
WHERE @stu1 IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM stu_info si WHERE si.student_id = @stu1);

INSERT INTO stu_info(student_id, grade_year, class_name, phone, email, is_deleted)
SELECT @stu2, @sem_year, '计科01班', '13800000002', 'stu002@campus.edu', 0
WHERE @stu2 IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM stu_info si WHERE si.student_id = @stu2);

UPDATE stu_info
SET grade_year = @sem_year,
    is_deleted = 0
WHERE student_id IN (@stu1, @stu2);

-- ------------------------------------------------------------
-- 2) 可选课池（学生端建议少量课程）：仅 CS 院系 6 门
-- ------------------------------------------------------------
DROP TEMPORARY TABLE IF EXISTS tmp_student_pool;
CREATE TEMPORARY TABLE tmp_student_pool (
    teaching_id INT PRIMARY KEY,
    course_id   INT NOT NULL
) ENGINE=MEMORY;

INSERT INTO tmp_student_pool (teaching_id, course_id)
SELECT t.id, t.course_id
FROM edu_teaching t
JOIN edu_courses c ON c.id = t.course_id AND c.is_deleted = 0
JOIN base_dept d ON d.id = c.dept_id AND d.is_deleted = 0
WHERE t.is_deleted = 0
  AND t.semester = @sem
  AND d.dept_code = 'CS'
  AND c.course_code IN ('CS101','CS102','CS105','CS106','CS107','CS108')
ORDER BY c.course_code, t.id
LIMIT 6;

-- 若教学班容量过低，抬到 40 便于演示（仅数据调整）
UPDATE edu_teaching t
JOIN tmp_student_pool p ON p.teaching_id = t.id
SET t.max_count = CASE WHEN t.max_count < 40 THEN 40 ELSE t.max_count END,
    t.status = 'OPEN';

-- ------------------------------------------------------------
-- 3) 已选课程 mock（两个演示学生）
--    stu001: 4 门；stu002: 3 门
-- ------------------------------------------------------------
DROP TEMPORARY TABLE IF EXISTS tmp_pick;
CREATE TEMPORARY TABLE tmp_pick (
    student_id INT NOT NULL,
    teaching_id INT NOT NULL,
    PRIMARY KEY(student_id, teaching_id)
) ENGINE=MEMORY;

-- stu001 选 4 门
INSERT INTO tmp_pick(student_id, teaching_id)
SELECT @stu1, teaching_id
FROM (
    SELECT teaching_id, ROW_NUMBER() OVER (ORDER BY teaching_id) AS rn
    FROM tmp_student_pool
) x
WHERE @stu1 IS NOT NULL AND x.rn <= 4;

-- stu002 选 3 门
INSERT INTO tmp_pick(student_id, teaching_id)
SELECT @stu2, teaching_id
FROM (
    SELECT teaching_id, ROW_NUMBER() OVER (ORDER BY teaching_id) AS rn
    FROM tmp_student_pool
) x
WHERE @stu2 IS NOT NULL AND x.rn BETWEEN 2 AND 4;

-- 先清理两个演示学生在当前学期的历史已选（仅当前学期），再按 tmp_pick 回填
UPDATE stu_selection s
JOIN tmp_sem_teaching_ids ts ON ts.teaching_id = s.teaching_id
SET s.deleted_at = UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3)) * 1000,
    s.is_deleted = 1
WHERE s.student_id IN (@stu1, @stu2)
  AND s.deleted_at = 0
  AND s.is_deleted = 0
  AND NOT EXISTS (
      SELECT 1
      FROM tmp_pick p
      WHERE p.student_id = s.student_id
        AND p.teaching_id = s.teaching_id
  );

INSERT INTO stu_selection(student_id, teaching_id, deleted_at, is_deleted)
SELECT p.student_id, p.teaching_id, 0, 0
FROM tmp_pick p
LEFT JOIN stu_selection s
  ON s.student_id = p.student_id
 AND s.teaching_id = p.teaching_id
 AND s.deleted_at = 0
 AND s.is_deleted = 0
WHERE s.id IS NULL;

-- ------------------------------------------------------------
-- 4) 候补 mock（构造 1 门课候补）
-- ------------------------------------------------------------
SET @wait_tid = (
    SELECT teaching_id
    FROM (
        SELECT teaching_id, ROW_NUMBER() OVER (ORDER BY teaching_id DESC) AS rn
        FROM tmp_student_pool
    ) z
    WHERE z.rn = 1
);

-- 将该课设为“满员”状态，便于学生端展示候补逻辑
UPDATE edu_teaching t
SET t.max_count = GREATEST(2, (
        SELECT COUNT(*) FROM stu_selection s
        WHERE s.teaching_id = t.id AND s.deleted_at = 0 AND s.is_deleted = 0
    ))
WHERE t.id = @wait_tid;

-- stu001 进入候补队列（若尚未在该课已选）
UPDATE stu_waiting_list w
JOIN tmp_sem_teaching_ids ts ON ts.teaching_id = w.teaching_id
SET w.deleted_at = UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3)) * 1000,
    w.is_deleted = 1
WHERE w.student_id IN (@stu1, @stu2)
  AND w.deleted_at = 0
  AND w.is_deleted = 0;

INSERT INTO stu_waiting_list(student_id, teaching_id, queue_no, deleted_at, is_deleted)
SELECT @stu1, @wait_tid, 1, 0, 0
WHERE @stu1 IS NOT NULL
  AND @wait_tid IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM stu_selection s
      WHERE s.student_id = @stu1 AND s.teaching_id = @wait_tid
        AND s.deleted_at = 0 AND s.is_deleted = 0
  )
  AND NOT EXISTS (
      SELECT 1 FROM stu_waiting_list w
      WHERE w.student_id = @stu1 AND w.teaching_id = @wait_tid
        AND w.deleted_at = 0 AND w.is_deleted = 0
  );

-- ------------------------------------------------------------
-- 5) 考试安排 + 评教 mock
-- ------------------------------------------------------------
INSERT INTO stu_exam_schedule(course_id, semester, exam_date, start_time, end_time, exam_room, is_deleted)
SELECT
    p.course_id,
    @sem,
    DATE_ADD('2024-12-15', INTERVAL ROW_NUMBER() OVER (ORDER BY p.course_id) DAY),
    '09:00:00',
    '11:00:00',
    CONCAT('E', LPAD(100 + ROW_NUMBER() OVER (ORDER BY p.course_id), 3, '0')),
    0
FROM (SELECT DISTINCT course_id FROM tmp_student_pool) p
ON DUPLICATE KEY UPDATE
    exam_date = VALUES(exam_date),
    start_time = VALUES(start_time),
    end_time = VALUES(end_time),
    exam_room = VALUES(exam_room),
    is_deleted = 0;

INSERT INTO stu_evaluation(student_id, course_id, semester, eval_score, eval_comment, is_deleted)
SELECT
    p.student_id,
    t.course_id,
    @sem,
    86 + MOD(p.student_id + t.course_id, 10),
    '课堂节奏清晰，案例实用。',
    0
FROM tmp_pick p
JOIN edu_teaching t ON t.id = p.teaching_id
WHERE p.student_id IN (@stu1, @stu2)
ON DUPLICATE KEY UPDATE
    eval_score = VALUES(eval_score),
    eval_comment = VALUES(eval_comment),
    is_deleted = 0;

-- ------------------------------------------------------------
-- 6) 与教师端对齐：同步当前学期教学班人数与状态
-- ------------------------------------------------------------
UPDATE edu_teaching t
SET t.enrolled_count = (
        SELECT COUNT(*)
        FROM stu_selection s
        WHERE s.teaching_id = t.id
          AND s.deleted_at = 0
          AND s.is_deleted = 0
    ),
    t.status = CASE
        WHEN (
            SELECT COUNT(*)
            FROM stu_selection s
            WHERE s.teaching_id = t.id
              AND s.deleted_at = 0
              AND s.is_deleted = 0
        ) >= t.max_count THEN 'FULL'
        ELSE 'OPEN'
    END
WHERE t.semester = @sem
  AND t.is_deleted = 0;

COMMIT;

-- ============================================================
-- 验证输出
-- ============================================================
SELECT 'stu_selection(stu001)' AS item, COUNT(*) AS cnt
FROM stu_selection s
WHERE s.student_id = @stu1 AND s.deleted_at = 0 AND s.is_deleted = 0
UNION ALL
SELECT 'stu_selection(stu002)', COUNT(*)
FROM stu_selection s
WHERE s.student_id = @stu2 AND s.deleted_at = 0 AND s.is_deleted = 0
UNION ALL
SELECT 'stu_waiting(stu001)', COUNT(*)
FROM stu_waiting_list w
WHERE w.student_id = @stu1 AND w.deleted_at = 0 AND w.is_deleted = 0
UNION ALL
SELECT 'exam_schedule(pool)', COUNT(*)
FROM stu_exam_schedule e
WHERE e.semester = @sem AND e.is_deleted = 0
  AND e.course_id IN (SELECT DISTINCT course_id FROM tmp_student_pool)
UNION ALL
SELECT 'evaluation(stu001+stu002)', COUNT(*)
FROM stu_evaluation v
WHERE v.semester = @sem AND v.is_deleted = 0
  AND v.student_id IN (@stu1, @stu2);
