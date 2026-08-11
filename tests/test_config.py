from pathlib import Path

from core.config import load_db_config


def _write_config(path: Path) -> None:
    path.write_text(
        """[mysql]
host = 127.0.0.1
port = 3306
database = demo
user = demo_user
password = demo_password
pool_name = test_pool
pool_size = 3
charset = utf8mb4
""",
        encoding="utf-8",
    )


def test_load_db_config_from_explicit_file(tmp_path, monkeypatch):
    config_file = tmp_path / "config.ini"
    _write_config(config_file)
    monkeypatch.setenv("APP_CONFIG_FILE", str(config_file))

    config = load_db_config(include_pool=True)

    assert config["database"] == "demo"
    assert config["pool_name"] == "test_pool"
    assert config["pool_size"] == 3


def test_environment_overrides_connection_values(tmp_path, monkeypatch):
    config_file = tmp_path / "config.ini"
    _write_config(config_file)
    monkeypatch.setenv("APP_CONFIG_FILE", str(config_file))
    monkeypatch.setenv("DB_HOST", "db.internal")
    monkeypatch.setenv("DB_PORT", "3307")
    monkeypatch.setenv("DB_PASSWORD", "overridden")

    config = load_db_config()

    assert config["host"] == "db.internal"
    assert config["port"] == 3307
    assert config["password"] == "overridden"
