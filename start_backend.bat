@echo off
cd /d "D:\coshub-api"
uvicorn main:app --reload --port 8000
pause
