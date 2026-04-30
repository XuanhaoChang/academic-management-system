from __future__ import annotations

import configparser
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, cast

import mysql.connector
from mysql.connector import pooling
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.cursor import MySQLCursorDict


class DBManager:
    _pool: Optional[pooling.MySQLConnectionPool] = None

    @classmethod
    def _load_config(cls) -> dict[str, Any]:
        config_file = Path(__file__).resolve().parent.parent / "config.ini"
        parser = configparser.ConfigParser()
        parser.read(config_file, encoding="utf-8")

        mysql_cfg = parser["mysql"]
        return {
            "host": mysql_cfg.get("host", "127.0.0.1"),
            "port": mysql_cfg.getint("port", 3306),
            "database": mysql_cfg.get("database", "my_db_project"),
            "user": mysql_cfg.get("user", "dbadmin"),
            "password": mysql_cfg.get("password", "DbAdmin2024"),
            "pool_name": mysql_cfg.get("pool_name", "my_db_pool"),
            "pool_size": mysql_cfg.getint("pool_size", 8),
            "charset": mysql_cfg.get("charset", "utf8mb4"),
            "autocommit": False,
            "use_pure": True,
        }

    @classmethod
    def init_pool(cls) -> None:
        if cls._pool is None:
            cls._pool = pooling.MySQLConnectionPool(**cls._load_config())

    @classmethod
    def get_connection(cls) -> MySQLConnectionAbstract:
        cls.init_pool()
        return cls._pool.get_connection()  # type: ignore[union-attr]

    @classmethod
    def verify_connection(cls) -> bool:
        conn = cls.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        finally:
            conn.close()

    @classmethod
    def exec_query(
        cls,
        sql: str,
        params: Optional[Sequence[Any]] = None,
        *,
        fetch: bool = True,
        with_soft_delete: bool = False,
        soft_delete_column: str = "is_deleted",
    ) -> list[dict[str, Any]]:
        final_sql = sql
        if with_soft_delete and "where" in sql.lower() and soft_delete_column not in sql.lower():
            final_sql = f"{sql} AND {soft_delete_column} = 0"

        conn = cls.get_connection()
        cursor = cast(MySQLCursorDict, conn.cursor(dictionary=True))
        try:
            cursor.execute(final_sql, params or ())
            if fetch:
                rows = cursor.fetchall() or []
                result: list[dict[str, Any]] = []
                for r in rows:
                    if r is None:
                        continue
                    result.append({str(k): v for k, v in r.items()})
                return result

            conn.commit()
            return []
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    @classmethod
    @contextmanager
    def transaction(cls):
        conn = cls.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @classmethod
    def exec_transaction(
        cls,
        tasks: Iterable[tuple[str, Sequence[Any]]],
    ) -> None:
        with cls.transaction() as conn:
            cursor = conn.cursor()
            try:
                for sql, params in tasks:
                    cursor.execute(sql, params)
            finally:
                cursor.close()
