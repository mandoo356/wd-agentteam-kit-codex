<#
  install_starterkit.ps1

  더블클릭 설치용 본체.
  - C:\WD-AgentTeam 표준 구조를 만든다.
  - 현재 스타터킷을 01_KIT\starter-kit 으로 복사한다.
  - 이동을 느리게 하는 node_modules 및 재생성 파일은 복사하지 않는다.
  - 실제 비밀키와 로그인 상태는 복사하지 않는다.
  - 기존 설치가 있으면 덮어쓰지 않는다.
#>
[CmdletBinding()]
param(
    [string]$InstallRoot = 'C:\WD-AgentTeam',
    [switch]$NoOpen,
    [switch]$SkipEnvironmentCheck
)

$ErrorActionPreference = 'Stop'
try {
    $null = & "$env:ComSpec" /c chcp 65001
    [Console]::OutputEncoding = [Text.Encoding]::UTF8
    [Console]::InputEncoding = [Text.Encoding]::UTF8
} catch {}

try { $Host.UI.RawUI.WindowTitle = '위드드림 AI 에이전트팀 — 폴더 생성 및 설치' } catch {}

$sourceKit = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetRoot = [IO.Path]::GetFullPath($InstallRoot)
$targetKit = Join-Path $targetRoot '01_KIT\starter-kit'
$marker = Join-Path $targetKit '환경점검.bat'
$logFile = Join-Path $targetRoot '설치결과.txt'

function Write-Step([string]$Text) {
    Write-Host ''
    Write-Host "  ▶ $Text" -ForegroundColor Magenta
}

function Write-Info([string]$Text) {
    Write-Host "     $Text" -ForegroundColor DarkGray
}

function Stop-WithMessage([string]$Text) {
    Write-Host ''
    Write-Host "  ❌ $Text" -ForegroundColor Red
    Write-Host ''
    $null = Read-Host '  이 창을 닫으려면 Enter'
    exit 1
}

Write-Host ''
Write-Host '  위드드림 AI 에이전트팀 — 폴더 생성 및 설치' -ForegroundColor Magenta
Write-Host "  설치 위치: $targetRoot" -ForegroundColor DarkGray

# ZIP 내부에서는 옆 파일을 안정적으로 읽지 못하므로 먼저 압축을 풀게 한다.
if (-not (Test-Path -LiteralPath (Join-Path $sourceKit 'env_check.ps1'))) {
    Stop-WithMessage '스타터킷이 완전히 풀리지 않았습니다. ZIP에서 모두 압축 풀기 후 다시 실행하세요.'
}

Write-Step '표준 폴더 만들기'
$folders = @(
    '00_README',
    '01_KIT',
    '02_INSTALLERS\Node22',
    '02_INSTALLERS\Python',
    '02_INSTALLERS\Git',
    '03_OFFLINE_PACKAGES',
    '04_LEARNER_BACKUP',
    '05_EXPORT\html',
    '05_EXPORT\pdf',
    '90_TEMP'
)

try {
    foreach ($relative in $folders) {
        $path = Join-Path $targetRoot $relative
        $null = New-Item -ItemType Directory -Path $path -Force
    }
} catch {
    Stop-WithMessage "C: 드라이브에 폴더를 만들 수 없습니다. 기관 보안정책 또는 권한을 확인하세요. ($($_.Exception.Message))"
}
Write-Info "$($folders.Count)개 표준 폴더 확인"

Write-Step '가벼운 스타터킷 설치'
if (Test-Path -LiteralPath $marker) {
    Write-Host '  ⚠ 기존 스타터킷이 있어 덮어쓰지 않았습니다.' -ForegroundColor Yellow
    Write-Info $targetKit
} else {
    $excludedDirs = @(
        (Join-Path $sourceKit 'office\node_modules'),
        (Join-Path $sourceKit 'office\dist'),
        (Join-Path $sourceKit 'office\.wrangler'),
        (Join-Path $sourceKit '__pycache__'),
        (Join-Path $sourceKit 'slack-server\__pycache__'),
        (Join-Path $sourceKit 'slack-server\logs'),
        (Join-Path $sourceKit 'naver-blog\logs'),
        (Join-Path $sourceKit 'naver-blog\.naver-profile'),
        (Join-Path $sourceKit '.image-flow-profile'),
        (Join-Path $sourceKit 'backup')
    )

    $copyArgs = @(
        $sourceKit,
        $targetKit,
        '/E',
        '/R:1',
        '/W:1',
        '/XJ',
        '/COPY:DAT',
        '/DCOPY:DAT',
        '/NP',
        '/XD'
    ) + $excludedDirs + @(
        '/XF',
        '.env',
        '.agent_session.json',
        '.naver-state.json',
        '환경점검_결과.html',
        '*.pyc'
    )

    & robocopy @copyArgs | Out-Null
    $copyCode = $LASTEXITCODE
    if ($copyCode -gt 7) {
        Stop-WithMessage "스타터킷 복사에 실패했습니다. robocopy 종료코드: $copyCode"
    }
    if (-not (Test-Path -LiteralPath $marker)) {
        Stop-WithMessage '복사가 끝났지만 환경점검.bat을 찾지 못했습니다. 원본 ZIP을 다시 받으세요.'
    }

    $installedFiles = Get-ChildItem -LiteralPath $targetKit -File -Force -Recurse
    $installedBytes = ($installedFiles | Measure-Object Length -Sum).Sum
    Write-Host '  ✅ 스타터킷 복사 성공' -ForegroundColor Green
    Write-Info ("{0}개 파일 / {1:N1}MB" -f $installedFiles.Count, ($installedBytes / 1MB))
}

$readmeSource = Join-Path $targetKit 'README.md'
$readmeTarget = Join-Path $targetRoot '00_README\스타터킷_README.md'
if ((Test-Path -LiteralPath $readmeSource) -and -not (Test-Path -LiteralPath $readmeTarget)) {
    Copy-Item -LiteralPath $readmeSource -Destination $readmeTarget
}

$logLines = @(
    "설치일시=$([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))",
    "원본=$sourceKit",
    "설치위치=$targetKit",
    '제외=node_modules, dist, .wrangler, cache, logs, .env, login profiles',
    '다음단계=01_KIT\starter-kit\환경점검.bat'
)
$logLines | Set-Content -LiteralPath $logFile -Encoding UTF8

Write-Step '설치 결과'
Write-Host "  ✅ 표준 폴더와 스타터킷 준비됨" -ForegroundColor Green
Write-Info "스타터킷: $targetKit"
Write-Info "기록: $logFile"
Write-Host ''
Write-Host '  node_modules는 이동 속도와 PC 호환성 문제 때문에 제외했습니다.' -ForegroundColor Yellow
Write-Host '  환경점검에서 안내하는 npm 설치를 대상 PC에서 진행하세요.' -ForegroundColor Yellow

if (-not $NoOpen) {
    try { Start-Process explorer.exe -ArgumentList "`"$targetRoot`"" } catch {}
}

if (-not $SkipEnvironmentCheck) {
    $answer = Read-Host '  이어서 환경점검을 실행할까요? [Y/n]'
    if ([string]::IsNullOrWhiteSpace($answer) -or $answer.Trim().ToLower().StartsWith('y')) {
        Start-Process -FilePath $marker -WorkingDirectory $targetKit
    }
}

Write-Host ''
Write-Host '  이 창은 닫아도 됩니다.' -ForegroundColor DarkGray
