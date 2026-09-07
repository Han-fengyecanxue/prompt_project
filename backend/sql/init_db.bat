@echo off
REM ============================================================
REM 数据库初始化脚本 (导入真实财报数据)
REM 用法: 需本机已装 MySQL, 运行 init_db.bat 并按提示输入密码
REM 数据: 03_real_data.sql = 东方财富/新浪公开接口采集的真实财报数据
REM       (24家上市公司 x 2021-2025年报, 与公开年报核对一致)
REM ============================================================
chcp 65001 >nul
set MYSQL=mysql
set DB_USER=root
set /p DB_PASS=请输入MySQL密码: 

echo [1/2] 建库建表 (01_schema.sql) ...
%MYSQL% -u%DB_USER% -p%DB_PASS% --default-character-set=utf8mb4 < 01_schema.sql
if errorlevel 1 goto :fail

echo [2/2] 导入真实财报数据 (03_real_data.sql) ...
%MYSQL% -u%DB_USER% -p%DB_PASS% --default-character-set=utf8mb4 < 03_real_data.sql
if errorlevel 1 goto :fail

echo.
echo 完成! 首次请启动后端后执行指标重算:
echo   curl -X POST http://localhost:8091/api/finance/recalc -H "Content-Type: application/json" -d "{}"
pause
exit /b 0

:fail
echo 导入失败, 请检查 MySQL 是否运行、密码是否正确
pause
exit /b 1
