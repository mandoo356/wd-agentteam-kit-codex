@echo off
chcp 65001 >nul
cd /d "%~dp0"
where codex.cmd >nul 2>nul
if errorlevel 1 (
  echo [오류] Codex CLI를 찾을 수 없습니다. 먼저 환경점검.bat을 실행하세요.
  pause
  exit /b 1
)
echo Codex를 YOLO 모드로 시작합니다. 이 폴더의 파일과 명령을 승인 질문 없이 다룰 수 있습니다.
echo 최초 실행 또는 업데이트 후 /hooks에서 5개 이벤트를 검토하고 신뢰하세요.
echo 작업기록의 Codex 훅 실행 확인을 확인한 뒤 실습하세요.
call codex.cmd --yolo
if errorlevel 1 pause
