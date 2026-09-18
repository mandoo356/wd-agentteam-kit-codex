@echo off
rem ============================================================
rem  Register the evening blog task (daily 20:00).
rem  Double-click once. No administrator rights are needed.
rem  (ASCII only: cmd.exe can open this file on every learner PC.)
rem ============================================================
chcp 65001 >nul
echo.
echo  Registering: EveningBlog  (every day at 20:00)
echo  Target: %~dp0evening_blog.bat
echo.
schtasks /Create /TN "EveningBlog" /TR "\"%~dp0evening_blog.bat\"" /SC DAILY /ST 20:00 /F
if errorlevel 1 (
  echo.
  echo  [ERROR] Registration failed. Copy the message above and ask your instructor.
) else (
  echo.
  echo  [OK] Done. Check it:  schtasks /Query /TN "EveningBlog"
  echo       Run it now:      schtasks /Run   /TN "EveningBlog"
  echo       Remove it:       schtasks /Delete /TN "EveningBlog" /F
)
echo.
pause
