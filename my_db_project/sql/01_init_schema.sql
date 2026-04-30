CREATE DATABASE IF NOT EXISTS my_db_project DEFAULT CHARACTER SET utf8mb4;
USE my_db_project;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS sys_roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    role_code VARCHAR(50) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sys_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    permission_name VARCHAR(100) NOT NULL,
    permission_code VARCHAR(100) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sys_role_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    UNIQUE KEY uk_role_permission (role_id, permission_id),
    CONSTRAINT fk_role_perm_role FOREIGN KEY (role_id) REFERENCES sys_roles(id),
    CONSTRAINT fk_role_perm_perm FOREIGN KEY (permission_id) REFERENCES sys_permissions(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS base_dept (
    id INT PRIMARY KEY AUTO_INCREMENT,
    dept_code VARCHAR(20) NOT NULL UNIQUE,
    dept_name VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS base_major (
    id INT PRIMARY KEY AUTO_INCREMENT,
    major_code VARCHAR(20) NOT NULL UNIQUE,
    major_name VARCHAR(100) NOT NULL,
    dept_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    CONSTRAINT fk_major_dept FOREIGN KEY (dept_id) REFERENCES base_dept(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sys_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    real_name VARCHAR(100) NOT NULL,
    role_id INT NOT NULL,
    dept_id INT NULL,
    major_id INT NULL,
    password_hash CHAR(64) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    CONSTRAINT fk_user_role FOREIGN KEY (role_id) REFERENCES sys_roles(id),
    CONSTRAINT fk_user_dept FOREIGN KEY (dept_id) REFERENCES base_dept(id),
    CONSTRAINT fk_user_major FOREIGN KEY (major_id) REFERENCES base_major(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sys_audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    action_type VARCHAR(50) NOT NULL,
    detail TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    INDEX idx_audit_created_at (created_at),
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES sys_users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sys_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value VARCHAR(500) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

-- ============================================================
-- [组员A] 课程与成绩相关表
-- ============================================================

CREATE TABLE IF NOT EXISTS edu_courses (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    course_code VARCHAR(20)    NOT NULL UNIQUE COMMENT '课程编号',
    course_name VARCHAR(100)   NOT NULL        COMMENT '课程名称',
    credits     DECIMAL(3,1)   NOT NULL DEFAULT 3.0 COMMENT '学分',
    dept_id     INT            NOT NULL,
    description TEXT           NULL               COMMENT '课程简介',
    created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted  TINYINT        NOT NULL DEFAULT 0,
    CONSTRAINT fk_course_dept FOREIGN KEY (dept_id) REFERENCES base_dept(id)
) ENGINE=InnoDB COMMENT='课程基础信息';

CREATE TABLE IF NOT EXISTS edu_teaching (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    course_id      INT          NOT NULL,
    teacher_id     INT          NOT NULL,
    classroom      VARCHAR(50)  NULL              COMMENT '教室',
    timeslot       VARCHAR(100) NULL              COMMENT '上课时间，如 周一3-4节',
    semester       VARCHAR(20)  NOT NULL          COMMENT '学期，格式: 2024-1',
    enrolled_count INT          NOT NULL DEFAULT 0,
    max_count      INT          NOT NULL DEFAULT 50,
    status         VARCHAR(20)  NOT NULL DEFAULT 'OPEN' COMMENT 'OPEN/CLOSED/FULL',
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted     TINYINT      NOT NULL DEFAULT 0,
    CONSTRAINT ck_teaching_max_count_pos CHECK (max_count > 0),
    CONSTRAINT fk_teaching_course  FOREIGN KEY (course_id)  REFERENCES edu_courses(id),
    CONSTRAINT fk_teaching_teacher FOREIGN KEY (teacher_id) REFERENCES sys_users(id)
) ENGINE=InnoDB COMMENT='授课安排';

CREATE TABLE IF NOT EXISTS edu_grades (
    id           INT PRIMARY KEY AUTO_INCREMENT,
    student_id   INT           NOT NULL,
    teaching_id  INT           NOT NULL COMMENT '教学班ID(edu_teaching.id)，非教师ID',
    exam_score   DECIMAL(5,2)  NULL    COMMENT '卷面成绩',
    score        DECIMAL(5,2)  NULL    COMMENT '百分制总成绩',
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted   TINYINT       NOT NULL DEFAULT 0,
    UNIQUE KEY uk_student_teaching (student_id, teaching_id),
    INDEX idx_grades_teaching_del_student (teaching_id, is_deleted, student_id),
    CONSTRAINT ck_grade_exam_score_range CHECK (exam_score IS NULL OR (exam_score >= 0 AND exam_score <= 100)),
    CONSTRAINT ck_grade_score_range CHECK (score IS NULL OR (score >= 0 AND score <= 100)),
    CONSTRAINT fk_grade_student  FOREIGN KEY (student_id)  REFERENCES sys_users(id),
    CONSTRAINT fk_grade_teaching FOREIGN KEY (teaching_id) REFERENCES edu_teaching(id)
) ENGINE=InnoDB COMMENT='学生成绩';

CREATE TABLE IF NOT EXISTS edu_archives (
    id               INT PRIMARY KEY AUTO_INCREMENT,
    original_grade_id INT         NOT NULL COMMENT '原edu_grades.id',
    student_id        INT         NOT NULL,
    teaching_id       INT         NOT NULL,
    score             DECIMAL(5,2) NULL,
    archived_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted        TINYINT      NOT NULL DEFAULT 0
) ENGINE=InnoDB COMMENT='历史成绩归档';

-- ============================================================
-- [组员B] 选课相关占位表 (组员B负责完善)
-- ============================================================

CREATE TABLE IF NOT EXISTS stu_selection (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT      NOT NULL,
    teaching_id INT     NOT NULL COMMENT '教学班ID(edu_teaching.id)，非教师ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at BIGINT   NOT NULL DEFAULT 0 COMMENT '软删除时间戳(毫秒), 0=有效',
    is_deleted TINYINT  NOT NULL DEFAULT 0 COMMENT '兼容字段，建议仅由 deleted_at 派生',
    UNIQUE KEY uk_selection_student_teaching (student_id, teaching_id, deleted_at),
    INDEX idx_sel_teaching_del_student (teaching_id, deleted_at, student_id),
    CONSTRAINT fk_stu_selection_student FOREIGN KEY (student_id) REFERENCES sys_users(id),
    CONSTRAINT fk_stu_selection_teaching FOREIGN KEY (teaching_id) REFERENCES edu_teaching(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS stu_waiting_list (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT      NOT NULL,
    teaching_id INT     NOT NULL COMMENT '教学班ID(edu_teaching.id)，非教师ID',
    queue_no   INT      NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at BIGINT   NOT NULL DEFAULT 0 COMMENT '软删除时间戳(毫秒), 0=有效',
    is_deleted TINYINT  NOT NULL DEFAULT 0 COMMENT '兼容字段，建议仅由 deleted_at 派生',
    UNIQUE KEY uk_waiting_student_teaching (student_id, teaching_id, deleted_at),
    INDEX idx_wait_teaching_del_queue (teaching_id, deleted_at, queue_no, id),
    CONSTRAINT fk_waiting_student FOREIGN KEY (student_id) REFERENCES sys_users(id),
    CONSTRAINT fk_waiting_teaching FOREIGN KEY (teaching_id) REFERENCES edu_teaching(id)
) ENGINE=InnoDB;
