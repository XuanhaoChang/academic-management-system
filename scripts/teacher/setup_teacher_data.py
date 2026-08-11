"""
setup_teacher_data.py — 教师端一键数据初始化脚本

整合了以下独立脚本（可单独运行，也可通过本脚本按顺序全部执行）：
  1. create_2024_1_archive.py  — 生成 2024-1 学期归档数据 + 锁定课程
  2. generate_daily_records.py — 为 2024-2 学期生成平时记录 (签到/作业/章节测验)
  3. add_2024_1_grades.py      — 为 2024-1 学期补录成绩（可选，已归档则可跳过）
  4. archive_2024_1.py         — 将 2024-1 成绩从主表归档到 edu_archives 再软删除

运行前提：
  - 已执行 sql/01~05_*.sql（基础建表 + 测试数据）
  - 已执行 sql/06_teacher_ext.sql（教师端扩展表/视图/存储过程）
  - 已执行 sql/07_teacher_demo_data.sql（更多学生 + 2024-2 成绩数据）

使用方法：
  python -m scripts.teacher.setup_teacher_data          # 全部步骤
  python -m scripts.teacher.setup_teacher_data --step 2 # 只执行第2步
"""

import sys
import random
import mysql.connector
from datetime import datetime, timedelta

from core.config import load_db_config

# ──────────────────────────────────────────────────────────────
# 数据库连接配置（与 config.ini 保持一致）
# ──────────────────────────────────────────────────────────────
DB_CONFIG = load_db_config()


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


# ══════════════════════════════════════════════════════════════
# STEP 1 — 为 2024-1 学期直接写入 edu_archives 并锁定课程
#           （适用于 edu_grades 里没有 2024-1 数据的情况）
# ══════════════════════════════════════════════════════════════
def step1_create_2024_1_archive():
    print("\n" + "=" * 60)
    print("STEP 1 — 创建 2024-1 学期归档数据 + 锁定课程")
    print("=" * 60)

    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id AS teaching_id, course_id
            FROM edu_teaching
            WHERE semester = '2024-1' AND is_deleted = 0
        """)
        teachings = cursor.fetchall()
        if not teachings:
            print("  [SKIP] 没有找到 2024-1 学期的授课安排，跳过此步骤。")
            return

        cursor.execute("""
            SELECT id AS student_id
            FROM sys_users
            WHERE role_id = 3 AND is_deleted = 0
            LIMIT 15
        """)
        students = cursor.fetchall()
        print(f"  找到 {len(teachings)} 个课程，{len(students)} 名学生")

        archived_count = 0
        for teaching in teachings:
            teaching_id = teaching['teaching_id']
            course_id   = teaching['course_id']
            for student in students:
                student_id = student['student_id']
                score  = round(random.uniform(55, 95), 2)
                gpa, letter = _score_to_gpa_letter(score)
                is_passed   = 1 if score >= 60 else 0
                original_id = teaching_id * 10000 + student_id
                try:
                    cursor.execute("""
                        INSERT INTO edu_archives
                            (original_grade_id, student_id, teaching_id, course_id, semester,
                             score, gpa_point, grade_letter, is_passed, archived_at)
                        VALUES (%s,%s,%s,%s,'2024-1',%s,%s,%s,%s,'2024-02-15 14:30:00')
                        ON DUPLICATE KEY UPDATE
                            score=VALUES(score), gpa_point=VALUES(gpa_point),
                            grade_letter=VALUES(grade_letter), is_passed=VALUES(is_passed)
                    """, (original_id, student_id, teaching_id, course_id,
                          score, gpa, letter, is_passed))
                    archived_count += 1
                except Exception as e:
                    print(f"    插入失败 (sid={student_id}): {e}")
            conn.commit()

        # 锁定 2024-1 所有课程
        cursor.execute("""
            UPDATE edu_teaching SET is_submitted=1
            WHERE semester='2024-1' AND is_deleted=0
        """)
        conn.commit()

        print(f"  [OK] 已写入 {archived_count} 条归档记录，已锁定所有 2024-1 课程。")

    finally:
        cursor.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# STEP 2 — 为 2024-2 学期生成平时记录 (签到 / 作业 / 章节测验)
# ══════════════════════════════════════════════════════════════
def step2_generate_daily_records():
    print("\n" + "=" * 60)
    print("STEP 2 — 生成 2024-2 学期平时记录")
    print("=" * 60)

    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT t.id AS teaching_id, c.course_name
            FROM edu_teaching t
            JOIN edu_courses c ON t.course_id = c.id
            WHERE t.semester='2024-2' AND t.is_deleted=0
        """)
        teachings = cursor.fetchall()

        cursor.execute("""
            SELECT id AS student_id, username
            FROM sys_users WHERE role_id=3 AND is_deleted=0
            ORDER BY id
        """)
        students = cursor.fetchall()

        if not teachings or not students:
            print("  [SKIP] 缺少 2024-2 课程或学生数据，跳过。")
            return

        print(f"  找到 {len(teachings)} 个课程，{len(students)} 名学生")
        total = 0
        start_date = datetime(2024, 9, 2)
        # (类型, 次数, 间隔天数)
        record_configs = [
            ('SIGNIN',       6, 7),
            ('HOMEWORK',     4, 7),
            ('CHAPTER_TEST', 3, 14),
        ]

        for teaching in teachings:
            tid  = teaching['teaching_id']
            name = teaching['course_name']
            for rtype, count, interval in record_configs:
                for i in range(count):
                    rdate = (start_date + timedelta(days=i * interval)).strftime('%Y-%m-%d')
                    for student in students:
                        completed = 1 if random.random() > 0.15 else 0
                        note = _gen_note(rtype, completed)
                        try:
                            cursor.execute("""
                                INSERT INTO edu_daily_records
                                    (teaching_id, student_id, record_date, record_type, completed, note)
                                VALUES (%s,%s,%s,%s,%s,%s)
                                ON DUPLICATE KEY UPDATE
                                    completed=VALUES(completed), note=VALUES(note)
                            """, (tid, student['student_id'], rdate, rtype, completed, note))
                            total += 1
                        except Exception as e:
                            print(f"    插入失败: {e}")
            conn.commit()
            print(f"  [OK] {name} — 签到×6  作业×4  测验×3")

        print(f"\n  [OK] 共生成 {total} 条平时记录。")

    finally:
        cursor.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# STEP 3 — 为 2024-1 学期补录 edu_grades（可选）
#           若 edu_grades 已有数据则跳过；用于测试"归档前"状态
# ══════════════════════════════════════════════════════════════
def step3_add_2024_1_grades():
    print("\n" + "=" * 60)
    print("STEP 3 — 为 2024-1 学期补录 edu_grades 成绩（可选）")
    print("=" * 60)

    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM edu_grades g
            JOIN edu_teaching t ON g.teaching_id=t.id
            WHERE t.semester='2024-1' AND g.is_deleted=0
        """)
        existing = cursor.fetchone()['cnt']
        if existing > 0:
            print(f"  [SKIP] edu_grades 中已有 {existing} 条 2024-1 记录，跳过。")
            return

        cursor.execute("""
            SELECT id AS teaching_id FROM edu_teaching
            WHERE semester='2024-1' AND is_deleted=0
        """)
        teachings = cursor.fetchall()
        cursor.execute("""
            SELECT id AS student_id FROM sys_users
            WHERE role_id=3 AND is_deleted=0
        """)
        students = cursor.fetchall()

        added = 0
        for teaching in teachings:
            tid = teaching['teaching_id']
            for student in students:
                sid   = student['student_id']
                score = round(random.uniform(55, 98), 2)
                gpa, letter = _score_to_gpa_letter(score)
                is_passed   = 1 if score >= 60 else 0
                try:
                    cursor.execute("""
                        INSERT INTO edu_grades
                            (student_id, teaching_id, exam_score, score, gpa_point, grade_letter, is_passed)
                        VALUES (%s,%s,NULL,%s,%s,%s,%s)
                        ON DUPLICATE KEY UPDATE
                            score=VALUES(score), gpa_point=VALUES(gpa_point),
                            grade_letter=VALUES(grade_letter), is_passed=VALUES(is_passed)
                    """, (sid, tid, score, gpa, letter, is_passed))
                    added += 1
                except Exception as e:
                    print(f"    插入失败 (sid={sid}): {e}")
            conn.commit()

        print(f"  [OK] 已录入 {added} 条成绩。")

    finally:
        cursor.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# STEP 4 — 将 2024-1 成绩从 edu_grades 归档到 edu_archives 并软删除
# ══════════════════════════════════════════════════════════════
def step4_archive_2024_1():
    print("\n" + "=" * 60)
    print("STEP 4 — 归档 2024-1 学期成绩（edu_grades → edu_archives）")
    print("=" * 60)

    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT g.id, g.student_id, g.teaching_id, t.course_id, t.semester,
                   g.score, g.gpa_point, g.grade_letter, g.is_passed
            FROM edu_grades g
            JOIN edu_teaching t ON g.teaching_id=t.id
            WHERE t.semester='2024-1' AND g.is_deleted=0
        """)
        grades = cursor.fetchall()
        if not grades:
            print("  [SKIP] edu_grades 中无 2024-1 记录（可能已归档或未录入）。")
            return

        print(f"  找到 {len(grades)} 条成绩，开始归档...")
        archived = 0
        for g in grades:
            try:
                cursor.execute("""
                    INSERT INTO edu_archives
                        (original_grade_id, student_id, teaching_id, course_id, semester,
                         score, gpa_point, grade_letter, is_passed, archived_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                    ON DUPLICATE KEY UPDATE
                        score=VALUES(score), gpa_point=VALUES(gpa_point),
                        grade_letter=VALUES(grade_letter), is_passed=VALUES(is_passed)
                """, (g['id'], g['student_id'], g['teaching_id'], g['course_id'],
                      g['semester'], g['score'], g['gpa_point'], g['grade_letter'], g['is_passed']))
                archived += 1
            except Exception as e:
                print(f"    归档失败 (gid={g['id']}): {e}")
        conn.commit()

        # 软删除主表记录
        cursor.execute("""
            UPDATE edu_grades g JOIN edu_teaching t ON g.teaching_id=t.id
            SET g.is_deleted=1 WHERE t.semester='2024-1'
        """)
        # 锁定课程
        cursor.execute("""
            UPDATE edu_teaching SET is_submitted=1
            WHERE semester='2024-1' AND is_deleted=0
        """)
        conn.commit()
        print(f"  [OK] 已归档 {archived} 条，主表记录已软删除，课程已锁定。")

    finally:
        cursor.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════════
def _score_to_gpa_letter(score: float):
    if   score >= 90: return 4.0, 'A+'
    elif score >= 85: return 4.0, 'A'
    elif score >= 82: return 3.0, 'B+'
    elif score >= 78: return 3.0, 'B'
    elif score >= 75: return 2.0, 'C+'
    elif score >= 72: return 2.0, 'C'
    elif score >= 60: return 1.0, 'D'
    else:             return 0.0, 'F'


def _gen_note(rtype: str, completed: int):
    if rtype == 'SIGNIN':
        return random.choice(['缺勤', '迟到', '请假']) if not completed else None
    elif rtype == 'HOMEWORK':
        return '未交' if not completed else random.choice(['优秀', '良好', '及格', None, None])
    elif rtype == 'CHAPTER_TEST':
        return '缺考' if not completed else f"{random.randint(65, 98)}分"
    return None


# ══════════════════════════════════════════════════════════════
# 入口
# ══════════════════════════════════════════════════════════════
def main():
    step_arg = None
    if '--step' in sys.argv:
        idx = sys.argv.index('--step')
        if idx + 1 < len(sys.argv):
            step_arg = int(sys.argv[idx + 1])

    steps = {
        1: step1_create_2024_1_archive,
        2: step2_generate_daily_records,
        3: step3_add_2024_1_grades,
        4: step4_archive_2024_1,
    }

    if step_arg:
        if step_arg not in steps:
            print(f"无效的 step 编号：{step_arg}，可选 1-4")
            sys.exit(1)
        steps[step_arg]()
    else:
        print("=" * 60)
        print("教师端数据初始化 — 全部步骤")
        print("=" * 60)
        # 推荐顺序：先建归档数据，再生成平时记录
        step1_create_2024_1_archive()
        step2_generate_daily_records()
        # step3 和 step4 仅在需要通过 edu_grades 中转归档时使用
        # step3_add_2024_1_grades()
        # step4_archive_2024_1()
        print("\n\n[全部完成] 教师端演示数据已就绪。")
        print("  - 2024-1 学期：在'历史归档'标签查看，课程状态 CLOSED")
        print("  - 2024-2 学期：在'成绩录入'/'平时分管理'标签操作，课程状态 OPEN")


if __name__ == '__main__':
    main()
