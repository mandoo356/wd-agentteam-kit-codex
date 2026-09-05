# 설치 위치에 맞춰 Codex 훅 명령의 절대경로를 생성한다. Node.js 22 이상을 사용한다.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$runtime = (Join-Path $PSScriptRoot '.codex\hooks\runtime.mjs').Replace('\','/')
if (-not (Test-Path -LiteralPath $runtime)) { throw 'Codex 훅 프로그램이 없습니다.' }
$command = 'node "' + $runtime + '"'
$hooks = [ordered]@{}
foreach ($event in @('SessionStart','UserPromptSubmit','PreToolUse','PostToolUse','Stop')) {
    $hooks[$event] = @(@{ hooks = @(@{ type='command'; command=$command; timeout=120 }) })
}
$json = @{ description='위드드림 Codex 작업 기록·자동 저장·위험 명령 차단'; hooks=$hooks } | ConvertTo-Json -Depth 8
$file = Join-Path $PSScriptRoot '.codex\hooks.json'
[IO.File]::WriteAllText($file, $json, (New-Object Text.UTF8Encoding($false)))
Write-Host 'Codex 훅 경로를 설정했습니다. Codex에서 프로젝트를 신뢰하고 /hooks에서 5개 이벤트를 확인·신뢰하세요.'
