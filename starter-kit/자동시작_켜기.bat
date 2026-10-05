@echo off
setlocal
rem Register logon autostart for the Slack-Codex server.
rem ASCII body on purpose (cmd.exe reads .bat in CP949).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0slack-server\install_autostart.ps1"
pause
