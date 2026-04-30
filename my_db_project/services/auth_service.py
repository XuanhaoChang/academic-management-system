from __future__ import annotations

import hashlib
from dataclasses import dataclass

from core.constants import ActionType
from core.db_manager import DBManager
from core.exceptions import AuthError
from core.logger import AuditLogger
from core.session import Session, SessionUser


@dataclass
class User:
    id: int
    username: str
    role_id: int
    real_name: str


class AuthService:
    @staticmethod
    def _hash_password(raw_password: str) -> str:
        return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

    @classmethod
    def login(cls, username: str, password_hash: str) -> User:
        sql = """
        SELECT id, username, role_id, real_name
        FROM sys_users
        WHERE username = %s
          AND password_hash = %s
          AND is_deleted = 0
        LIMIT 1
        """
        rows = DBManager.exec_query(sql, (username, password_hash), fetch=True)
        if not rows:
            raise AuthError("用户名或密码错误")

        row = rows[0]
        user = User(
            id=row["id"],
            username=row["username"],
            role_id=row["role_id"],
            real_name=row["real_name"],
        )
        Session.current_user = SessionUser(**user.__dict__)
        AuditLogger.log_action(user.id, ActionType.LOGIN, f"User {user.username} logged in")
        return user

    @classmethod
    def login_with_password(cls, username: str, raw_password: str) -> User:
        return cls.login(username, cls._hash_password(raw_password))

    # register method removed: registration is not supported in this wave

    @classmethod
    def update_password(cls, uid: int, old: str, new: str) -> None:
        check_sql = """
        SELECT id
        FROM sys_users
        WHERE id = %s
          AND password_hash = %s
          AND is_deleted = 0
        """
        old_hash = cls._hash_password(old)
        if not DBManager.exec_query(check_sql, (uid, old_hash)):
            raise AuthError("旧密码错误")

        update_sql = """
        UPDATE sys_users
        SET password_hash = %s
        WHERE id = %s AND is_deleted = 0
        """
        new_hash = cls._hash_password(new)
        DBManager.exec_query(update_sql, (new_hash, uid), fetch=False)
        AuditLogger.log_action(uid, ActionType.UPDATE_PASSWORD, "Password updated")
