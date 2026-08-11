from dataclasses import dataclass
from typing import Optional


@dataclass
class SessionUser:
    id: int
    username: str
    role_id: int
    real_name: str


class Session:
    current_user: Optional[SessionUser] = None

    @classmethod
    def clear(cls) -> None:
        cls.current_user = None
