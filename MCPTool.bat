@echo off
setlocal EnableExtensions

cd /d "%~dp0"
title MCPTool

chcp 65001 >nul 2>&1
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

where powershell.exe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Windows PowerShell is required to run the MCPTool launcher.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows_launcher.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [MCPTool] Launcher exited with code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
