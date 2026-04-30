# my_db_project (教务管理系统)

## 数据库架构文档

- 统一设计说明（人类 + Agent）：`DATABASE_ARCHITECTURE.md`

## 快速启动

### 1. 安装依赖
```bash
pip install PyQt6 mysql-connector-python openpyxl matplotlib numpy
```

### 2. 配置数据库
编辑 `config.ini` 文件，设置 MySQL 连接信息：
```ini
[mysql]
host = 127.0.0.1
port = 3306
database = my_db_project
user = dbadmin
password = DbAdmin2024
```

远程部署时，将 `host` 改为数据库服务器 IP（例如 `192.168.1.10`）。

### 2.1 开启远程访问（数据库服务器）
1. 创建数据库与本地/远程账号授权（数据库服务器执行）
```bash
cd /path/to/my_db_project
#sudo mysql -u root -p < sql/00_setup.sql
```

2. 验证账号已创建（数据库服务器执行）
```bash
sudo mysql -u root -p -e "SELECT user,host FROM mysql.user WHERE user='dbadmin';"
```
预期至少看到两条：
- `dbadmin | localhost`
- `dbadmin | %`

3. 修改 MySQL 监听地址（数据库服务器执行）

Ubuntu/Debian 常见位置：
```bash
sudo sed -i 's/^bind-address\s*=.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo systemctl restart mysql
sudo systemctl status mysql --no-pager
```

CentOS/RHEL 常见位置：
```bash
sudo sed -i 's/^bind-address\s*=.*/bind-address = 0.0.0.0/' /etc/my.cnf
sudo systemctl restart mysqld
sudo systemctl status mysqld --no-pager
```

4. 放行 3306 端口

**开发/演示模式（放行所有来源，方便 IP 变动）：**

UFW（Ubuntu）：
```bash
sudo ufw allow 3306/tcp
sudo ufw status
```

firewalld（CentOS/RHEL）：
```bash
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

**安全模式（仅放行特定网段）：**
如果您有固定物理环境，建议使用此方式：
- UFW: `sudo ufw allow from 192.168.0.0/16 to any port 3306 proto tcp`
- firewalld: `sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.0.0/16" port protocol="tcp" port="3306" accept'`

5. 获取服务器公网 IP 与测试
若服务器 IP 动态变动，可在服务器执行以下命令获取当前 IP：
```bash
curl ifconfig.me
```
然后在客户端测试连接：
```bash
mysql -h <服务器IP> -P 3306 -u dbadmin -p -e "SHOW DATABASES LIKE 'my_db_project';"
```

6. 客户端项目配置
把 `config.ini` 中的 `host` 改成数据库服务器 IP：
```ini
[mysql]
host = <服务器IP>
port = 3306
database = my_db_project
user = dbadmin
password = DbAdmin2024
```

7. 安全建议（强烈推荐）
- 不要在公网直接开放 3306，优先使用 Tailscale/ZeroTier/WireGuard 等内网组网。
- 若必须公网访问，请将 `dbadmin@%` 改为固定来源网段或固定客户端 IP。

### 3. 初始化数据库
有两种方式：

**方式一：使用 Python 脚本（推荐）**
```bash
python init_database.py
python setup_procedures.py
```

**方式二：手动执行 SQL**
```bash
mysql -u root -p < sql/00_setup.sql
mysql -u dbadmin -p < sql/01_init_schema.sql
mysql -u dbadmin -p < sql/02_views.sql
mysql -u dbadmin -p < sql/03_procedures.sql
mysql -u dbadmin -p < sql/04_triggers.sql
mysql -u dbadmin -p < sql/05_test_data.sql
mysql -u dbadmin -p < sql/06_teacher_ext.sql
mysql -u dbadmin -p < sql/07_teacher_demo_data.sql
mysql -u dbadmin -p < sql/08_student_ext.sql
mysql -u dbadmin -p < sql/09_student_demo_data.sql
```

### 4. 启动应用
```bash
python main.py
```

默认测试账号：
- 管理员：admin / admin123
- 教师：teacher01 / teacher123
- 学生：stu001 / student123

## 功能模块

### 管理员端
- 用户管理：批量导入、增删改查、角色分配
- 部门管理：院系结构维护
- 专业管理：专业信息管理
- 课程管理：课程信息维护
- 开课管理：教学班级安排

### 教师端（组员A）
- **成绩录入**：卷面成绩录入、Excel 导入导出、提交锁定
- **成绩分析**：可视化图表、统计指标、分析报告导出
- **挂科预警**：不及格学生预警、预警名单导出
- **平时分管理**：签到/作业/测验记录、自动计算平时分
- **历史归档**：学期成绩归档查询
- **批量操作**：批量调分、智能曲线、成绩筛选、批量导出
- **课程设置**：权重配置、自动保存、数据备份恢复

### 学生端（组员B）
- 个人信息：姓名/学号/年级/专业/专业排名/GPA 展示，支持修改密码
- 选课系统：在线选课、退课、候补、取消候补，课程搜索（课程/教师/教室），显示教师/教室/学期/容量
- 课表查询：10 节次周课表，显示课程名+教室与节次起止时间
- 成绩查询：课程检索、平时分/卷面分/最终分/绩点/等级展示，不及格高亮，支持导出 Excel
- 考试查询：课程检索、考试时间展示（开始结束合并）、缓考申请与取消申请
- 课程评教：显示课程编号/课程名/学期/任课教师/打分状态，支持 0-100 打分与评语提交

## 技术栈
- **前端**：PyQt6
- **后端**：Python 3.10+
- **数据库**：MySQL 8.0+
- **数据分析**：matplotlib, numpy
- **文档导出**：openpyxl, reportlab
