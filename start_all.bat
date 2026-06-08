
@echo off
chcp 65001 >nul
title COSHub 一键启动

echo ============================================================
echo   🚀 COSHub 一键启动
echo ============================================================
echo.

REM 启动后端
echo [1/3] 正在启动后端...
start "COSHub-Backend" cmd /k "cd /d %~dp0 && uvicorn main:app --reload --port 8000"

timeout /t 2 /nobreak >nul

REM 启动前端
echo [2/3] 正在启动前端...
start "COSHub-Frontend" cmd /k "cd /d %~dp0coshub && npm run dev"

timeout /t 3 /nobreak >nul

REM 打开浏览器
echo [3/3] 正在打开浏览器...
start http://127.0.0.1:5173

echo.
echo ============================================================
echo   ✅ 启动完成！
echo   👉 后端: http://127.0.0.1:8000/docs (API文档)
echo   👉 前端: http://127.0.0.1:5173
echo   💡 关闭终端即可停止服务
echo ============================================================
pause

