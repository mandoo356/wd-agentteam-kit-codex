@echo off
rem ============================================================
rem  Evening blog - runs at 20:00 by Windows Task Scheduler.
rem  Uses the required Python 3.14 installation for this course.
rem  (ASCII only: cmd.exe can open this file on every learner PC.)
rem ============================================================
chcp 65001 >nul
set "PY314=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not exist "%PY314%" (
  echo [ERROR] Python 3.14 was not found: %PY314%
  echo Run the starter kit environment check first.
  exit /b 1
)
"%PY314%" -X utf8 "%~dp0evening_blog.py"
exit /b %ERRORLEVEL%
