# 贡献指南

感谢你愿意改进本项目。提交变更前，请先创建 Issue 描述问题或目标，较大的功能建议先讨论方案。

## 本地开发

1. Fork 并克隆仓库。
2. 创建独立分支：`git switch -c feat/short-description`。
3. 创建虚拟环境并执行 `pip install -r requirements.txt`。
4. 将 `config.example.ini` 复制为 `config.ini`，仅填写本地数据库信息。
5. 完成修改后运行 `python -m compileall -q .` 和相关测试。

## 提交约定

- 一次提交只处理一个清晰目标。
- 数据库结构变更应同步更新 `sql/` 和 `docs/`。
- 多表写操作应使用事务；SQL 查询必须参数化。
- 不要提交密码、证书、数据库备份、日志或本地配置文件。
- PR 中请说明影响模块、验证方式和必要的数据库迁移步骤。
