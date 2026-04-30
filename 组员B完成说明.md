# 组员B 任务完成说明

## ✅ 完成范围（学生端）

### 一、数据库与脚本（学生端扩展）

- 已完成 `sql/08_student_ext.sql`：
  - 新增 `stu_info`（学生扩展信息）
  - 新增 `stu_course_prereq`（先修课关系）
  - 新增 `stu_exam_schedule`（考试安排）
  - 新增 `stu_exam_defer_req`（缓考申请）
  - 新增 `stu_evaluation`（课程评教）
  - 增强 `proc_attempt_enroll`（按学期开课容量控制选课）
  - 调整 `trigger_auto_fill_vacancy`（仅同步人数/状态，递补由服务层事务处理）

- 已完成 `sql/09_student_demo_data.sql`：
  - 清理重复选课/候补记录
  - 初始化学生扩展资料 `stu_info`
  - 自动生成当前学期考试安排
  - 预置选课/候补演示数据（含满员与候补队列）
  - 同步 `edu_teaching.enrolled_count/status`
  - 已补充 `MA201-高等数学` 的学生端可见数据（当前学期开课 + 演示学生可选）

### 二、后端服务层（学生业务）

- `services/student_service.py`
  - 当前学期识别、学生信息查询、可选/已选/候补课程查询
  - 成绩查询（当前学期）、GPA 计算、专业排名
  - 考试查询 + 缓考申请/取消申请
  - 课程评教查询与提交
  - 兼容旧库：当 `stu_exam_defer_req` 未初始化时，考试查询可降级运行并给出可理解提示

- `services/student_selection_impl.py` + `services/student_selection_patch.py`
  - 选课、退课、取消候补三类核心操作
  - 退课后自动递补（服务层事务内完成）
  - 选课成功后自动清理该课程旧评教记录，确保“新选课默认未打分”

### 三、学生端 UI（PyQt6）

- `views/student/enrollment.py`
  - 页面结构：`个人信息 / 选课系统 / 课表查询 / 成绩查询 / 考试查询 / 课程评教`
  - 选课系统：
    - 可选课程、已选课程、候补课程三表分区展示
    - 支持按课程编号/课程名/教师/教室搜索
    - 支持选课、退课、取消候补
    - 显示课程编号、课程名、上课时间、教室、学期、容量/已选
  - 课表查询：
    - 10 节次显示
    - 左侧显示每节课时间范围
    - 课表格内展示“课程名 + 教室”
  - 成绩查询：
    - 支持课程名检索
    - 不及格（<60）红色高亮
    - 支持导出 Excel 成绩单
  - 考试查询：
    - 支持检索、申请缓考、取消申请
  - 课程评教：
    - 显示任课教师与打分状态
    - 支持 0~100 分打分及评语提交
  - 个人信息：
    - 展示姓名、学号、年级、专业、专业排名、GPA
    - 支持修改密码
  - 刷新按钮行为：
    - 实现“刷新当前页面”而非重置数据库数据

- `views/main_window.py`
  - 学生角色下使用学生端页面与右侧纵向导航布局，保持与当前系统风格一致

### 四、稳定性与一致性补充

- `views/login_dialog.py`
  - 恢复正式登录异常处理，避免调试代码导致的登录不稳定

- `services/admin_service.py`
  - 管理员新增/导入/修改为学生角色时，自动补齐 `stu_info`，保证新建学生账号可直接进入学生端

## 📁 组员B主要文件清单

### 新增文件
- `组员B完成说明.md`

### 主要修改文件
- `sql/08_student_ext.sql`
- `sql/09_student_demo_data.sql`
- `services/student_service.py`
- `services/student_selection_impl.py`
- `services/student_selection_patch.py`
- `services/selection_service.py`
- `views/student/enrollment.py`
- `views/main_window.py`
- `views/login_dialog.py`
- `services/admin_service.py`

## 🧪 建议验收路径

1. 运行学生侧 SQL 脚本：`sql/08_student_ext.sql`、`sql/09_student_demo_data.sql`
2. 用管理员账号确认课程中存在“高等数学（MA201）”
3. 用学生账号登录，在“选课系统”中确认可见“高等数学”
4. 验证选课、退课、候补、缓考、评教、成绩导出全流程

---

组员B学生端功能已按当前代码状态完成并可演示。
