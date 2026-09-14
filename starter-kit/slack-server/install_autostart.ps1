<#
  현재 Windows 사용자에게 Slack-Codex 서버 자동 시작을 설치한다.
  관리자 권한 없이 현재 사용자 로그온 예약 작업으로 등록한다.
#>
[CmdletBinding()]
param(
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'
$taskName = 'WithDream Slack Codex Server'
$serverRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $serverRoot 'run_hidden.ps1'
$pythonExe = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe'

if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    throw "숨김 실행 파일이 없습니다: $runner"
}
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw "Python 3.14가 없습니다. 환경점검.bat을 먼저 실행하세요: $pythonExe"
}

$powerShellExe = Join-Path $PSHOME 'powershell.exe'
$arguments = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$runner`""
$action = New-ScheduledTaskAction -Execute $powerShellExe -Argument $arguments -WorkingDirectory $serverRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description 'Windows 로그인 후 Slack과 Codex 직원을 검은 창 없이 연결하고, 종료 시 자동 재시작합니다.' `
    -RunLevel Limited `
    -Force | Out-Null

if (-not $NoStart) {
    Start-ScheduledTask -TaskName $taskName
    $deadline = (Get-Date).AddSeconds(10)
    do {
        Start-Sleep -Milliseconds 500
        $task = Get-ScheduledTask -TaskName $taskName
    } while ($task.State -ne 'Running' -and (Get-Date) -lt $deadline)
}

$task = Get-ScheduledTask -TaskName $taskName
if ((-not $NoStart -and $task.State -ne 'Running') -or ($NoStart -and $task.State -notin @('Running','Ready'))) {
    throw "예약 작업 상태가 비정상입니다: $($task.State)"
}

Write-Output "WD_AUTOSTART_OK task=$taskName state=$($task.State)"
