# Copilot Instructions For my_db_project

## 项目定位
- 这是基于 Python、PyQt6 与 MySQL 的桌面教务管理系统。
- 代码由多人接力完成，优先保证一致性与可回归性，再做功能扩展。

## 常用命令
- 安装依赖: `pip install -r requirements.txt`
- 初始化数据库: `python init_database.py`
- 启动程序: `python main.py`
- 运行语法检查: `python -m compileall -q core models services ui utils views scripts main.py init_database.py`

## 架构边界
- `core/`: 基础设施层（数据库、会话、异常、日志）。
- `services/`: 业务逻辑层（按角色与领域拆分）。
- `models/`: 数据访问对象与分析查询。
- `views/`: 主窗口与页面装配。
- `ui/`: 复用组件与角色子面板。
- `sql/`: 数据库脚本与扩展（按编号顺序执行）。

## 强约定（提交前必须满足）
- 数据库访问统一通过 `core.db_manager.DBManager`，禁止字符串拼接 SQL。
- 多表写操作必须放在 `DBManager.transaction()` 中，保证事务原子性。
- 业务层只抛 `BusinessError`/`ValidationError` 等领域异常，UI 层负责统一提示。
- 涉及删除时优先遵守 `is_deleted` 逻辑删除语义，不直接物理删除（除非业务明确例外）。
- 变更型业务操作应补齐审计日志（参考 `core.logger.AuditLogger` 使用方式）。

## 现有代码风险与协作提醒
- 文档提到的某些脚本可能与当前仓库不完全一致；新增流程时以仓库现状为准并同步更新文档。
- `views/student/enrollment.py` 体量大，新增学生端功能优先拆分到 `ui/` 或 `views/student/` 子模块，避免继续膨胀单文件。
- `*:Zone.Identifier` 属于跨平台拷贝残留，已由 `.gitignore` 排除。
- GUI 测试依赖图形环境；在无桌面环境执行时需考虑 Qt offscreen 方案。

## 链接文档（不重复维护）
- 项目入口与启动说明: `README.md`
- 系统架构: `docs/architecture.md`

## 推荐工作方式
- 先改 `services/` 与 `models/`，后改 `views/`/`ui/`，最后补测试。
- 涉及数据库结构或 SQL 逻辑时，同时更新 `sql/` 脚本与最小可运行验证步骤。
- PR 描述中至少包含: 影响模块、回归点、手工测试步骤。
