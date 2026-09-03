@echo off
REM ============================================================
REM 数据库初始化脚本 (默认导入: 真实财报数据)
REM 用法: 需本机已装 MySQL, 以管理员/普通用户运行 init_db.bat
REM 说明: 真实数据 03_real_data.sql(东方财富/新浪采集, 24家x2021-2025)
REM       模拟数据 02_seed_data.sql 仅作功能演示备选(量级近似, 非真实)
REM ============================================================
chcp 65001 >nul
set MYSQL=mysql
set DB_USER=root
set /p DB_PASS=请输入MySQL密码: 

echo [1/3] 建库建表 (01_schema.sql) ...
%MYSQL% -u%DB_USER% -p%DB_PASS% --default-character-set=utf8mb4 < 01_schema.sql
if errorlevel 1 goto :fail

echo.
set /p DATA_MODE=导入哪种数据?  [R]真实财报数据(默认,推荐)  [S]模拟演示数据(02_seed): 
if /i "%DATA_MODE%"=="S" goto :seed
echo [2/3] 导入真实财报数据 (03_real_data.sql) ...
%MYSQL% -u%DB_USER% -p%DB_PASS% --default-character-set=utf8mb4 < 03_real_data.sql
if errorlevel 1 goto :fail
goto :done

:seed
echo [2/3] 导入模拟演示数据 (02_seed_data.sql) ...
%MYSQL% -u%DB_USER% -p%DB_PASS% --default-character-set=utf8mb4 < 02_seed_data.sql
if errorlevel 1 goto :fail

:done
echo.
echo 完成! 首次请启动后端后执行指标重算:
echo   curl -X POST http://localhost:8091/api/finance/recalc -H "Content-Type: application/json" -d "{}"
pause
exit /b 0

:fail
echo 导入失败, 请检查 MySQL 是否运行、密码是否正确
pause
exit /b 1
