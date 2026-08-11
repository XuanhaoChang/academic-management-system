USE my_db_project;

SET @sem = (
    SELECT config_value
    FROM sys_config
    WHERE config_key='current_semester' AND is_deleted=0
    LIMIT 1
);

SET @demo_dept_id = (
    SELECT id
    FROM base_dept
    WHERE is_deleted = 0
    ORDER BY id
    LIMIT 1
);

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description, is_deleted)
SELECT 'CS105', '计算机网络', 3.0, @demo_dept_id, '网络基础与协议分析', 0
WHERE @demo_dept_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_courses c
      WHERE c.course_code = 'CS105'
  );

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description, is_deleted)
SELECT 'CS106', 'Web开发技术', 3.0, @demo_dept_id, '前后端开发基础', 0
WHERE @demo_dept_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_courses c
      WHERE c.course_code = 'CS106'
  );

-- 高等数学（与管理员端课程库同步）
SET @math_dept_id = (
    SELECT id
    FROM base_dept
    WHERE dept_code = 'MA' AND is_deleted = 0
    LIMIT 1
);
SET @math_dept_id = IFNULL(@math_dept_id, @demo_dept_id);

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description, is_deleted)
SELECT 'MA201', '高等数学', 4.0, @math_dept_id, '微积分基础理论', 0
WHERE @math_dept_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_courses c
      WHERE c.course_code = 'MA201'
  );

-- ------------------------------------------------------------
-- A. 清理重复记录（解决“选课记录重复”）
-- ------------------------------------------------------------
DELETE s1
FROM stu_selection s1
JOIN stu_selection s2
  ON s1.student_id = s2.student_id
 AND s1.teaching_id = s2.teaching_id
 AND s1.deleted_at = s2.deleted_at
 AND s1.id > s2.id;

DELETE w1
FROM stu_waiting_list w1
JOIN stu_waiting_list w2
  ON w1.student_id = w2.student_id
 AND w1.teaching_id = w2.teaching_id
 AND w1.deleted_at = w2.deleted_at
 AND w1.id > w2.id;

SET @demo_student_id = (
    SELECT id
    FROM sys_users
    WHERE username = 'stu001' AND role_id = 3 AND is_deleted = 0
    LIMIT 1
);

-- 将所有学生同步到 stu_info（不存在时插入）
INSERT INTO stu_info(student_id, grade_year, class_name, phone, email, is_deleted)
SELECT
    u.id,
    2024,
    CONCAT('计科', LPAD((u.id % 4) + 1, 2, '0'), '班'),
    CONCAT('1380000', LPAD(u.id, 4, '0')),
    CONCAT(u.username, '@campus.edu'),
    0
FROM sys_users u
WHERE u.role_id = 3 AND u.is_deleted = 0
  AND NOT EXISTS (SELECT 1 FROM stu_info si WHERE si.student_id = u.id);

-- 先修课关系（可演示“先修课未修不允许选课”）
INSERT IGNORE INTO stu_course_prereq(course_id, pre_course_id, is_deleted)
SELECT c2.id, c1.id, 0
FROM edu_courses c1, edu_courses c2
WHERE c1.course_code='CS102' AND c2.course_code='CS103';

INSERT IGNORE INTO stu_course_prereq(course_id, pre_course_id, is_deleted)
SELECT c2.id, c1.id, 0
FROM edu_courses c1, edu_courses c2
WHERE c1.course_code='CS103' AND c2.course_code='CS104';

INSERT INTO stu_exam_schedule(course_id, semester, exam_date, start_time, end_time, exam_room, is_deleted)
SELECT
    t.course_id,
    t.semester,
    DATE_ADD(CURDATE(), INTERVAL (ROW_NUMBER() OVER (ORDER BY t.course_id)) DAY),
    '09:00:00',
    '11:00:00',
    CONCAT('E', LPAD((t.course_id % 20) + 100, 3, '0')),
    0
FROM edu_teaching t
WHERE t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
  AND t.is_deleted = 0
ON DUPLICATE KEY UPDATE
    exam_date = VALUES(exam_date),
    start_time = VALUES(start_time),
    end_time = VALUES(end_time),
    exam_room = VALUES(exam_room),
    is_deleted = 0;

-- 初始化一些评教数据
INSERT INTO stu_evaluation(student_id, course_id, semester, eval_score, eval_comment, is_deleted)
SELECT
    u.id,
    c.id,
    @sem,
    88,
    '课堂节奏合理，案例充足',
    0
FROM sys_users u
JOIN edu_courses c ON c.course_code = 'CS101'
WHERE u.username IN ('stu001', 'stu002')
ON DUPLICATE KEY UPDATE eval_score = VALUES(eval_score), eval_comment = VALUES(eval_comment), is_deleted = 0;

-- ------------------------------------------------------------
-- B. 为当前演示学生预置几门已选课程
-- 说明：先清理 stu001 历史选课/候补，再重建演示数据
-- ------------------------------------------------------------
DELETE FROM stu_selection
WHERE student_id = @demo_student_id
;

DELETE FROM stu_waiting_list
WHERE student_id = @demo_student_id
;

SET @demo_teacher_id2 = (
    SELECT id
    FROM sys_users
    WHERE role_id = 2 AND is_deleted = 0
    ORDER BY id
    LIMIT 1
);

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @demo_teacher_id2, 'A301', '周一1-2节', @sem, 40, 0, 'OPEN', 0
FROM edu_courses c
WHERE c.course_code = 'CS101'
  AND c.is_deleted = 0
  AND @demo_teacher_id2 IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM edu_teaching t
      WHERE t.course_id = c.id
        AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
        AND t.is_deleted = 0
  );

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @demo_teacher_id2, 'A302', '周二3-4节', @sem, 35, 0, 'OPEN', 0
FROM edu_courses c
WHERE c.course_code = 'CS102'
  AND c.is_deleted = 0
  AND @demo_teacher_id2 IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM edu_teaching t
      WHERE t.course_id = c.id
        AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
        AND t.is_deleted = 0
  );

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @demo_teacher_id2, 'A303', '周四1-2节', @sem, 30, 0, 'OPEN', 0
FROM edu_courses c
WHERE c.course_code = 'CS105'
  AND c.is_deleted = 0
  AND @demo_teacher_id2 IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM edu_teaching t
      WHERE t.course_id = c.id
        AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
        AND t.is_deleted = 0
  );

SET @math_teacher_id = (
    SELECT id
    FROM sys_users
    WHERE username = 'teacher02' AND role_id = 2 AND is_deleted = 0
    LIMIT 1
);
SET @math_teacher_id = IFNULL(@math_teacher_id, @demo_teacher_id2);

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @math_teacher_id, 'A201', '周二1-2节,周四1-2节', @sem, 60, 0, 'OPEN', 0
FROM edu_courses c
WHERE c.course_code = 'MA201'
  AND c.is_deleted = 0
  AND @math_teacher_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM edu_teaching t
      WHERE t.course_id = c.id
        AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
        AND t.is_deleted = 0
  );

-- 给 stu001 预置 3 门“已选课程”
INSERT IGNORE INTO stu_selection(student_id, teaching_id, deleted_at)
SELECT @demo_student_id, t.id, 0
FROM edu_courses c
JOIN edu_teaching t ON t.course_id = c.id
                   AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
                   AND t.is_deleted = 0
WHERE @demo_student_id IS NOT NULL
  AND c.course_code IN ('CS101', 'CS102', 'CS105', 'MA201')
  AND c.is_deleted = 0;

-- ------------------------------------------------------------
-- C. 构造“容量已满 -> 候补队列”的演示场景（仍使用现有学生）
-- 目标课程：CS106（容量设置为 2）
-- 结果：2 人已选，stu001 在候补队列
-- ------------------------------------------------------------
SET @demo_course_id = (
    SELECT id FROM edu_courses
    WHERE course_code = 'CS106' AND is_deleted = 0
    LIMIT 1
);

SET @demo_teacher_id = (
    SELECT id FROM sys_users
    WHERE role_id = 2 AND is_deleted = 0
    ORDER BY id
    LIMIT 1
);

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT @demo_course_id, @demo_teacher_id, 'B201', '周五1-2节', @sem, 2, 0, 'OPEN', 0
WHERE @demo_course_id IS NOT NULL
  AND @demo_teacher_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM edu_teaching t
    JOIN edu_courses c2 ON c2.id = t.course_id
    WHERE c2.course_code = 'CS106'
      AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
      AND t.is_deleted = 0
      AND c2.is_deleted = 0
  );

SET @demo_teaching_id = (
    SELECT t.id
    FROM edu_teaching t
    JOIN edu_courses c ON c.id = t.course_id
    WHERE c.course_code = 'CS106'
      AND semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
      AND t.is_deleted = 0
      AND c.is_deleted = 0
    ORDER BY t.id DESC
    LIMIT 1
);

UPDATE edu_teaching
SET max_count = 2
WHERE id = @demo_teaching_id;

-- 清空该演示课程当前学期的已选/候补，保证每次重跑结果一致
DELETE FROM stu_selection
WHERE teaching_id = @demo_teaching_id
;

DELETE FROM stu_waiting_list
WHERE teaching_id = @demo_teaching_id
;

-- 2 名已有学生占满名额（动态选取，避免依赖固定账号）
INSERT IGNORE INTO stu_selection(student_id, teaching_id, deleted_at)
SELECT u.id, @demo_teaching_id, 0
FROM sys_users u
WHERE u.role_id = 3
  AND u.id <> @demo_student_id
  AND u.is_deleted = 0
ORDER BY u.id
LIMIT 2;

-- 候补队列：stu001 固定排 1
INSERT IGNORE INTO stu_waiting_list(student_id, teaching_id, queue_no, deleted_at)
SELECT @demo_student_id, @demo_teaching_id, 1, 0
WHERE @demo_student_id IS NOT NULL
  AND @demo_teaching_id IS NOT NULL;

-- 候补队列补 2 人（排 2/3），同样动态选取
INSERT IGNORE INTO stu_waiting_list(student_id, teaching_id, queue_no, deleted_at)
SELECT x.student_id, @demo_teaching_id, x.queue_no, 0
FROM (
    SELECT
        u.id AS student_id,
        ROW_NUMBER() OVER (ORDER BY u.id) + 1 AS queue_no
    FROM sys_users u
    WHERE u.role_id = 3
      AND u.id <> @demo_student_id
      AND u.is_deleted = 0
      AND NOT EXISTS (
          SELECT 1
          FROM stu_selection s
          WHERE s.student_id = u.id
        AND s.teaching_id = @demo_teaching_id
            AND s.deleted_at = 0
      )
    LIMIT 2
) x;

UPDATE edu_teaching t
SET t.enrolled_count = (
        SELECT COUNT(*)
        FROM stu_selection s
        WHERE s.teaching_id = t.id
          AND s.deleted_at = 0
    ),
    t.status = CASE
        WHEN (
            SELECT COUNT(*)
            FROM stu_selection s
            WHERE s.teaching_id = t.id
              AND s.deleted_at = 0
        ) >= t.max_count THEN 'FULL'
        ELSE 'OPEN'
    END
WHERE t.id = @demo_teaching_id;

-- 同步当前学期所有课程人数，保证“我的已选课程”与容量状态一致
UPDATE edu_teaching t
SET t.enrolled_count = (
        SELECT COUNT(*)
        FROM stu_selection s
        WHERE s.teaching_id = t.id
          AND s.deleted_at = 0
    ),
    t.status = CASE
        WHEN (
            SELECT COUNT(*)
            FROM stu_selection s
            WHERE s.teaching_id = t.id
              AND s.deleted_at = 0
        ) >= t.max_count THEN 'FULL'
        ELSE 'OPEN'
    END
WHERE t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
  AND t.is_deleted = 0;

SET @tid_cs102_2024_2 = ( -- D. 补充 2024-2 CS102 成绩
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS102'
      AND t.semester COLLATE utf8mb4_unicode_ci = '2024-2'
      AND t.is_deleted = 0
    LIMIT 1
);

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @demo_teacher_id2, 'A302', '周二3-4节', '2024-2', 35, 0, 'OPEN', 0
FROM edu_courses c
WHERE c.course_code = 'CS102' AND c.is_deleted = 0
  AND @demo_teacher_id2 IS NOT NULL
  AND @tid_cs102_2024_2 IS NULL;

SET @tid_cs102_2024_2 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS102'
      AND t.semester COLLATE utf8mb4_unicode_ci = '2024-2'
      AND t.is_deleted = 0
    LIMIT 1
);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT
    u.id,
    @tid_cs102_2024_2,
    CASE u.username
        WHEN 'stu001' THEN 79.0
        WHEN 'stu002' THEN 86.0
        WHEN 'stu003' THEN 44.0
        WHEN 'stu004' THEN 72.0
        WHEN 'stu005' THEN 63.0
        WHEN 'stu006' THEN 90.5
        WHEN 'stu007' THEN 77.0
        WHEN 'stu008' THEN 51.0
        WHEN 'stu009' THEN 83.5
        WHEN 'stu010' THEN 80.0
    END,
    CASE u.username
        WHEN 'stu001' THEN 78.2
        WHEN 'stu002' THEN 84.0
        WHEN 'stu003' THEN 47.3
        WHEN 'stu004' THEN 71.5
        WHEN 'stu005' THEN 62.8
        WHEN 'stu006' THEN 88.6
        WHEN 'stu007' THEN 76.4
        WHEN 'stu008' THEN 53.1
        WHEN 'stu009' THEN 81.9
        WHEN 'stu010' THEN 79.0
    END
FROM sys_users u
WHERE u.username IN ('stu001','stu002','stu003','stu004','stu005',
                     'stu006','stu007','stu008','stu009','stu010')
  AND @tid_cs102_2024_2 IS NOT NULL
ON DUPLICATE KEY UPDATE
    exam_score   = VALUES(exam_score),
    score        = VALUES(score);

SET @hist_teacher_id = ( -- E. 2024-1 历史授课 + 成绩
    SELECT id FROM sys_users
    WHERE role_id = 2 AND is_deleted = 0
    ORDER BY id
    LIMIT 1
);

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @hist_teacher_id, 'A201', '周一1-2节', '2024-1', 50, 0, 'CLOSED', 0
FROM edu_courses c
WHERE c.course_code = 'CS101' AND c.is_deleted = 0
  AND @hist_teacher_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_teaching t
      WHERE t.course_id = c.id
        AND t.semester COLLATE utf8mb4_unicode_ci = '2024-1'
        AND t.is_deleted = 0
  );

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @hist_teacher_id, 'A202', '周三3-4节', '2024-1', 40, 0, 'CLOSED', 0
FROM edu_courses c
WHERE c.course_code = 'CS102' AND c.is_deleted = 0
  AND @hist_teacher_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_teaching t
      WHERE t.course_id = c.id
        AND t.semester COLLATE utf8mb4_unicode_ci = '2024-1'
        AND t.is_deleted = 0
  );

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @hist_teacher_id, 'B301', '周二5-6节,周四5-6节', '2024-1', 60, 0, 'CLOSED', 0
FROM edu_courses c
WHERE c.course_code = 'CS103' AND c.is_deleted = 0
  AND @hist_teacher_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_teaching t
      WHERE t.course_id = c.id
        AND t.semester COLLATE utf8mb4_unicode_ci = '2024-1'
        AND t.is_deleted = 0
  );

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @hist_teacher_id, 'B201', '周一3-4节,周五3-4节', '2024-1', 80, 0, 'CLOSED', 0
FROM edu_courses c
WHERE c.course_code = 'MA201' AND c.is_deleted = 0
  AND @hist_teacher_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_teaching t
      WHERE t.course_id = c.id
        AND t.semester COLLATE utf8mb4_unicode_ci = '2024-1'
        AND t.is_deleted = 0
  );

SET @tid_cs101_2024_1 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS101'
      AND t.semester COLLATE utf8mb4_unicode_ci = '2024-1'
      AND t.is_deleted = 0 LIMIT 1
);

SET @tid_cs102_2024_1 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS102'
      AND t.semester COLLATE utf8mb4_unicode_ci = '2024-1'
      AND t.is_deleted = 0 LIMIT 1
);

SET @tid_cs103_2024_1 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS103'
      AND t.semester COLLATE utf8mb4_unicode_ci = '2024-1'
      AND t.is_deleted = 0 LIMIT 1
);

SET @tid_ma201_2024_1 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'MA201'
      AND t.semester COLLATE utf8mb4_unicode_ci = '2024-1'
      AND t.is_deleted = 0 LIMIT 1
);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs101_2024_1, 76.0, 75.2
FROM sys_users u WHERE u.username = 'stu001' AND @tid_cs101_2024_1 IS NOT NULL
ON DUPLICATE KEY UPDATE exam_score=VALUES(exam_score), score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs102_2024_1, 82.0, 81.0
FROM sys_users u WHERE u.username = 'stu001' AND @tid_cs102_2024_1 IS NOT NULL
ON DUPLICATE KEY UPDATE exam_score=VALUES(exam_score), score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs103_2024_1, 70.0, 71.5
FROM sys_users u WHERE u.username = 'stu001' AND @tid_cs103_2024_1 IS NOT NULL
ON DUPLICATE KEY UPDATE exam_score=VALUES(exam_score), score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_ma201_2024_1, 88.5, 87.0
FROM sys_users u WHERE u.username = 'stu001' AND @tid_ma201_2024_1 IS NOT NULL
ON DUPLICATE KEY UPDATE exam_score=VALUES(exam_score), score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs101_2024_1, 90.0, 89.5
FROM sys_users u WHERE u.username = 'stu002' AND @tid_cs101_2024_1 IS NOT NULL
ON DUPLICATE KEY UPDATE exam_score=VALUES(exam_score), score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs101_2024_1, 55.0, 57.0
FROM sys_users u WHERE u.username = 'stu003' AND @tid_cs101_2024_1 IS NOT NULL
ON DUPLICATE KEY UPDATE exam_score=VALUES(exam_score), score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs102_2024_1, 88.0, 87.3
FROM sys_users u WHERE u.username = 'stu002' AND @tid_cs102_2024_1 IS NOT NULL
ON DUPLICATE KEY UPDATE exam_score=VALUES(exam_score), score=VALUES(score);

INSERT INTO stu_evaluation (student_id, course_id, semester, eval_score, eval_comment, is_deleted) -- F. 评教记录
SELECT u.id, c.id, '2024-2', 85, '讲解清晰，案例丰富，收获很多', 0
FROM sys_users u, edu_courses c
WHERE u.username = 'stu001' AND c.course_code = 'CS103'
ON DUPLICATE KEY UPDATE eval_score=VALUES(eval_score), eval_comment=VALUES(eval_comment), is_deleted=0;

INSERT INTO stu_evaluation (student_id, course_id, semester, eval_score, eval_comment, is_deleted)
SELECT u.id, c.id, '2024-2', 78, '内容较难，希望增加课后答疑时间', 0
FROM sys_users u, edu_courses c
WHERE u.username = 'stu001' AND c.course_code = 'CS104'
ON DUPLICATE KEY UPDATE eval_score=VALUES(eval_score), eval_comment=VALUES(eval_comment), is_deleted=0;

INSERT INTO stu_evaluation (student_id, course_id, semester, eval_score, eval_comment, is_deleted)
SELECT u.id, c.id, '2024-2', 92, '老师非常认真负责，课堂氛围活跃', 0
FROM sys_users u, edu_courses c
WHERE u.username = 'stu001' AND c.course_code = 'CS102'
ON DUPLICATE KEY UPDATE eval_score=VALUES(eval_score), eval_comment=VALUES(eval_comment), is_deleted=0;

INSERT INTO stu_evaluation (student_id, course_id, semester, eval_score, eval_comment, is_deleted)
SELECT u.id, c.id, '2024-2', 95, '课程内容合理，实践环节很有帮助', 0
FROM sys_users u, edu_courses c
WHERE u.username = 'stu002' AND c.course_code = 'CS101'
ON DUPLICATE KEY UPDATE eval_score=VALUES(eval_score), eval_comment=VALUES(eval_comment), is_deleted=0;

INSERT INTO stu_evaluation (student_id, course_id, semester, eval_score, eval_comment, is_deleted)
SELECT u.id, c.id, '2024-2', 90, '理论与实践结合好', 0
FROM sys_users u, edu_courses c
WHERE u.username = 'stu002' AND c.course_code = 'CS103'
ON DUPLICATE KEY UPDATE eval_score=VALUES(eval_score), eval_comment=VALUES(eval_comment), is_deleted=0;

INSERT INTO stu_exam_defer_req (student_id, course_id, semester, reason, status, is_deleted) -- G. 缓考申请
SELECT u.id, c.id, @sem, '因病住院，医院开具证明，申请缓考', 'PENDING', 0
FROM sys_users u, edu_courses c
WHERE u.username = 'stu001' AND c.course_code = 'CS105'
  AND @sem IS NOT NULL
ON DUPLICATE KEY UPDATE reason=VALUES(reason), status=VALUES(status), is_deleted=0;

INSERT INTO stu_exam_defer_req (student_id, course_id, semester, reason, status, is_deleted)
SELECT u.id, c.id, '2024-2', '参加校运动会，与考试时间冲突', 'APPROVED', 0
FROM sys_users u, edu_courses c
WHERE u.username = 'stu003' AND c.course_code = 'CS101'
ON DUPLICATE KEY UPDATE reason=VALUES(reason), status=VALUES(status), is_deleted=0;

SET @stu002_id = (SELECT id FROM sys_users WHERE username = 'stu002' AND role_id = 3 AND is_deleted = 0 LIMIT 1); -- H. 其他学生当前学期选课

SET @stu003_id = (SELECT id FROM sys_users WHERE username = 'stu003' AND role_id = 3 AND is_deleted = 0 LIMIT 1);

SET @stu004_id = (SELECT id FROM sys_users WHERE username = 'stu004' AND role_id = 3 AND is_deleted = 0 LIMIT 1);

SET @stu005_id = (SELECT id FROM sys_users WHERE username = 'stu005' AND role_id = 3 AND is_deleted = 0 LIMIT 1);

SET @stu006_id = (SELECT id FROM sys_users WHERE username = 'stu006' AND role_id = 3 AND is_deleted = 0 LIMIT 1);

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @demo_teacher_id2, 'A201', '周一1-2节', t2.semester, 50, 0, 'OPEN', 0
FROM edu_courses c
JOIN (SELECT @sem AS semester) t2
WHERE c.course_code = 'CS101' AND c.is_deleted = 0
  AND @demo_teacher_id2 IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_teaching tx
      WHERE tx.course_id = c.id
        AND tx.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
        AND tx.is_deleted = 0
  );

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @demo_teacher_id2, 'A302', '周二3-4节', t2.semester, 35, 0, 'OPEN', 0
FROM edu_courses c
JOIN (SELECT @sem AS semester) t2
WHERE c.course_code = 'CS102' AND c.is_deleted = 0
  AND @demo_teacher_id2 IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_teaching tx
      WHERE tx.course_id = c.id
        AND tx.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
        AND tx.is_deleted = 0
  );

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @demo_teacher_id2, 'D301', '周一5-6节,周三5-6节', t2.semester, 60, 0, 'OPEN', 0
FROM edu_courses c
JOIN (SELECT @sem AS semester) t2
WHERE c.course_code = 'CS103' AND c.is_deleted = 0
  AND @demo_teacher_id2 IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_teaching tx
      WHERE tx.course_id = c.id
        AND tx.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
        AND tx.is_deleted = 0
  );

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
SELECT c.id, @demo_teacher_id2, 'D401', '周二5-6节,周四5-6节', t2.semester, 50, 0, 'OPEN', 0
FROM edu_courses c
JOIN (SELECT @sem AS semester) t2
WHERE c.course_code = 'CS104' AND c.is_deleted = 0
  AND @demo_teacher_id2 IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM edu_teaching tx
      WHERE tx.course_id = c.id
        AND tx.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
        AND tx.is_deleted = 0
  );

INSERT IGNORE INTO stu_selection (student_id, teaching_id, deleted_at)
SELECT @stu002_id, t.id, 0
FROM edu_courses c
JOIN edu_teaching t ON t.course_id = c.id
  AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
  AND t.is_deleted = 0
WHERE c.course_code IN ('CS101', 'CS103') AND c.is_deleted = 0
  AND @stu002_id IS NOT NULL;

INSERT IGNORE INTO stu_selection (student_id, teaching_id, deleted_at)
SELECT @stu003_id, t.id, 0
FROM edu_courses c
JOIN edu_teaching t ON t.course_id = c.id
  AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
  AND t.is_deleted = 0
WHERE c.course_code IN ('CS102', 'MA201') AND c.is_deleted = 0
  AND @stu003_id IS NOT NULL;

INSERT IGNORE INTO stu_selection (student_id, teaching_id, deleted_at)
SELECT @stu004_id, t.id, 0
FROM edu_courses c
JOIN edu_teaching t ON t.course_id = c.id
  AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
  AND t.is_deleted = 0
WHERE c.course_code IN ('CS103', 'CS104', 'MA201') AND c.is_deleted = 0
  AND @stu004_id IS NOT NULL;

INSERT IGNORE INTO stu_selection (student_id, teaching_id, deleted_at)
SELECT @stu005_id, t.id, 0
FROM edu_courses c
JOIN edu_teaching t ON t.course_id = c.id
  AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
  AND t.is_deleted = 0
WHERE c.course_code IN ('CS101', 'CS102', 'CS105') AND c.is_deleted = 0
  AND @stu005_id IS NOT NULL;

INSERT IGNORE INTO stu_selection (student_id, teaching_id, deleted_at)
SELECT @stu006_id, t.id, 0
FROM edu_courses c
JOIN edu_teaching t ON t.course_id = c.id
  AND t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
  AND t.is_deleted = 0
WHERE c.course_code IN ('CS101', 'CS103', 'CS104') AND c.is_deleted = 0
  AND @stu006_id IS NOT NULL;

UPDATE edu_teaching t -- I. 同步当前学期 enrolled_count
SET t.enrolled_count = (
        SELECT COUNT(*)
        FROM stu_selection s
        WHERE s.teaching_id = t.id
          AND s.deleted_at = 0
    ),
    t.status = CASE
        WHEN (
            SELECT COUNT(*)
            FROM stu_selection s
            WHERE s.teaching_id = t.id
              AND s.deleted_at = 0
        ) >= t.max_count THEN 'FULL'
        ELSE 'OPEN'
    END
WHERE t.semester COLLATE utf8mb4_unicode_ci = @sem COLLATE utf8mb4_unicode_ci
  AND t.is_deleted = 0;

SET @tid_cs103_2024_1_full = ( -- J. 数据结构与算法 2024-1 完整成绩
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON c.id = t.course_id
    WHERE c.course_code = 'CS103'
      AND t.semester COLLATE utf8mb4_unicode_ci = '2024-1'
      AND t.is_deleted = 0
    LIMIT 1
);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs103_2024_1_full,
    CASE u.username
        WHEN 'stu001' THEN 82.0
        WHEN 'stu002' THEN 87.0
        WHEN 'stu003' THEN 48.0
        WHEN 'stu004' THEN 73.0
        WHEN 'stu005' THEN 66.0
        WHEN 'stu006' THEN 91.0
        WHEN 'stu007' THEN 78.0
        WHEN 'stu008' THEN 53.0
        WHEN 'stu009' THEN 86.0
        WHEN 'stu010' THEN 82.0
        WHEN 'stu011' THEN 70.0
        WHEN 'stu012' THEN 93.0
        WHEN 'stu013' THEN 46.0
        WHEN 'stu014' THEN 85.0
        WHEN 'stu015' THEN 62.0
        WHEN 'stu016' THEN 80.0
        WHEN 'stu017' THEN 73.0
        WHEN 'stu018' THEN 90.0
        WHEN 'stu019' THEN 44.0
        WHEN 'stu020' THEN 78.0
    END,
    CASE u.username
        WHEN 'stu001' THEN 84.4
        WHEN 'stu002' THEN 88.9
        WHEN 'stu003' THEN 50.6
        WHEN 'stu004' THEN 74.1
        WHEN 'stu005' THEN 67.2
        WHEN 'stu006' THEN 92.3
        WHEN 'stu007' THEN 79.4
        WHEN 'stu008' THEN 55.1
        WHEN 'stu009' THEN 87.2
        WHEN 'stu010' THEN 83.4
        WHEN 'stu011' THEN 71.0
        WHEN 'stu012' THEN 94.1
        WHEN 'stu013' THEN 49.2
        WHEN 'stu014' THEN 86.5
        WHEN 'stu015' THEN 63.4
        WHEN 'stu016' THEN 81.0
        WHEN 'stu017' THEN 74.1
        WHEN 'stu018' THEN 91.0
        WHEN 'stu019' THEN 47.8
        WHEN 'stu020' THEN 79.3
    END
FROM sys_users u
WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005',
    'stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015',
    'stu016','stu017','stu018','stu019','stu020'
)
  AND @tid_cs103_2024_1_full IS NOT NULL
ON DUPLICATE KEY UPDATE
    exam_score   = VALUES(exam_score),
    score        = VALUES(score);

UPDATE edu_teaching SET enrolled_count = 20, status = 'CLOSED'
WHERE id = @tid_cs103_2024_1_full;

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs103_2024_1_full, u.id,
    '2024-03-04', 'SIGNIN',
    CASE u.username
        WHEN 'stu003' THEN 0 WHEN 'stu008' THEN 0 WHEN 'stu013' THEN 0 ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '缺勤' WHEN 'stu008' THEN '迟到' WHEN 'stu013' THEN '请假' ELSE NULL END
FROM sys_users u
WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005',
    'stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015',
    'stu016','stu017','stu018','stu019','stu020'
)
  AND @tid_cs103_2024_1_full IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs103_2024_1_full, u.id,
    '2024-03-11', 'SIGNIN',
    CASE u.username WHEN 'stu019' THEN 0 ELSE 1 END,
    CASE u.username WHEN 'stu019' THEN '缺勤' ELSE NULL END
FROM sys_users u
WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005',
    'stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015',
    'stu016','stu017','stu018','stu019','stu020'
)
  AND @tid_cs103_2024_1_full IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs103_2024_1_full, u.id,
    '2024-03-18', 'HOMEWORK',
    CASE u.username
        WHEN 'stu003' THEN 0 WHEN 'stu008' THEN 0 WHEN 'stu013' THEN 0 WHEN 'stu019' THEN 0
        ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '未交' WHEN 'stu008' THEN '未交'
        WHEN 'stu013' THEN '未交' WHEN 'stu019' THEN '未交'
        WHEN 'stu006' THEN '优秀' WHEN 'stu012' THEN '优秀' WHEN 'stu018' THEN '优秀'
        WHEN 'stu002' THEN '优秀' WHEN 'stu009' THEN '良好'
        ELSE '良好' END
FROM sys_users u
WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005',
    'stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015',
    'stu016','stu017','stu018','stu019','stu020'
)
  AND @tid_cs103_2024_1_full IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs103_2024_1_full, u.id,
    '2024-03-25', 'SIGNIN',
    CASE u.username
        WHEN 'stu003' THEN 0 WHEN 'stu013' THEN 0 WHEN 'stu019' THEN 0 ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '缺勤' WHEN 'stu013' THEN '缺勤' WHEN 'stu019' THEN '缺勤'
        ELSE NULL END
FROM sys_users u
WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005',
    'stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015',
    'stu016','stu017','stu018','stu019','stu020'
)
  AND @tid_cs103_2024_1_full IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs103_2024_1_full, u.id,
    '2024-04-01', 'CHAPTER_TEST',
    CASE u.username
        WHEN 'stu003' THEN 0 WHEN 'stu008' THEN 0 WHEN 'stu013' THEN 0 WHEN 'stu019' THEN 0
        ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '缺考' WHEN 'stu008' THEN '缺考'
        WHEN 'stu013' THEN '缺考' WHEN 'stu019' THEN '缺考'
        WHEN 'stu006' THEN '96分' WHEN 'stu012' THEN '94分' WHEN 'stu018' THEN '91分'
        WHEN 'stu002' THEN '89分' WHEN 'stu009' THEN '87分'
        WHEN 'stu001' THEN '83分' WHEN 'stu014' THEN '86分'
        ELSE '75分' END
FROM sys_users u
WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005',
    'stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015',
    'stu016','stu017','stu018','stu019','stu020'
)
  AND @tid_cs103_2024_1_full IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs103_2024_1_full, u.id,
    '2024-04-08', 'HOMEWORK',
    CASE u.username
        WHEN 'stu003' THEN 0 WHEN 'stu008' THEN 0 WHEN 'stu013' THEN 0 WHEN 'stu019' THEN 0
        ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '未交' WHEN 'stu008' THEN '未交'
        WHEN 'stu013' THEN '未交' WHEN 'stu019' THEN '未交'
        WHEN 'stu006' THEN '优秀' WHEN 'stu012' THEN '优秀'
        WHEN 'stu001' THEN '良好' WHEN 'stu002' THEN '优秀'
        ELSE '良好' END
FROM sys_users u
WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005',
    'stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015',
    'stu016','stu017','stu018','stu019','stu020'
)
  AND @tid_cs103_2024_1_full IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

SET @tid_cs102_2024_2_main = ( -- K. 程序设计基础 2024-2（CS102）：补全 stu011-stu020 成绩 + 全员平时记录
    SELECT DISTINCT g.teaching_id FROM edu_grades g
    JOIN edu_teaching t ON t.id = g.teaching_id
    JOIN edu_courses c ON c.id = t.course_id
    WHERE c.course_code = 'CS102'
      AND t.semester COLLATE utf8mb4_unicode_ci = '2024-2'
      AND t.is_deleted = 0
    LIMIT 1
);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs102_2024_2_main,
    CASE u.username
        WHEN 'stu011' THEN 68.0
        WHEN 'stu012' THEN 91.0
        WHEN 'stu013' THEN 48.0
        WHEN 'stu014' THEN 83.0
        WHEN 'stu015' THEN 61.0
        WHEN 'stu016' THEN 79.0
        WHEN 'stu017' THEN 70.0
        WHEN 'stu018' THEN 88.0
        WHEN 'stu019' THEN 43.0
        WHEN 'stu020' THEN 76.0
    END,
    CASE u.username
        WHEN 'stu011' THEN 77.6
        WHEN 'stu012' THEN 91.7
        WHEN 'stu013' THEN 43.6
        WHEN 'stu014' THEN 86.1
        WHEN 'stu015' THEN 72.7
        WHEN 'stu016' THEN 84.3
        WHEN 'stu017' THEN 79.0
        WHEN 'stu018' THEN 91.6
        WHEN 'stu019' THEN 40.1
        WHEN 'stu020' THEN 82.2
    END
FROM sys_users u
WHERE u.username IN ('stu011','stu012','stu013','stu014','stu015',
                     'stu016','stu017','stu018','stu019','stu020')
  AND @tid_cs102_2024_2_main IS NOT NULL
ON DUPLICATE KEY UPDATE
    exam_score   = VALUES(exam_score),
    score        = VALUES(score);

UPDATE edu_teaching SET enrolled_count = 20
WHERE id = @tid_cs102_2024_2_main;

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs102_2024_2_main, u.id, '2024-09-09', 'SIGNIN',
    CASE WHEN u.username IN ('stu003','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username WHEN 'stu003' THEN '缺勤' WHEN 'stu013' THEN '请假' WHEN 'stu019' THEN '缺勤' ELSE NULL END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs102_2024_2_main IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs102_2024_2_main, u.id, '2024-09-16', 'HOMEWORK',
    CASE WHEN u.username IN ('stu003','stu008','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '未交' WHEN 'stu008' THEN '未交'
        WHEN 'stu013' THEN '未交' WHEN 'stu019' THEN '未交'
        WHEN 'stu006' THEN '优秀' WHEN 'stu012' THEN '优秀' WHEN 'stu018' THEN '优秀'
        WHEN 'stu002' THEN '优秀' WHEN 'stu009' THEN '良好' WHEN 'stu014' THEN '优秀'
        ELSE '良好' END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs102_2024_2_main IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs102_2024_2_main, u.id, '2024-09-23', 'SIGNIN',
    CASE WHEN u.username IN ('stu003','stu008','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username WHEN 'stu003' THEN '缺勤' WHEN 'stu008' THEN '迟到' WHEN 'stu013' THEN '缺勤' WHEN 'stu019' THEN '缺勤' ELSE NULL END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs102_2024_2_main IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs102_2024_2_main, u.id, '2024-10-07', 'HOMEWORK',
    CASE WHEN u.username IN ('stu003','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '未交' WHEN 'stu013' THEN '未交' WHEN 'stu019' THEN '未交'
        WHEN 'stu006' THEN '优秀' WHEN 'stu012' THEN '优秀' WHEN 'stu002' THEN '优秀'
        ELSE '良好' END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs102_2024_2_main IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs102_2024_2_main, u.id, '2024-10-14', 'SIGNIN',
    CASE WHEN u.username IN ('stu003','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username WHEN 'stu003' THEN '缺勤' WHEN 'stu013' THEN '缺勤' WHEN 'stu019' THEN '缺勤' ELSE NULL END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs102_2024_2_main IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs102_2024_2_main, u.id, '2024-10-21', 'CHAPTER_TEST',
    CASE WHEN u.username IN ('stu003','stu008','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '缺考' WHEN 'stu008' THEN '缺考'
        WHEN 'stu013' THEN '缺考' WHEN 'stu019' THEN '缺考'
        WHEN 'stu006' THEN '93分' WHEN 'stu012' THEN '91分' WHEN 'stu018' THEN '90分'
        WHEN 'stu002' THEN '88分' WHEN 'stu009' THEN '85分' WHEN 'stu014' THEN '84分'
        WHEN 'stu001' THEN '81分' WHEN 'stu016' THEN '80分' WHEN 'stu010' THEN '82分'
        ELSE '74分' END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs102_2024_2_main IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

SET @tid_cs105_2024_2 = ( -- L. 计算机网络 2024-2（CS105）：全员成绩 + 平时记录
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON c.id = t.course_id
    WHERE c.course_code = 'CS105'
      AND t.semester COLLATE utf8mb4_unicode_ci = '2024-2'
      AND t.is_deleted = 0
    LIMIT 1
);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs105_2024_2,
    CASE u.username
        WHEN 'stu001' THEN 85.0
        WHEN 'stu002' THEN 90.0
        WHEN 'stu003' THEN 42.0
        WHEN 'stu004' THEN 74.0
        WHEN 'stu005' THEN 67.0
        WHEN 'stu006' THEN 93.0
        WHEN 'stu007' THEN 79.0
        WHEN 'stu008' THEN 50.0
        WHEN 'stu009' THEN 88.0
        WHEN 'stu010' THEN 83.0
        WHEN 'stu011' THEN 71.0
        WHEN 'stu012' THEN 95.0
        WHEN 'stu013' THEN 45.0
        WHEN 'stu014' THEN 87.0
        WHEN 'stu015' THEN 63.0
        WHEN 'stu016' THEN 81.0
        WHEN 'stu017' THEN 75.0
        WHEN 'stu018' THEN 92.0
        WHEN 'stu019' THEN 47.0
        WHEN 'stu020' THEN 80.0
    END,
    CASE u.username
        WHEN 'stu001' THEN 88.5
        WHEN 'stu002' THEN 93.0
        WHEN 'stu003' THEN 44.4
        WHEN 'stu004' THEN 76.8
        WHEN 'stu005' THEN 69.9
        WHEN 'stu006' THEN 95.1
        WHEN 'stu007' THEN 82.3
        WHEN 'stu008' THEN 50.0
        WHEN 'stu009' THEN 91.6
        WHEN 'stu010' THEN 85.1
        WHEN 'stu011' THEN 73.7
        WHEN 'stu012' THEN 96.5
        WHEN 'stu013' THEN 46.5
        WHEN 'stu014' THEN 89.9
        WHEN 'stu015' THEN 65.1
        WHEN 'stu016' THEN 84.7
        WHEN 'stu017' THEN 77.5
        WHEN 'stu018' THEN 94.4
        WHEN 'stu019' THEN 47.9
        WHEN 'stu020' THEN 83.0
    END
FROM sys_users u
WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005',
    'stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015',
    'stu016','stu017','stu018','stu019','stu020'
)
  AND @tid_cs105_2024_2 IS NOT NULL
ON DUPLICATE KEY UPDATE
    exam_score   = VALUES(exam_score),
    score        = VALUES(score);

UPDATE edu_teaching SET enrolled_count = 20
WHERE id = @tid_cs105_2024_2;

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs105_2024_2, u.id, '2024-09-05', 'SIGNIN',
    CASE WHEN u.username IN ('stu003','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username WHEN 'stu003' THEN '缺勤' WHEN 'stu013' THEN '请假' WHEN 'stu019' THEN '缺勤' ELSE NULL END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs105_2024_2 IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs105_2024_2, u.id, '2024-09-12', 'HOMEWORK',
    CASE WHEN u.username IN ('stu003','stu008','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '未交' WHEN 'stu008' THEN '未交'
        WHEN 'stu013' THEN '未交' WHEN 'stu019' THEN '未交'
        WHEN 'stu006' THEN '优秀' WHEN 'stu012' THEN '优秀' WHEN 'stu018' THEN '优秀'
        WHEN 'stu002' THEN '优秀' WHEN 'stu009' THEN '优秀'
        ELSE '良好' END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs105_2024_2 IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs105_2024_2, u.id, '2024-09-19', 'SIGNIN',
    CASE WHEN u.username IN ('stu003','stu008','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username WHEN 'stu003' THEN '缺勤' WHEN 'stu008' THEN '迟到' WHEN 'stu013' THEN '缺勤' WHEN 'stu019' THEN '缺勤' ELSE NULL END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs105_2024_2 IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs105_2024_2, u.id, '2024-10-03', 'HOMEWORK',
    CASE WHEN u.username IN ('stu003','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '未交' WHEN 'stu013' THEN '未交' WHEN 'stu019' THEN '未交'
        WHEN 'stu006' THEN '优秀' WHEN 'stu012' THEN '优秀' WHEN 'stu002' THEN '优秀'
        ELSE '良好' END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs105_2024_2 IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs105_2024_2, u.id, '2024-10-10', 'SIGNIN',
    CASE WHEN u.username IN ('stu003','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username WHEN 'stu003' THEN '缺勤' WHEN 'stu013' THEN '缺勤' WHEN 'stu019' THEN '缺勤' ELSE NULL END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs105_2024_2 IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note)
SELECT @tid_cs105_2024_2, u.id, '2024-10-17', 'CHAPTER_TEST',
    CASE WHEN u.username IN ('stu003','stu008','stu013','stu019') THEN 0 ELSE 1 END,
    CASE u.username
        WHEN 'stu003' THEN '缺考' WHEN 'stu008' THEN '缺考'
        WHEN 'stu013' THEN '缺考' WHEN 'stu019' THEN '缺考'
        WHEN 'stu006' THEN '95分' WHEN 'stu012' THEN '97分' WHEN 'stu018' THEN '93分'
        WHEN 'stu002' THEN '91分' WHEN 'stu009' THEN '89分' WHEN 'stu014' THEN '88分'
        WHEN 'stu001' THEN '86分' WHEN 'stu010' THEN '84分' WHEN 'stu016' THEN '82分'
        ELSE '74分' END
FROM sys_users u WHERE u.username IN (
    'stu001','stu002','stu003','stu004','stu005','stu006','stu007','stu008','stu009','stu010',
    'stu011','stu012','stu013','stu014','stu015','stu016','stu017','stu018','stu019','stu020'
) AND @tid_cs105_2024_2 IS NOT NULL
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

SELECT '09_student_demo_data.sql executed.' AS status;
