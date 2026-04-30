USE my_db_project;

START TRANSACTION;

-- ============================================================
-- 1) 课程定义: edu_courses (8 条)
-- ============================================================
INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS107', '软件工程实践', 3.0, d.id, '需求分析、设计建模、测试与交付'
FROM base_dept d
WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE
    course_name = VALUES(course_name),
    credits = VALUES(credits),
    dept_id = VALUES(dept_id),
    description = VALUES(description),
    is_deleted = 0;

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS108', '分布式系统基础', 3.0, d.id, '一致性、复制、容错与服务治理'
FROM base_dept d
WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE
    course_name = VALUES(course_name),
    credits = VALUES(credits),
    dept_id = VALUES(dept_id),
    description = VALUES(description),
    is_deleted = 0;

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS109', '数据库性能优化', 2.5, d.id, '索引设计、执行计划、锁与事务'
FROM base_dept d
WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE
    course_name = VALUES(course_name),
    credits = VALUES(credits),
    dept_id = VALUES(dept_id),
    description = VALUES(description),
    is_deleted = 0;

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS110', '数据可视化', 2.0, d.id, '可视化编码、图表设计与交互分析'
FROM base_dept d
WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE
    course_name = VALUES(course_name),
    credits = VALUES(credits),
    dept_id = VALUES(dept_id),
    description = VALUES(description),
    is_deleted = 0;

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'MA202', '离散数学进阶', 3.0, d.id, '图论、组合数学与逻辑推理'
FROM base_dept d
WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE
    course_name = VALUES(course_name),
    credits = VALUES(credits),
    dept_id = VALUES(dept_id),
    description = VALUES(description),
    is_deleted = 0;

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'MA203', '概率统计与数据分析', 3.0, d.id, '概率分布、参数估计、回归分析'
FROM base_dept d
WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE
    course_name = VALUES(course_name),
    credits = VALUES(credits),
    dept_id = VALUES(dept_id),
    description = VALUES(description),
    is_deleted = 0;

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS111', '云原生应用开发', 2.5, d.id, '容器化、服务编排与持续交付'
FROM base_dept d
WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE
    course_name = VALUES(course_name),
    credits = VALUES(credits),
    dept_id = VALUES(dept_id),
    description = VALUES(description),
    is_deleted = 0;

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS112', '人工智能导论', 3.0, d.id, '搜索、机器学习基础与案例实践'
FROM base_dept d
WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE
    course_name = VALUES(course_name),
    credits = VALUES(credits),
    dept_id = VALUES(dept_id),
    description = VALUES(description),
    is_deleted = 0;

-- ============================================================
-- 2) 教学班: edu_teaching (12 条, 2024-2)
--    采用“更新已有 + 插入缺失”保证幂等
-- ============================================================
DROP TEMPORARY TABLE IF EXISTS tmp_mock_teaching;
CREATE TEMPORARY TABLE tmp_mock_teaching (
    course_code       VARCHAR(20)  NOT NULL,
    teacher_username  VARCHAR(50)  NOT NULL,
    classroom         VARCHAR(50)  NOT NULL,
    timeslot          VARCHAR(100) NOT NULL,
    semester          VARCHAR(20)  NOT NULL,
    max_count         INT          NOT NULL,
    enrolled_count    INT          NOT NULL,
    status            VARCHAR(20)  NOT NULL
) ENGINE=MEMORY;

INSERT INTO tmp_mock_teaching (course_code, teacher_username, classroom, timeslot, semester, max_count, enrolled_count, status) VALUES
('CS107', 'teacher01', 'D501', '周一3-4节,周三3-4节', '2024-2', 60, 20, 'OPEN'),
('CS108', 'teacher01', 'D502', '周二1-2节,周四1-2节', '2024-2', 55, 18, 'OPEN'),
('CS109', 'teacher02', 'D503', '周二3-4节,周四3-4节', '2024-2', 50, 17, 'OPEN'),
('CS110', 'teacher02', 'D504', '周五1-2节',           '2024-2', 45, 16, 'OPEN'),
('MA202', 'teacher01', 'A301', '周一7-8节',           '2024-2', 50, 15, 'OPEN'),
('MA203', 'teacher02', 'A302', '周三7-8节',           '2024-2', 48, 15, 'OPEN'),
('CS111', 'teacher01', 'E201', '周四7-8节',           '2024-2', 60, 19, 'OPEN'),
('CS112', 'teacher02', 'E202', '周五3-4节',           '2024-2', 58, 18, 'OPEN'),
('CS107', 'teacher02', 'D505', '周二7-8节',           '2024-2', 52, 14, 'OPEN'),
('CS108', 'teacher02', 'D506', '周三1-2节',           '2024-2', 56, 14, 'OPEN'),
('CS109', 'teacher01', 'D507', '周五7-8节',           '2024-2', 50, 13, 'FULL'),
('CS112', 'teacher01', 'E203', '周一1-2节',           '2024-2', 60, 20, 'OPEN');

UPDATE edu_teaching t
JOIN edu_courses c ON t.course_id = c.id
JOIN sys_users u ON t.teacher_id = u.id
JOIN tmp_mock_teaching m
  ON m.course_code = c.course_code
 AND m.teacher_username = u.username
 AND m.semester = t.semester
 AND m.timeslot = t.timeslot
SET
    t.classroom = m.classroom,
    t.max_count = m.max_count,
    t.enrolled_count = m.enrolled_count,
    t.status = m.status,
    t.is_deleted = 0
WHERE t.is_deleted = 0;

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status)
SELECT c.id, u.id, m.classroom, m.timeslot, m.semester, m.max_count, m.enrolled_count, m.status
FROM tmp_mock_teaching m
JOIN edu_courses c ON c.course_code = m.course_code AND c.is_deleted = 0
JOIN sys_users u ON u.username = m.teacher_username AND u.is_deleted = 0
LEFT JOIN edu_teaching t
  ON t.course_id = c.id
 AND t.teacher_id = u.id
 AND t.semester = m.semester
 AND t.timeslot = m.timeslot
 AND t.is_deleted = 0
WHERE t.id IS NULL;

-- 目标学生: 20 名
DROP TEMPORARY TABLE IF EXISTS tmp_mock_students;
CREATE TEMPORARY TABLE tmp_mock_students (
    student_id INT PRIMARY KEY
) ENGINE=MEMORY;

INSERT INTO tmp_mock_students (student_id)
SELECT u.id
FROM sys_users u
WHERE u.role_id = 3 AND u.is_deleted = 0
ORDER BY u.username
LIMIT 20;

-- 目标教学班: 本脚本定义课程在 2024-2 的所有班级（最多 12）
DROP TEMPORARY TABLE IF EXISTS tmp_mock_teaching_ids;
CREATE TEMPORARY TABLE tmp_mock_teaching_ids (
    teaching_id INT PRIMARY KEY
) ENGINE=MEMORY;

INSERT INTO tmp_mock_teaching_ids (teaching_id)
SELECT t.id
FROM edu_teaching t
JOIN edu_courses c ON t.course_id = c.id
WHERE t.semester = '2024-2'
  AND t.is_deleted = 0
  AND c.course_code IN ('CS107','CS108','CS109','CS110','MA202','MA203','CS111','CS112')
ORDER BY t.id
LIMIT 12;

-- ============================================================
-- 3) 成绩: edu_grades (约 20 x 12 = 240 条)
-- ============================================================
DROP TEMPORARY TABLE IF EXISTS tmp_mock_grades;
CREATE TEMPORARY TABLE tmp_mock_grades (
    student_id  INT NOT NULL,
    teaching_id INT NOT NULL,
    exam_score  DECIMAL(5,2) NOT NULL,
    score       DECIMAL(5,2) NOT NULL,
    PRIMARY KEY (student_id, teaching_id)
) ENGINE=MEMORY;

INSERT INTO tmp_mock_grades (student_id, teaching_id, exam_score, score)
SELECT
    s.student_id,
    t.teaching_id,
    ROUND(55 + MOD(s.student_id * 17 + t.teaching_id * 13, 44) + MOD(s.student_id + t.teaching_id, 100) / 100, 2) AS exam_score,
    ROUND(
        LEAST(
            100,
            (55 + MOD(s.student_id * 17 + t.teaching_id * 13, 44) + MOD(s.student_id + t.teaching_id, 100) / 100) * 0.70
            + (18 + MOD(s.student_id * 5 + t.teaching_id * 3, 13))
        ),
        2
    ) AS score
FROM tmp_mock_students s
CROSS JOIN tmp_mock_teaching_ids t;

UPDATE edu_grades g
JOIN tmp_mock_grades m
    ON g.student_id = m.student_id
 AND g.teaching_id = m.teaching_id
SET
        g.exam_score = m.exam_score,
        g.score = m.score,
        g.is_deleted = 0;

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT m.student_id, m.teaching_id, m.exam_score, m.score
FROM tmp_mock_grades m
LEFT JOIN edu_grades g
    ON g.student_id = m.student_id
 AND g.teaching_id = m.teaching_id
WHERE g.id IS NULL;

-- ============================================================
-- 4) 日常记录: edu_daily_records (3 班 x 20 人 x 13 次 = 780 条)
-- ============================================================
DROP TEMPORARY TABLE IF EXISTS tmp_daily_teachings;
CREATE TEMPORARY TABLE tmp_daily_teachings (
    teaching_id INT PRIMARY KEY
) ENGINE=MEMORY;

INSERT INTO tmp_daily_teachings (teaching_id)
SELECT teaching_id
FROM tmp_mock_teaching_ids
ORDER BY teaching_id
LIMIT 3;

DROP TEMPORARY TABLE IF EXISTS tmp_daily_events;
CREATE TEMPORARY TABLE tmp_daily_events (
    event_idx   INT PRIMARY KEY,
    day_offset  INT NOT NULL,
    record_type ENUM('SIGNIN','HOMEWORK','CHAPTER_TEST') NOT NULL
) ENGINE=MEMORY;

INSERT INTO tmp_daily_events (event_idx, day_offset, record_type) VALUES
(1,   0, 'SIGNIN'),
(2,   7, 'SIGNIN'),
(3,  14, 'SIGNIN'),
(4,  21, 'SIGNIN'),
(5,  28, 'SIGNIN'),
(6,  35, 'SIGNIN'),
(7,   2, 'HOMEWORK'),
(8,   9, 'HOMEWORK'),
(9,  16, 'HOMEWORK'),
(10, 23, 'HOMEWORK'),
(11, 10, 'CHAPTER_TEST'),
(12, 24, 'CHAPTER_TEST'),
(13, 38, 'CHAPTER_TEST');

DROP TEMPORARY TABLE IF EXISTS tmp_mock_daily_records;
CREATE TEMPORARY TABLE tmp_mock_daily_records (
    teaching_id  INT NOT NULL,
    student_id   INT NOT NULL,
    record_date  DATE NOT NULL,
    record_type  ENUM('SIGNIN','HOMEWORK','CHAPTER_TEST') NOT NULL,
    completed    TINYINT NOT NULL,
    note         VARCHAR(200) NULL,
    PRIMARY KEY (teaching_id, student_id, record_date, record_type)
) ENGINE=MEMORY;

INSERT INTO tmp_mock_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT
    dt.teaching_id,
    s.student_id,
    DATE_ADD('2024-09-02', INTERVAL e.day_offset DAY) AS record_date,
    e.record_type,
    CASE
        WHEN MOD(dt.teaching_id + s.student_id + e.event_idx, 100) < 85 THEN 1
        ELSE 0
    END AS completed,
    CASE e.record_type
        WHEN 'SIGNIN' THEN
            CASE
                WHEN MOD(dt.teaching_id + s.student_id + e.event_idx, 100) < 85 THEN NULL
                ELSE '缺勤'
            END
        WHEN 'HOMEWORK' THEN
            CASE
                WHEN MOD(dt.teaching_id + s.student_id + e.event_idx, 100) < 85 THEN '按时提交'
                ELSE '未交'
            END
        WHEN 'CHAPTER_TEST' THEN
            CASE
                WHEN MOD(dt.teaching_id + s.student_id + e.event_idx, 100) < 85
                    THEN CONCAT(CAST(65 + MOD(dt.teaching_id * 11 + s.student_id * 7 + e.event_idx * 3, 34) AS CHAR), '分')
                ELSE '缺考'
            END
        ELSE NULL
    END AS note
FROM tmp_daily_teachings dt
CROSS JOIN tmp_mock_students s
CROSS JOIN tmp_daily_events e;

UPDATE edu_daily_records dr
JOIN tmp_mock_daily_records m
    ON dr.teaching_id = m.teaching_id
 AND dr.student_id = m.student_id
 AND dr.record_date = m.record_date
 AND dr.record_type = m.record_type
SET
        dr.completed = m.completed,
        dr.note = m.note,
        dr.is_deleted = 0;

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT m.teaching_id, m.student_id, m.record_date, m.record_type, m.completed, m.note
FROM tmp_mock_daily_records m
LEFT JOIN edu_daily_records dr
    ON dr.teaching_id = m.teaching_id
 AND dr.student_id = m.student_id
 AND dr.record_date = m.record_date
 AND dr.record_type = m.record_type
WHERE dr.id IS NULL;

-- ============================================================
-- 5) 调课申请: edu_schedule_change_req (6 条)
-- ============================================================
DROP TEMPORARY TABLE IF EXISTS tmp_mock_req;
CREATE TEMPORARY TABLE tmp_mock_req (
    course_code      VARCHAR(20)  NOT NULL,
    original_time    VARCHAR(100) NOT NULL,
    requested_time   VARCHAR(100) NOT NULL,
    reason           VARCHAR(500) NOT NULL,
    status           ENUM('PENDING','APPROVED','REJECTED') NOT NULL,
    admin_comment    VARCHAR(300) NULL
) ENGINE=MEMORY;

INSERT INTO tmp_mock_req (course_code, original_time, requested_time, reason, status, admin_comment) VALUES
('CS107', '周一3-4节,周三3-4节', '周五5-6节',       '[MOCK-2024-2-01] 教研活动冲突，申请顺延', 'PENDING',  NULL),
('CS108', '周二1-2节,周四1-2节', '周二3-4节,周四3-4节', '[MOCK-2024-2-02] 教室临时占用，申请换时段', 'APPROVED', '同意，已协调空教室'),
('CS109', '周二3-4节,周四3-4节', '周三3-4节,周五3-4节', '[MOCK-2024-2-03] 课程竞赛辅导冲突', 'REJECTED', '与其他核心课冲突，驳回'),
('CS110', '周五1-2节',           '周四5-6节',       '[MOCK-2024-2-04] 校级活动占用教室', 'PENDING',  NULL),
('CS111', '周四7-8节',           '周二7-8节',       '[MOCK-2024-2-05] 教学观摩安排调整', 'APPROVED', '同意，注意通知学生'),
('CS112', '周五3-4节',           '周三5-6节',       '[MOCK-2024-2-06] 与实验课时间重叠', 'REJECTED', '当前排课资源不足，暂不通过');

-- 先更新已有（按 teaching_id + reason 定位）
UPDATE edu_schedule_change_req r
JOIN edu_teaching t ON r.teaching_id = t.id AND t.is_deleted = 0
JOIN edu_courses c ON t.course_id = c.id AND c.is_deleted = 0
JOIN tmp_mock_req q
  ON q.course_code = c.course_code
 AND q.original_time = t.timeslot
 AND t.semester = '2024-2'
SET
    r.original_time = q.original_time,
    r.requested_time = q.requested_time,
    r.status = q.status,
    r.admin_comment = CASE WHEN q.status = 'PENDING' THEN NULL ELSE q.admin_comment END,
    r.processed_by = CASE
        WHEN q.status = 'PENDING' THEN NULL
        ELSE (SELECT id FROM sys_users WHERE role_id = 1 AND is_deleted = 0 ORDER BY id LIMIT 1)
    END,
    r.is_deleted = 0
WHERE r.reason = q.reason;

-- 插入缺失
INSERT INTO edu_schedule_change_req
(teaching_id, teacher_id, reason, original_time, requested_time, status, admin_comment, processed_by)
SELECT
    t.id,
    t.teacher_id,
    q.reason,
    q.original_time,
    q.requested_time,
    q.status,
    CASE WHEN q.status = 'PENDING' THEN NULL ELSE q.admin_comment END,
    CASE
        WHEN q.status = 'PENDING' THEN NULL
        ELSE (SELECT id FROM sys_users WHERE role_id = 1 AND is_deleted = 0 ORDER BY id LIMIT 1)
    END
FROM tmp_mock_req q
JOIN edu_courses c ON c.course_code = q.course_code AND c.is_deleted = 0
JOIN edu_teaching t
  ON t.course_id = c.id
 AND t.semester = '2024-2'
 AND t.timeslot = q.original_time
 AND t.is_deleted = 0
WHERE NOT EXISTS (
    SELECT 1
    FROM edu_schedule_change_req r
    WHERE r.teaching_id = t.id
      AND r.reason = q.reason
      AND r.is_deleted = 0
);

COMMIT;

-- ============================================================
-- 验证统计
-- ============================================================
SELECT 'edu_courses' AS table_name, COUNT(*) AS total_rows FROM edu_courses WHERE is_deleted = 0
UNION ALL
SELECT 'edu_teaching_2024_2', COUNT(*) FROM edu_teaching WHERE semester = '2024-2' AND is_deleted = 0
UNION ALL
SELECT 'edu_grades_mock_courses', COUNT(*)
FROM edu_grades g
JOIN edu_teaching t ON g.teaching_id = t.id
JOIN edu_courses c ON t.course_id = c.id
WHERE t.semester = '2024-2'
  AND c.course_code IN ('CS107','CS108','CS109','CS110','MA202','MA203','CS111','CS112')
  AND g.is_deleted = 0
UNION ALL
SELECT 'edu_daily_records_mock_courses', COUNT(*)
FROM edu_daily_records dr
JOIN edu_teaching t ON dr.teaching_id = t.id
JOIN edu_courses c ON t.course_id = c.id
WHERE t.semester = '2024-2'
  AND c.course_code IN ('CS107','CS108','CS109','CS110','MA202','MA203','CS111','CS112')
  AND dr.is_deleted = 0
UNION ALL
SELECT 'edu_schedule_change_req_mock', COUNT(*)
FROM edu_schedule_change_req r
WHERE r.reason LIKE '[MOCK-2024-2-%'
  AND r.is_deleted = 0;
