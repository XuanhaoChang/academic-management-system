from typing import Optional

from core.db_manager import DBManager


class AuditLogger:
    @staticmethod
    def log_action(user_id: Optional[int], action_type: str, detail: str) -> None:
        sql = """
        INSERT INTO sys_audit_logs (user_id, action_type, detail)
        VALUES (%s, %s, %s)
        """
        DBManager.exec_query(sql, (user_id, action_type, detail), fetch=False)
