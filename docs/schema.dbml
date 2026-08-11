// ==================== ENUM ====================

Enum "edu_daily_records_record_type_enum" {
  "SIGNIN"
  "HOMEWORK"
  "CHAPTER_TEST"
}

Enum "edu_schedule_change_req_status_enum" {
  "PENDING"
  "APPROVED"
  "REJECTED"
}

Enum "stu_exam_defer_req_status_enum" {
  "PENDING"
  "APPROVED"
  "REJECTED"
}

// ==================== 基础数据层 ====================

Table "base_dept" {
  "id" int [pk, increment]
  "dept_code" varchar(20)
  "dept_name" varchar(100)
  "created_at" datetime
  "is_deleted" tinyint
}

Table "base_major" {
  "id" int [pk, increment]
  "major_code" varchar(20)
  "major_name" varchar(100)
  "dept_id" int
  "created_at" datetime
  "is_deleted" tinyint
}

// ==================== 用户权限层 ====================

Table "sys_roles" {
  "id" int [pk, increment]
  "role_name" varchar(50)
  "role_code" varchar(50)
  "created_at" datetime
  "is_deleted" tinyint
}

Table "sys_permissions" {
  "id" int [pk, increment]
  "permission_name" varchar(100)
  "permission_code" varchar(100)
  "created_at" datetime
  "is_deleted" tinyint
}

Table "sys_role_permissions" {
  "id" int [pk, increment]
  "role_id" int
  "permission_id" int
  "created_at" datetime
  "is_deleted" tinyint
}

Table "sys_users" {
  "id" int [pk, increment]
  "username" varchar(50)
  "real_name" varchar(100)
  "role_id" int
  "dept_id" int
  "major_id" int
  "password_hash" char(64)
  "created_at" datetime
  "is_deleted" tinyint
}

Table "sys_audit_logs" {
  "id" bigint [pk, increment]
  "user_id" int
  "action_type" varchar(50)
  "detail" text
  "created_at" datetime
  "is_deleted" tinyint
}

Table "sys_config" {
  "id" int [pk, increment]
  "config_key" varchar(100)
  "config_value" varchar(500)
  "created_at" datetime
  "is_deleted" tinyint
}

// ==================== 教学核心层 ====================

Table "edu_courses" {
  "id" int [pk, increment]
  "course_code" varchar(20)
  "course_name" varchar(100)
  "credits" decimal(3,1)
  "dept_id" int
  "description" text
  "created_at" datetime
  "is_deleted" tinyint
}

Table "edu_teaching" {
  "id" int [pk, increment]
  "course_id" int
  "teacher_id" int
  "classroom" varchar(50)
  "timeslot" varchar(100)
  "semester" varchar(20)
  "enrolled_count" int
  "max_count" int
  "status" varchar(20)
  "created_at" datetime
  "is_deleted" tinyint
  "is_submitted" tinyint
}

Table "stu_course_prereq" {
  "id" int [pk, increment]
  "course_id" int
  "pre_course_id" int
  "created_at" datetime
  "is_deleted" tinyint
}

// ==================== 教学运行数据层 ====================

Table "stu_selection" {
  "id" int [pk, increment]
  "student_id" int
  "teaching_id" int
  "created_at" datetime
  "deleted_at" bigint
  "is_deleted" tinyint
}

Table "stu_waiting_list" {
  "id" int [pk, increment]
  "student_id" int
  "teaching_id" int
  "queue_no" int
  "created_at" datetime
  "deleted_at" bigint
  "is_deleted" tinyint
}

Table "edu_daily_records" {
  "id" int [pk, increment]
  "teaching_id" int
  "student_id" int
  "record_date" date
  "record_type" edu_daily_records_record_type_enum
  "completed" tinyint
  "note" varchar(200)
  "created_at" datetime
  "is_deleted" tinyint
}

Table "edu_grades" {
  "id" int [pk, increment]
  "student_id" int
  "teaching_id" int
  "exam_score" decimal(5,2)
  "score" decimal(5,2)
  "created_at" datetime
  "is_deleted" tinyint
}

Table "edu_archives" {
  "id" int [pk, increment]
  "original_grade_id" int
  "student_id" int
  "teaching_id" int
  "score" decimal(5,2)
  "archived_at" datetime
  "created_at" datetime
  "is_deleted" tinyint
}

// ==================== 业务扩展层 ====================

Table "stu_exam_schedule" {
  "id" int [pk, increment]
  "course_id" int
  "semester" varchar(20)
  "exam_date" date
  "start_time" time
  "end_time" time
  "exam_room" varchar(50)
  "created_at" datetime
  "is_deleted" tinyint
}

Table "stu_exam_defer_req" {
  "id" int [pk, increment]
  "student_id" int
  "course_id" int
  "semester" varchar(20)
  "reason" varchar(500)
  "status" stu_exam_defer_req_status_enum
  "created_at" datetime
  "updated_at" datetime
  "is_deleted" tinyint
}

Table "stu_evaluation" {
  "id" int [pk, increment]
  "student_id" int
  "course_id" int
  "semester" varchar(20)
  "eval_score" int
  "eval_comment" varchar(500)
  "created_at" datetime
  "is_deleted" tinyint
}

Table "edu_schedule_change_req" {
  "id" int [pk, increment]
  "teaching_id" int
  "teacher_id" int
  "reason" varchar(500)
  "original_time" varchar(100)
  "requested_time" varchar(100)
  "status" edu_schedule_change_req_status_enum
  "admin_comment" varchar(300)
  "processed_by" int
  "created_at" datetime
  "is_deleted" tinyint
}

Table "stu_info" {
  "id" int [pk, increment]
  "student_id" int
  "grade_year" int
  "class_name" varchar(50)
  "phone" varchar(30)
  "email" varchar(120)
  "created_at" datetime
  "is_deleted" tinyint
}

// ==================== 关系 ====================

Ref: base_dept.id < base_major.dept_id
Ref: base_dept.id < edu_courses.dept_id
Ref: base_dept.id < sys_users.dept_id

Ref: base_major.id < sys_users.major_id

Ref: sys_roles.id < sys_users.role_id
Ref: sys_permissions.id < sys_role_permissions.permission_id
Ref: sys_roles.id < sys_role_permissions.role_id
Ref: sys_users.id < sys_audit_logs.user_id

Ref: edu_courses.id < edu_teaching.course_id
Ref: sys_users.id < edu_teaching.teacher_id

Ref: edu_courses.id < stu_course_prereq.course_id
Ref: edu_courses.id < stu_course_prereq.pre_course_id

Ref: sys_users.id < stu_selection.student_id
Ref: edu_teaching.id < stu_selection.teaching_id

Ref: sys_users.id < stu_waiting_list.student_id
Ref: edu_teaching.id < stu_waiting_list.teaching_id

Ref: sys_users.id < edu_daily_records.student_id
Ref: edu_teaching.id < edu_daily_records.teaching_id

Ref: sys_users.id < edu_grades.student_id
Ref: edu_teaching.id < edu_grades.teaching_id

Ref: edu_courses.id < stu_exam_schedule.course_id
Ref: edu_courses.id < stu_exam_defer_req.course_id
Ref: sys_users.id < stu_exam_defer_req.student_id

Ref: edu_courses.id < stu_evaluation.course_id
Ref: sys_users.id < stu_evaluation.student_id

Ref: edu_teaching.id < edu_schedule_change_req.teaching_id
Ref: sys_users.id < edu_schedule_change_req.teacher_id

Ref: sys_users.id < stu_info.student_id