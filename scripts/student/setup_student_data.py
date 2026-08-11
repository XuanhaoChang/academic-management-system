"""
学生端一键初始化脚本

用途：
1) 执行 sql/08_student_ext.sql（学生端扩展对象）
2) 执行 sql/09_student_demo_data.sql（学生端演示数据）
"""
from __future__ import annotations

from pathlib import Path

import mysql.connector

from core.config import load_db_config

DB = load_db_config()


def run_sql_file(path: Path) -> None:
    conn = mysql.connector.connect(**DB)
    cursor = conn.cursor()
    try:
        content = path.read_text(encoding="utf-8")
        # 按 DELIMITER 拆分执行（简单稳妥）
        statements: list[str] = []
        chunks = content.split("DELIMITER $$")
        if len(chunks) == 1:
            statements = [s.strip() for s in content.split(";") if s.strip()]
        else:
            # 先处理 DELIMITER 之前
            head = chunks[0]
            statements.extend([s.strip() for s in head.split(";") if s.strip()])
            # 处理中间块（直到 DELIMITER ;）
            rest = "$$".join(chunks[1:])
            proc_parts = rest.split("DELIMITER ;")
            for part in proc_parts[:-1]:
                p = part.strip()
                if p:
                    statements.append(p)
            tail = proc_parts[-1]
            statements.extend([s.strip() for s in tail.split(";") if s.strip()])

        for stmt in statements:
            if not stmt or stmt.startswith("--"):
                continue
            cursor.execute(stmt)
            if cursor.with_rows:
                cursor.fetchall()
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    files = [
        root / "sql" / "08_student_ext.sql",
        root / "sql" / "09_student_demo_data.sql",
    ]
    for f in files:
        if not f.exists():
            raise FileNotFoundError(f"缺少 SQL 文件: {f}")
        print(f"[RUN] {f.name}")
        run_sql_file(f)
    print("[OK] 学生端数据初始化完成")


if __name__ == "__main__":
    main()
