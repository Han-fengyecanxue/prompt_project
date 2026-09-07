@echo off
chcp 65001 >nul
title 财报解读系统 - 前端 (5173)
cd /d "%~dp0frontend"
echo ============================================
echo  前端启动 (Vite :5173, /api 代理到 8091)
echo  启动后浏览器打开: http://localhost:5173
echo  关闭本窗口 = 停止前端
echo ============================================
if not exist node_modules (
  echo 首次运行, 安装依赖...
  call npm.cmd install
)
call npm.cmd run dev
pause
