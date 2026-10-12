# sql 目录说明

本目录用于初始化数据库并导入真实财务报表数据。

## 文件清单

| 文件 | 类型 | 作用 |
|------|------|------|
| `01_schema.sql` | SQL | 建库建表，定义表结构 |
| `03_real_data.sql` | SQL | 真实财报数据导入文件（含清空旧数据+整体插入） |
| `fetch_real_data.py` | Python | 从东财/新浪接口采集数据，生成 `03_real_data.sql` |
| `init_db.bat` | 批处理 | 一键执行 `01_schema.sql` + `03_real_data.sql` 导入数据库 |

## 使用方式

### 1. 初始化数据库（用已有数据）

运行 `init_db.bat`，输入 MySQL root 密码即可。

### 2. 抓取最新数据再导入
