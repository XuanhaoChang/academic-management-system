from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_db_config(*, include_pool: bool = False) -> dict[str, Any]:
    """Load database settings from config.ini with optional env overrides."""
    config_path = Path(os.getenv("APP_CONFIG_FILE", PROJECT_ROOT / "config.ini"))
    if not config_path.is_file():
        raise FileNotFoundError(
            "未找到 config.ini；请先复制 config.example.ini 并填写本地数据库配置。"
        )

    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")
    if "mysql" not in parser:
        raise ValueError(f"配置文件缺少 [mysql] 段: {config_path}")

    mysql_cfg = parser["mysql"]
    config: dict[str, Any] = {
        "host": os.getenv("DB_HOST", mysql_cfg.get("host", "127.0.0.1")),
        "port": int(os.getenv("DB_PORT", mysql_cfg.get("port", "3306"))),
        "database": os.getenv(
            "DB_NAME", mysql_cfg.get("database", "my_db_project")
        ),
        "user": os.getenv("DB_USER", mysql_cfg.get("user", "dbadmin")),
        "password": os.getenv("DB_PASSWORD", mysql_cfg.get("password", "")),
        "charset": mysql_cfg.get("charset", "utf8mb4"),
    }
    if include_pool:
        config.update(
            pool_name=mysql_cfg.get("pool_name", "my_db_pool"),
            pool_size=mysql_cfg.getint("pool_size", 8),
        )
    return config
