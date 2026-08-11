"""数据库初始化脚本 - 按顺序执行所有 SQL 文件"""
import mysql.connector
from pathlib import Path
import sys

from core.config import load_db_config

SQL_FILES = [
    '01_init_schema.sql',
    '02_views.sql',
    '03_procedures.sql',
    '04_triggers.sql',
    '05_test_data.sql',
    '06_teacher_ext.sql',
    '08_student_ext.sql',
]

def execute_sql_statements(cursor, conn, statements):
    """执行 SQL 语句列表"""
    success = 0
    failed = 0
    
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt or stmt.startswith('--'):
            continue
        
        try:
            cursor.execute(stmt)
            if cursor.with_rows:
                cursor.fetchall()
            conn.commit()
            print(f"  [OK] {stmt[:60]}...")
            success += 1
        except Exception as e:
            print(f"  [FAIL] {stmt[:60]}...")
            print(f"    Error: {e}")
            failed += 1
    
    return success, failed

def parse_sql_file(content: str):
    """解析 SQL 文件，处理 DELIMITER"""
    statements = []
    current_statement = []
    delimiter = ';'
    
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 处理 DELIMITER 指令
        if line.upper().startswith('DELIMITER'):
            parts = line.split()
            if len(parts) > 1:
                delimiter = parts[1]
            i += 1
            continue
        
        if not line or line.startswith('--'):
            i += 1
            continue
            
        current_statement.append(lines[i])
        
        # 检查是否到达当前定义的结束符
        if line.endswith(delimiter):
            # 去掉末尾的结束符
            stmt_text = '\n'.join(current_statement)
            if stmt_text.endswith(delimiter):
                stmt_text = stmt_text[:-len(delimiter)]
            statements.append(stmt_text)
            current_statement = []
            
        i += 1
            
    return statements

def main():
    print("=" * 60)
    print("数据库初始化脚本")
    print("=" * 60)
    
    sql_dir = Path(__file__).parent / 'sql'
    
    conn = mysql.connector.connect(**load_db_config())
    cursor = conn.cursor()
    
    total_success = 0
    total_failed = 0
    
    for sql_file in SQL_FILES:
        file_path = sql_dir / sql_file
        if not file_path.exists():
            print(f"\n[SKIP] {sql_file} - 文件不存在")
            continue
        
        print(f"\n执行: {sql_file}")
        print("-" * 60)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            statements = parse_sql_file(content)
            success, failed = execute_sql_statements(cursor, conn, statements)
            
            total_success += success
            total_failed += failed
            
            print(f"  文件完成: 成功 {success}, 失败 {failed}")
            
        except Exception as e:
            print(f"  [ERROR] 文件执行失败: {e}")
            total_failed += 1
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"总计: 成功 {total_success}, 失败 {total_failed}")
    print("=" * 60)

if __name__ == '__main__':
    main()
