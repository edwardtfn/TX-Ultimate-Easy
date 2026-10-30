@echo off
setlocal
set PYTHONUNBUFFERED=1
cd /d "%~dp0"

if exist "C:\Users\Al\AppData\Local\esphome-venv\Scripts\python.exe" (
    set "PY_BIN=C:\Users\Al\AppData\Local\esphome-venv\Scripts\python.exe"
) else (
    set "PY_BIN=python"
)

"%PY_BIN%" -u run_tests.py %*
