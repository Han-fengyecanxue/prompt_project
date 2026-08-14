@echo off
REM ============================================================
REM 一键初始化数据库 (schema + 种子数据)
REM 用法: 双击运行, 或命令行执行 init_db.bat
REM 前置: 本机 MySQL 已启动, 且已安装 Python 3 (py 命令)
REM ============================================================
chcp 65001 >nul
set MYSQL=mysql
set DB_USER=root
set /p DB_PASS=请输入MySQL密码: 

echo [1/2] 创建表结构 (01_schema.sql) ...
%MYSQL% -u%DB_USER% -p%DB_PASS% --default-character-set=utf8mb4 < 01_schema.sql
if errorlevel 1 goto :fail

echo [2/2] 导入种子数据 (02_seed_data.sql) ...
%MYSQL% -u%DB_USER% -p%DB_PASS% --default-character-set=utf8mb4 < 02_seed_data.sql
if errorlevel 1 goto :fail

echo.
echo 完成! 接下来启动后端并执行一次指标重算:
echo   POST http://localhost:8091/api/finance/recalc
echo   (或 curl -X POST http://localhost:8091/api/finance/recalc -H "Content-Type: application/json" -d "{}")
pause
exit /b 0

:fail
echo 初始化失败, 请检查 MySQL 服务与密码是否正确。
pause
exit /b 1
