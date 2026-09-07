<#
  Slack-Codex 서버 숨김 감시기.
  Windows 예약 작업이 이 파일을 실행한다. 검은 창 없이 서버를 유지하고,
  서버가 비정상 종료되면 잠시 뒤 다시 시작한다.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$serverRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe'
$serverFile = Join-Path $serverRoot 'server.py'
$logRoot = Join-Path $serverRoot 'logs'
$null = New-Item -ItemType Directory -Path $logRoot -Force

while ($true) {
    $logFile = Join-Path $logRoot ("supervisor-{0}.log" -f (Get-Date -Format 'yyyy-MM-dd'))
    try {
        if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
            "$(Get-Date -Format s) Python 3.14를 찾지 못했습니다: $pythonExe" | Add-Content -LiteralPath $logFile -Encoding UTF8
            Start-Sleep -Seconds 60
            continue
        }
        if (-not (Test-Path -LiteralPath $serverFile -PathType Leaf)) {
            "$(Get-Date -Format s) server.py를 찾지 못했습니다: $serverFile" | Add-Content -LiteralPath $logFile -Encoding UTF8
            Start-Sleep -Seconds 60
            continue
        }

        "$(Get-Date -Format s) Slack-Codex 서버 시작" | Add-Content -LiteralPath $logFile -Encoding UTF8
        Push-Location $serverRoot
        try {
            & $pythonExe -X utf8 -u $serverFile *>> $logFile
            $serverExit = $LASTEXITCODE
        } finally {
            Pop-Location
        }
        "$(Get-Date -Format s) 서버 종료코드=$serverExit; 10초 뒤 재시작" | Add-Content -LiteralPath $logFile -Encoding UTF8
    } catch {
        "$(Get-Date -Format s) 감시기 오류=$($_.Exception.Message); 10초 뒤 재시작" | Add-Content -LiteralPath $logFile -Encoding UTF8
    }
    Start-Sleep -Seconds 10
}
