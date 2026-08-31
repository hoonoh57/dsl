@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\dsl_stack.ps1" -Action restart
exit /b %ERRORLEVEL%
