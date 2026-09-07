@echo off
chcp 65001 >nul
title 财报解读系统 - 后端 (8091)
REM 适配最终结构: backend\ 或过渡期 prompt_project\ 均可
if exist "%~dp0backend\target\prompt_project-0.0.1-SNAPSHOT.jar" (
  cd /d "%~dp0backend"
) else (
  cd /d "%~dp0prompt_project"
)
echo ============================================
echo  后端启动 (Spring Boot :8091, 数据库 financial_analysis)
echo  前置: MySQL57 服务运行中; 首次需 init_db.bat 建库
echo  关闭本窗口 = 停止后端
echo ============================================
if not exist target\prompt_project-0.0.1-SNAPSHOT.jar (
  echo 未找到 jar, 先打包...
  call mvnw.cmd -DskipTests package
)
if not exist logs mkdir logs
java -jar target\prompt_project-0.0.1-SNAPSHOT.jar > logs\backend.log 2>&1
pause
