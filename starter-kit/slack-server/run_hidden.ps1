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
$fails = 0
$notified = $false

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
        $startedAt = Get-Date
        Push-Location $serverRoot
        try {
            & $pythonExe -X utf8 -u $serverFile *>> $logFile
            $serverExit = $LASTEXITCODE
        } finally {
            Pop-Location
        }
        "$(Get-Date -Format s) 서버 종료코드=$serverExit; 재시작 준비" | Add-Content -LiteralPath $logFile -Encoding UTF8
    } catch {
        "$(Get-Date -Format s) 감시기 오류=$($_.Exception.Message); 재시작 준비" | Add-Content -LiteralPath $logFile -Encoding UTF8
    }

    # 2026-10-05: 예전에는 여기서 10초마다 조용히 영원히 다시 띄웠다. 열쇠가 틀리면
    #   하루 종일 돌면서 아무도 모른다 — 수강생 눈에는 "PC 를 껐다 켜니 슬랙이 죽었다" 로 보인다.
    #   바로 꺼지는 게 3번 연속이면 안내 창을 한 번 띄우고 재시도 간격을 60초로 늘린다.
    $lived = [int]((Get-Date) - $startedAt).TotalSeconds
    if ($lived -lt 20) { $fails++ } else { $fails = 0; $notified = $false }
    if ($fails -ge 3) {
        $help = Join-Path $logRoot '서버가_안뜹니다.txt'
        @(
            '슬랙 서버가 떴다가 바로 꺼지는 것이 반복되고 있습니다.',
            '',
            "마지막 확인: $(Get-Date -Format 'yyyy-MM-dd HH:mm')   연속 실패 $fails 회",
            '',
            '거의 모든 경우 원인은 슬랙 열쇠 3개입니다.',
            '  1) 스타터킷 폴더의 환경점검.bat 을 다시 누르세요',
            '  2) 열쇠 3개를 다시 붙여넣으세요 (xoxb- / xapp- / 내 슬랙 아이디)',
            '  3) 끝나면 이 파일은 지워도 됩니다',
            '',
            "자세한 기록: slack-server\logs\$(Split-Path $logFile -Leaf)"
        ) | Set-Content -LiteralPath $help -Encoding UTF8
        if (-not $notified) {
            "$(Get-Date -Format s) 연속 $fails 회 실패 — 안내 창을 띄우고 재시도 간격을 60초로 늘립니다" | Add-Content -LiteralPath $logFile -Encoding UTF8
            $notice = Join-Path $serverRoot 'notice.vbs'
            if (Test-Path -LiteralPath $notice) {
                try { Start-Process -FilePath 'wscript.exe' -ArgumentList ('"{0}"' -f $notice) -WindowStyle Hidden } catch {}
            }
            $notified = $true
        }
        Start-Sleep -Seconds 60
    } else {
        Start-Sleep -Seconds 10
    }
}
