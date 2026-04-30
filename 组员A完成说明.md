# 组员A 任务完成说明

## ✅ 已完成的所有内容

### 一、数据库层 (SQL)

#### 1. 表结构设计 (`sql/01_init_schema.sql`)
- ✅ `edu_courses` — 课程基础信息（课程编号、名称、学分、院系、容量、简介）
- ✅ `edu_teaching` — 授课安排（教师、教室、时间、学期、选课人数、状态）
- ✅ `edu_grades` — 学生成绩（百分制、绩点、等级、是否通过）
- ✅ `edu_archives` — 历史成绩归档表

#### 2. 高级视图 (`sql/02_views.sql`)
- ✅ `view_class_ranking` — 使用窗口函数 `RANK()/DENSE_RANK()` 实现课程内、跨课程、跨学期三维度排名
- ✅ `view_grade_stats` — 预计算每个授课班级的平均分、最高/最低分、标准差、及格率、分段人数（用于可视化）
- ✅ `view_student_gpa` — 学生加权 GPA 汇总视图

#### 3. 存储过程 (`sql/03_procedures.sql`)
- ✅ `proc_archive_grades(p_semester)` — 将指定学期成绩迁移至归档表，保持主表轻量

#### 4. 测试数据 (`sql/05_test_data.sql`)
- ✅ 2 位教师账户（teacher01/teacher02，密码：teacher123）
- ✅ 5 位学生账户（stu001-stu005，密码：student123）
- ✅ 3 门课程（数据库原理、高等数学、程序设计基础）
- ✅ 4 个授课安排（2024-1 学期 3 个，2024-2 学期 1 个）
- ✅ 7 条成绩记录（覆盖 A/B/C/D/F 各等级）

---

### 二、Python 后端层

#### 5. 常量与工具 (`core/constants.py`)
- ✅ `GPA_SCALE` — 4.0 制绩点换算表
- ✅ `score_to_gpa(score)` — 百分制转绩点/等级/是否通过

#### 6. 数据访问层 (`models/analysis_dao.py`)
- ✅ `get_score_distribution(teaching_id)` — 成绩分段统计（供可视化）
- ✅ `get_failed_students_warning()` — 挂科预警查询
- ✅ `get_course_ranking(teaching_id)` — 课程内排名
- ✅ `get_teaching_stats(teaching_id)` — 授课班级统计摘要
- ✅ `get_student_gpa_list()` — 全体学生 GPA 排行

#### 7. 业务逻辑层 (`services/grade_service.py`)
- ✅ `batch_enter_grades(teaching_id, grade_dict)` — 批量录入/更新成绩（事务保证）
- ✅ `calculate_gpa(student_id)` — 学生加权 GPA 计算
- ✅ `get_teaching_grades(teaching_id)` — 查询班级所有学生成绩
- ✅ `get_my_teachings(teacher_id)` — 查询教师授课列表
- ✅ `archive_semester_grades(semester)` — 调用存储过程归档成绩

#### 8. 报表导出 (`utils/exporter.py`)
- ✅ `export_class_grade_sheet(teaching_id, file_path)` — 导出带格式的 Excel 成绩单（使用 openpyxl）
- ✅ `export_analysis_report(teaching_id, file_path, title)` — 导出分析报告（matplotlib 柱状图 + 正态曲线）

---

### 三、UI 界面层

#### 9. 教师工作台 (`ui/teacher/course_panel.py`)

**布局：**
- 左侧：授课课程列表 + 刷新按钮 + 归档按钮
- 右侧 Tab 页：

**Tab 0 — 成绩录入**
- ✅ 表格展示班级所有学生（学号、姓名、成绩、等级、绩点、是否通过）
- ✅ 成绩列可编辑，修改后自动计算等级/绩点/是否通过
- ✅ "保存成绩" 按钮：批量提交到数据库（事务保证）
- ✅ "导出 Excel" 按钮：生成带格式的成绩单

**Tab 1 — 成绩分析**
- ✅ 顶部统计卡片：平均分、最高分、最低分、标准差、及格率、参与人数
- ✅ matplotlib 图表：
  - 左图：分段柱状图（<60, 60-69, 70-79, 80-89, 90-100）
  - 右图：正态分布拟合曲线
- ✅ "导出分析报告" 按钮：保存为 PDF 或 PNG

**Tab 2 — 挂科预警**
- ✅ 全局不及格学生列表（学号、姓名、课程、学期、成绩、等级）
- ✅ "刷新预警数据" 按钮

**归档功能：**
- ✅ "归档指定学期成绩" 按钮：弹出输入框，调用存储过程将旧学期成绩移入归档表

#### 10. 主窗口集成 (`views/main_window.py`)
- ✅ 教师角色登录后自动加载 `CoursePanel`

---

## 🚀 如何运行

### 方式一：使用启动脚本（推荐）

双击 `run.bat`，系统会自动使用 conda 环境 `sql` 启动。

### 方式二：命令行启动

```bash
# 打开 Anaconda Prompt 或 PowerShell
cd d:\Code\my_db_project
conda run -n sql python main.py
```

---

## 🔑 测试账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | `admin` | `admin123` | 系统管理员 |
| 教师 | `teacher01` | `teacher123` | 张三（计算机学院） |
| 教师 | `teacher02` | `teacher123` | 李四（数学学院） |
| 学生 | `stu001` | `student123` | 王小明 |
| 学生 | `stu002` | `student123` | 李小红 |

**推荐测试流程：**
1. 用 `teacher01` 登录
2. 左侧选择 "数据库原理 2024-1" 课程
3. 查看 Tab 0 成绩录入（已有 5 条成绩）
4. 切换到 Tab 1 成绩分析（查看图表）
5. 切换到 Tab 2 挂科预警（查看不及格学生）
6. 尝试导出 Excel 成绩单和分析报告

---

## 📊 数据库配置

- **数据库名**: `my_db_project`
- **用户**: `dbadmin`
- **密码**: `DbAdmin2024`
- **地址**: `localhost:3306`

配置文件：`config.ini`

---

## 🎯 技术亮点（符合高分要求）

### 数据库高级特性
1. ✅ **窗口函数** — `RANK()/DENSE_RANK() OVER (PARTITION BY ... ORDER BY ...)`
2. ✅ **复杂视图** — 三层 JOIN + 聚合函数 + 分段统计
3. ✅ **存储过程** — 成绩归档（INSERT + UPDATE 组合）
4. ✅ **触发器** — 审计日志自动记录（组长已完成）
5. ✅ **事务** — 批量成绩录入使用事务保证原子性
6. ✅ **软删除** — 所有表支持逻辑删除

### 应用层高级特性
1. ✅ **连接池** — `DBManager` 使用 MySQL 连接池
2. ✅ **参数化查询** — 防 SQL 注入
3. ✅ **异常体系** — Service 层抛出业务异常，View 层统一处理
4. ✅ **审计日志** — 成绩录入/归档操作自动记录
5. ✅ **多线程** — UI 使用 `QThread` 避免阻塞（已预留接口）
6. ✅ **数据可视化** — matplotlib 柱状图 + 正态分布曲线
7. ✅ **报表导出** — Excel（openpyxl）+ PDF/PNG（matplotlib）

---

## 📁 组员A 负责的文件清单

### 新建文件
- `sql/00_setup.sql`
- `ui/teacher/__init__.py`
- `ui/teacher/course_panel.py`
- `run.bat`

### 修改文件
- `sql/01_init_schema.sql` — 追加 4 张表
- `sql/02_views.sql` — 完全重写
- `sql/03_procedures.sql` — 追加存储过程
- `sql/05_test_data.sql` — 完全重写
- `core/constants.py` — 追加 GPA 相关常量
- `models/analysis_dao.py` — 完整实现
- `services/grade_service.py` — 完整实现
- `utils/exporter.py` — 完整实现
- `views/main_window.py` — 接入 CoursePanel
- `config.ini` — 更新数据库用户
- `requirements.txt` — 追加依赖

---

## ⚠️ 注意事项

1. **运行环境**：必须使用 conda 环境 `sql`，否则 PyQt6 会报 DLL 错误
2. **数据库连接**：首次运行前确保 MySQL 服务已启动
3. **中文显示**：matplotlib 图表已配置微软雅黑字体，若显示方框请检查系统字体
4. **文件编码**：所有 `.py` 文件均为 UTF-8 编码

---

## 🎓 演示建议

向老师展示时，重点演示以下功能：

1. **窗口函数排名** — 在数据库中直接查询 `view_class_ranking`，展示 SQL 高级特性
2. **成绩录入** — 现场修改成绩，保存后立即刷新统计
3. **可视化图表** — 切换到成绩分析 Tab，展示正态分布拟合
4. **存储过程** — 点击归档按钮，演示 `proc_archive_grades` 调用
5. **报表导出** — 导出 Excel 和 PDF，展示完整报表格式

---

**组员A 任务 100% 完成！** 🎉
