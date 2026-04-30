#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '.')

from config import DB_CONFIG
import mysql.connector

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

cursor.execute('''
    SELECT t.id, c.course_name, t.semester, 
           COUNT(DISTINCT g.id) as grade_count
    FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    LEFT JOIN edu_grades g ON t.id = g.teaching_id AND g.is_deleted = 0
    WHERE t.teacher_id = 1
    GROUP BY t.id, c.course_name, t.semester
    ORDER BY c.course_name, t.semester
''')

print("教师的所有课程:")
print("-" * 80)

courses_dict = {}
for row in cursor.fetchall():
    course_key = f"{row['course_name']}_{row['semester']}"
    if course_key not in courses_dict:
        courses_dict[course_key] = []
    courses_dict[course_key].append(row)
    
    status = "有成绩" if row['grade_count'] > 0 else "无成绩"
    print(f"ID: {row['id']:3d}, 课程: {row['course_name']:20s}, 学期: {row['semester']}, {status}")

print("\n" + "=" * 80)
print("重复的课程（同课程同学期出现多次）:")
print("=" * 80)
for key, rows in courses_dict.items():
    if len(rows) > 1:
        print(f"\n课程: {key}")
        for row in rows:
            status = "有成绩" if row['grade_count'] > 0 else "无成绩"
            print(f"  ID: {row['id']}, {status}")

cursor.close()
conn.close()
