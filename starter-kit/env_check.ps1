<#
  env_check.ps1 — 「에이전트팀 만들기 과정」 출발선 자동 점검

  무엇을 하나
    1) 필요한 프로그램(Node·Python·Git·Codex CLI…)이 깔렸는지, 버전이 맞는지 본다
    2) 빠진 것은 winget / npm.cmd / pip 으로 묻지 않고 설치한다 (2026-09-07)
    3) ChatGPT 로그인과 가려진 슬랙 열쇠 3개 입력 후 실제 연결을 점검한다
    4) 결과 체크리스트를 검은 창과 HTML(환경점검_결과.html)로 보여준다

  실행
    환경점검.bat 더블클릭  ← 이게 전부입니다
    (직접)  powershell -NoProfile -ExecutionPolicy Bypass -File env_check.ps1

  옵션 (강사·테스트용)
    -SkipInstall      자동 설치 안 함
    -SkipLogin        로그인 창·슬랙 입력·슬랙 연결 시험 모두 생략
    -SkipSlack        슬랙 입력·슬랙 연결 시험 모두 생략
    -NoServerTest     서버 첫 기동 시험만 생략
    -OptionalLogins   선택 로그인(Google Flow·네이버)도 진행
    -NoBrowser        HTML·안내 페이지 안 열음
    -NoPause          끝나고 Enter 대기 안 함
    -Yes              호환용: 선택 로그인 뒤 Enter 대기 생략 (비밀값 입력은 생략하지 않음)
    -PretendMissing   테스트용 — 특정 항목을 "없는 것"으로 가정
                      예) -PretendMissing node,git,codex-login

  🔒 이 파일은 .env 의 열쇠 값을 절대 읽어 화면에 찍지 않습니다. 입력 값은 가리고 .env에만 저장하며 기존 다른 설정은 보존합니다.
  🔒 로그인은 항상 사람이 직접 합니다. 비밀번호를 대신 입력하지 않습니다.
#>
[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$SkipLogin,
    [switch]$SkipSlack,
    [switch]$NoServerTest,
    [switch]$OptionalLogins,
    [switch]$NoBrowser,
    [switch]$NoPause,
    [switch]$Yes,
    [string[]]$PretendMissing = @()
)

# ── 0. 콘솔 준비 ──────────────────────────────────────────────
$ErrorActionPreference = 'Continue'
# -File 로 넘어오면 "node,git" 이 한 덩어리로 들어오므로 콤마를 잘라 준다
$PretendMissing = @($PretendMissing | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
try { $null = & "$env:ComSpec" /c chcp 65001 } catch {}
try {
    [Console]::OutputEncoding = [Text.Encoding]::UTF8
    [Console]::InputEncoding  = [Text.Encoding]::UTF8
} catch {}
try { $Host.UI.RawUI.WindowTitle = '에이전트팀 만들기 — 환경 점검' } catch {}

$KIT    = Split-Path -Parent $MyInvocation.MyCommand.Path
$COURSE = Split-Path -Parent $KIT
$USERHOME = $env:USERPROFILE
$REPORT = Join-Path $KIT '환경점검_결과.html'
$STARTED = Get-Date
# 대표 PC에서는 C:\Users\USER\AppData\Local\Programs\Python\Python314\python.exe. 다른 PC도 같은 사용자 설치 경로를 사용합니다.
$PYTHON314 = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe'

$OKM = [char]0x2705   # ✅
$NOM = [char]0x274C   # ❌
$WRN = [char]0x26A0   # ⚠

# ── 1. 도우미 ────────────────────────────────────────────────
function Write-Step([string]$t) { Write-Host ''; Write-Host "  ▶ $t" -ForegroundColor Magenta }
function Write-Info([string]$t) { Write-Host "     $t" -ForegroundColor DarkGray }
function Write-Warn([string]$t) { Write-Host "     $WRN $t" -ForegroundColor Yellow }

# 설치에는 확인 질문이 없습니다. 비밀값과 본인 로그인만 직접 입력합니다.

function Wait-Enter([string]$msg) {
    if ($Yes -or $NoPause) { return }
    $null = Read-Host "  ⏎ $msg (Enter)"
}

function Invoke-Cmd {
    # cmd.exe 로 한 줄을 실행해 출력·종료코드를 돌려준다. 멈추면 시간 초과로 끊는다.
    param([string]$Line, [int]$TimeoutSec = 30)
    $tmp = [IO.Path]::GetTempFileName()
    try {
        # Start-Process는 일부 자동화 환경에서 Path/PATH 중복 때문에 실패한다.
        # ProcessStartInfo는 그 환경도 그대로 넘길 수 있어 강의 PC와 자동 검증 양쪽에서 안전하다.
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $env:ComSpec
        $psi.Arguments = "/d /s /c `"$Line > `"`"$tmp`"`" 2>&1`""
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $psi
        $null = $p.Start()
        if (-not $p.WaitForExit($TimeoutSec * 1000)) {
            try { $p.Kill() } catch {}
            return @{ ok = $false; code = -2; out = '(시간 초과)' }
        }
        $out = ''
        try { $out = [IO.File]::ReadAllText($tmp, [Text.Encoding]::UTF8).Trim() } catch {}
        $code = $p.ExitCode
        if ($code -eq $null) {
            # 그래도 비면 출력으로 판정 (cmd 의 "인식되지 않습니다" 메시지가 없으면 성공으로 본다)
            $code = 1
            # 종료코드를 확인할 수 없으면 성공으로 추정하지 않습니다.
        }
        return @{ ok = ($code -eq 0); code = $code; out = $out }
    } catch {
        return @{ ok = $false; code = -1; out = "$_" }
    } finally {
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
}

function First-Line([string]$s) { if (-not $s) { return '' }; return ($s -split "`r?`n")[0].Trim() }

function Get-Ver([string]$text) {
    if ($text -match '(\d+)\.(\d+)(?:\.(\d+))?') {
        $patch = 0; if ($Matches[3]) { $patch = $Matches[3] }
        return [version]('{0}.{1}.{2}' -f $Matches[1], $Matches[2], $patch)
    }
    return $null
}

function Has-Cmd([string]$name) {
    $c = Get-Command $name -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c) { return $c.Source }
    return $null
}

function Refresh-Path {
    $m = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $u = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = (@($env:Path, $m, $u, (Join-Path $env:APPDATA 'npm')) | Where-Object { $_ }) -join ';'
}

function Open-Url([string]$url) {
    if ($NoBrowser) { Write-Info "(브라우저 생략) $url"; return }
    try { Start-Process $url } catch { Write-Warn "열 수 없음: $url" }
}

function Open-NewWindow([string]$title, [string]$cmdline, [string]$workdir = $KIT) {
    # 사람이 직접 조작해야 하는 명령(로그인 등)은 별도 검은 창에 띄운다.
    if ($SkipLogin) { Write-Info "(로그인 창 생략) $cmdline"; return }
    try {
        Start-Process -FilePath $env:ComSpec -ArgumentList "/k title $title && $cmdline" -WorkingDirectory $workdir
    } catch { Write-Warn "창을 열 수 없음: $_" }
}

# ── 2. 결과 저장소 ───────────────────────────────────────────
$script:Results = New-Object System.Collections.ArrayList

function Set-Result {
    param([string]$Id, [string]$Name, [string]$Group, [bool]$Ok, [string]$Detail,
          [string]$Fix = '', [string]$Url = '')
    if ($PretendMissing -contains $Id) { $Ok = $false; $Detail = "(테스트) 없는 것으로 가정 — $Detail" }
    $row = [pscustomobject]@{ Id=$Id; Name=$Name; Group=$Group; Ok=$Ok; Detail=$Detail; Fix=$Fix; Url=$Url }
    $i = -1
    for ($k = 0; $k -lt $script:Results.Count; $k++) { if ($script:Results[$k].Id -eq $Id) { $i = $k } }
    if ($i -ge 0) { $script:Results[$i] = $row } else { $null = $script:Results.Add($row) }
    $mark = $NOM; $color = 'Red'
    if ($Ok) { $mark = $OKM; $color = 'Green' }
    Write-Host ("  {0}  {1}" -f $mark, $Name) -ForegroundColor $color
    if ($Detail) { Write-Host ("        └ {0}" -f $Detail) -ForegroundColor DarkGray }
    return $Ok
}
function Get-Result([string]$Id) { foreach ($r in $script:Results) { if ($r.Id -eq $Id) { return $r } }; return $null }
function Is-Ok([string]$Id) { $r = Get-Result $Id; return ($r -and $r.Ok) }

# ── 3. 개별 검사 ─────────────────────────────────────────────
function Check-Internet {
    foreach ($h in 'chatgpt.com', 'nodejs.org', 'www.google.com') {
        try {
            $c = New-Object Net.Sockets.TcpClient
            $ar = $c.BeginConnect($h, 443, $null, $null)
            $done = $ar.AsyncWaitHandle.WaitOne(3000)
            if ($done -and $c.Connected) { $c.Close(); return (Set-Result 'internet' '인터넷 연결' '기본' $true "$h 연결됨") }
            $c.Close()
        } catch {}
    }
    Set-Result 'internet' '인터넷 연결' '기본' $false 'Wi-Fi/랜선을 확인하세요 — 설치와 로그인 모두 인터넷이 필요합니다'
}

function Check-Disk {
    try {
        $drive = Get-PSDrive -Name $KIT.Substring(0, 1) -ErrorAction Stop
        $gb = [math]::Round($drive.Free / 1GB, 1)
        Set-Result 'disk' '디스크 여유 3GB 이상' '기본' ($gb -ge 3) "$($drive.Name): 드라이브 여유 ${gb}GB (설치 1.6GB + 스타터킷 0.7GB)"
    } catch { Set-Result 'disk' '디스크 여유 3GB 이상' '기본' $true '확인 불가 — 건너뜁니다' }
}

function Check-Node {
    $r = Invoke-Cmd 'node -v'
    if (-not $r.ok -or -not $r.out) {
        return (Set-Result 'node' 'Node.js 22 이상' '필수' $false '설치 안 됨' 'nodejs.org 에서 LTS 설치' 'https://nodejs.org/ko/download')
    }
    $v = Get-Ver $r.out
    $ok = ($v -ne $null -and $v.Major -ge 22)
    $d = (First-Line $r.out); if (-not $ok) { $d += ' → 22 이상 필요. nodejs.org 에서 LTS 를 덮어 설치' }
    Set-Result 'node' 'Node.js 22 이상' '필수' $ok $d 'nodejs.org 에서 LTS 설치' 'https://nodejs.org/ko/download'
}

function Check-Npm {
    $r = Invoke-Cmd 'npm.cmd -v'
    $ok = ($r.ok -and $r.out -and (Get-Ver $r.out) -ne $null)
    $d = 'Node.js 를 깔면 같이 들어옵니다'; if ($ok) { $d = 'npm ' + (First-Line $r.out) }
    Set-Result 'npm' 'npm (Codex CLI 설치용)' '필수' $ok $d 'Node.js 다시 설치' 'https://nodejs.org/ko/download'
}

function Check-Python {
    $script:PY = $null
    $script:PythonExe = $null
    if (Test-Path -LiteralPath $PYTHON314 -PathType Leaf) {
        $r = Invoke-Cmd "`"$PYTHON314`" -V"
        if ($r.ok -and $r.out -match '^Python 3\.14\.') {
            $script:PY = "`"$PYTHON314`""
            $script:PythonExe = $PYTHON314
            return (Set-Result 'python' 'Python 3.14 (절대경로)' '필수' $true "$(First-Line $r.out) — $PYTHON314")
        }
    }
    Set-Result 'python' 'Python 3.14 (절대경로)' '필수' $false '표준 경로에 Python 3.14가 없습니다. PATH의 다른 버전은 쓰지 않습니다.' '환경점검 자동 설치를 다시 실행하세요' 'https://www.python.org/downloads/windows/'
}

function Check-Pip {
    if (-not $script:PY) { return (Set-Result 'pip' 'pip (파이썬 꾸러미 설치 도구)' '필수' $false 'Python 먼저') }
    $r = Invoke-Cmd "$($script:PY) -m pip --version"
    $ok = ($r.ok -and $r.out -match 'pip')
    $d = 'pip 이 없습니다 → Python 재설치'; if ($ok) { $d = First-Line $r.out }
    Set-Result 'pip' 'pip (파이썬 꾸러미 설치 도구)' '필수' $ok $d
}

function Check-Git {
    $r = Invoke-Cmd 'git --version'
    $ok = ($r.ok -and $r.out -match 'git version')
    $d = '설치 안 됨'; if ($ok) { $d = First-Line $r.out }
    Set-Result 'git' 'Git' '필수' $ok $d 'git-scm.com 에서 설치 (기본값으로 Next 만)' 'https://git-scm.com/download/win'
}

function Check-Codex {
    Refresh-Path
    $r = Invoke-Cmd 'codex.cmd --version' 40
    $ok = $r.ok -and $r.out -match 'codex'
    $d = '실행 실패'; if ($ok) { $d = First-Line $r.out }
    Set-Result 'codex' 'Codex CLI 설치' '필수' $ok $d 'Node.js 22 이상 → npm.cmd install -g @openai/codex' 'https://learn.chatgpt.com/docs/codex'
}

function Check-CodexLogin([switch]$Quiet) {
    if (-not (Is-Ok 'codex')) {
        if ($Quiet) { return $false }
        return (Set-Result 'codex-login' 'Codex CLI 로그인 (ChatGPT 계정)' '필수' $false 'Codex CLI 먼저 설치' '' 'https://chatgpt.com/')
    }
    $r = Invoke-Cmd 'codex.cmd login status' 40
    $logged = $false; $d = '로그인 안 됨'
    if ($r.ok -and $r.out -match 'Logged in') { $logged = $true; $d = First-Line $r.out }
    if ($Quiet) { return $logged }
    Set-Result 'codex-login' 'Codex CLI 로그인 (ChatGPT 계정)' '필수' $logged $d 'codex.cmd login' 'https://chatgpt.com/'
}

function Check-PyPackages {
    $req = @('slack_bolt', 'slack_sdk', 'aiohttp', 'dotenv')
    if (-not (Is-Ok 'python')) {
        Set-Result 'pypkg' '파이썬 꾸러미 4개 (slack-bolt·slack-sdk·aiohttp·python-dotenv)' '필수' $false 'Python 먼저'
        Set-Result 'playwright' 'playwright 패키지 (블로그·이미지 스킬용)' '선택' $false 'Python 먼저'
        return
    }
    $tmp = [IO.Path]::GetTempFileName()
    @'
import importlib
mods = ["slack_bolt","slack_sdk","aiohttp","dotenv","playwright"]
for m in mods:
    try:
        importlib.import_module(m)
        print(m + "=O")
    except Exception:
        print(m + "=X")
'@ | Set-Content -Path $tmp -Encoding ASCII
    $r = Invoke-Cmd "$($script:PY) `"$tmp`"" 40
    Remove-Item $tmp -ErrorAction SilentlyContinue
    $missing = @(); $have = @{}
    foreach ($tok in ($r.out -split '\s+')) {
        if ($tok -match '^(\w+)=(O|X)$') { $have[$Matches[1]] = ($Matches[2] -eq 'O') }
    }
    foreach ($m in $req) { if (-not $have[$m]) { $missing += $m } }
    if ($have.Count -eq 0) {
        Set-Result 'pypkg' '파이썬 꾸러미 4개 (slack-bolt·slack-sdk·aiohttp·python-dotenv)' '필수' $false "확인 실패: $(First-Line $r.out)"
        Set-Result 'playwright' 'playwright 패키지 (블로그·이미지 스킬용)' '선택' $false '확인 실패'
        return
    }
    $d = '4개 모두 실제 import 통과'; if ($missing.Count) { $d = '빠짐: ' + ($missing -join ', ') }
    Set-Result 'pypkg' '파이썬 꾸러미 4개 (slack-bolt·slack-sdk·aiohttp·python-dotenv)' '필수' ($r.ok -and $missing.Count -eq 0) $d "$($script:PY) -m pip install -r slack-server\requirements.txt"
    $pd = 'pip install playwright'; if ($have['playwright']) { $pd = '설치됨' }
    Set-Result 'playwright' 'playwright 패키지 (블로그·이미지 스킬용)' '선택' ([bool]$have['playwright']) $pd "$($script:PY) -m pip install playwright"
}

function Check-Folders {
    # 배포 과정에서 빠진 빈 폴더만 복구한다. 직원 TOML·스킬·기억 파일의 내용은 만들지 않는다.
    $folders = @('.codex\agents', '.agents\skills', 'workspace\inbox', 'workspace\memory', 'workspace\결과물')
    $repairErrors = @()
    foreach ($relative in $folders) {
        $folderPath = Join-Path $KIT $relative
        if (-not (Test-Path -LiteralPath $folderPath -PathType Container)) {
            try {
                if (Test-Path -LiteralPath $folderPath) { throw '같은 이름의 파일이 있습니다.' }
                $null = New-Item -ItemType Directory -Path $folderPath -Force -ErrorAction Stop
                if (-not (Test-Path -LiteralPath $folderPath -PathType Container)) { throw '폴더 생성 결과를 확인할 수 없습니다.' }
            }
            catch { $repairErrors += $relative }
        }
    }
    $missing = @($folders | Where-Object { -not (Test-Path -LiteralPath (Join-Path $KIT $_) -PathType Container) })
    $missing += @(@('slack-server\server.py', '점검.py') | Where-Object { -not (Test-Path -LiteralPath (Join-Path $KIT $_) -PathType Leaf) })
    $d = "정상 — $KIT"
    if ($missing.Count) { $d = '없음 또는 형식 오류: ' + ($missing -join ', ') + ' — 파일 누락은 스타터킷 압축을 다시 풀어 복원하세요' }
    if ($repairErrors.Count) { $d += ' / 폴더 복구 실패: ' + ($repairErrors -join ', ') + ' — 같은 이름의 파일 또는 쓰기 권한을 확인하세요' }
    Set-Result 'folders' '스타터킷 폴더 구조' '필수' ($missing.Count -eq 0) $d
}

function Check-CodexHooks {
    $files = @('.codex/hooks.json','.codex/hooks/runtime.mjs','configure_hooks.ps1')
    $missing = @($files | Where-Object { -not (Test-Path -LiteralPath (Join-Path $KIT $_)) })
    Set-Result 'codex-hooks' 'Codex 자동 기록·저장·차단 파일' '필수' ($missing.Count -eq 0) '파일 존재 검사입니다. /hooks에서 신뢰하고 작업기록의 실행 확인을 별도로 보세요.' '스타터킷 재설치 후 /hooks 검토·신뢰'
}

function Check-MyData {
    # 표준 설치(C:\Agent\01_KIT\starter-kit)면 두 단계 위가 회사 건물 — 그 안의 MyData\ 를 센다
    $root = Split-Path -Parent $COURSE
    $base = Join-Path $root 'MyData'
    if ((Split-Path -Leaf $COURSE) -ne '01_KIT' -or -not (Test-Path $base)) {
        Set-Result 'mydata' '내 자료 (제안서 3·블로그 3·로고 1)' '선택' $false 'MyData 폴더 없음 — 표준 설치가 아니면 건너뜁니다'
        return
    }
    $n = @{}
    foreach ($k in 'Proposal','Blog','Logo','Profile') {
        $n[$k] = @(Get-ChildItem -LiteralPath (Join-Path $base $k) -File -ErrorAction SilentlyContinue).Count
    }
    $ok = ($n['Proposal'] -ge 3) -and ($n['Blog'] -ge 3) -and ($n['Logo'] -ge 1)
    $d = "제안서(Proposal) $($n['Proposal'])개 · 블로그(Blog) $($n['Blog'])개 · 로고(Logo) $($n['Logo'])개 · 프로필(Profile) $($n['Profile'])개 — $base"
    Set-Result 'mydata' '내 자료 (제안서 3·블로그 3·로고 1)' '선택' $ok $d "$base 에 파일을 넣으세요 (모듈 3.5 전까지)"
}

function Check-SlackEnv {
    if ($SkipSlack -or $SkipLogin) {
        return (Set-Result 'slack' '슬랙 열쇠 3개 (.env)' '필수' $false '옵션으로 생략 — 확인하지 않음')
    }
    $envFile = Join-Path $KIT 'slack-server\.env'
    $values = @{}
    if (Test-Path -LiteralPath $envFile) {
        foreach ($line in [IO.File]::ReadAllLines($envFile, [Text.Encoding]::UTF8)) {
            if ($line -match '^\s*(?:export\s+)?(SLACK_BOT_TOKEN|SLACK_APP_TOKEN|OWNER_USER_ID)\s*=\s*(.*?)\s*$') {
                $values[$Matches[1]] = $Matches[2].Trim('"').Trim("'")
            }
        }
    }
    $problems = @()
    foreach ($key in @('SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'OWNER_USER_ID')) {
        if (-not (Test-SlackValue $key $values[$key])) { $problems += "$key 비어 있거나 형식 오류" }
    }
    $detail = '봇 토큰·앱 토큰·멤버 ID 형식 정상 (유효성은 다음 연결 검사에서 확인)'
    if ($problems.Count) { $detail = $problems -join ' / ' }
    Set-Result 'slack' '슬랙 열쇠 3개 (.env)' '필수' ($problems.Count -eq 0) $detail '교안 2~3쪽에서 준비한 값 3개를 환경점검에 붙여넣으세요'
}

function Test-SlackValue([string]$key, [string]$value) {
    switch ($key) {
        'SLACK_BOT_TOKEN' { return $value -match '^xoxb-[A-Za-z0-9-]+$' }
        'SLACK_APP_TOKEN' { return $value -match '^xapp-[A-Za-z0-9-]+$' }
        'OWNER_USER_ID' { return $value -match '^[UW][A-Z0-9]{8,}$' }
    }
    return $false
}

function Check-VSCode {
    $p = Has-Cmd 'code'
    if (-not $p) { foreach ($c in @("$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe", "$env:ProgramFiles\Microsoft VS Code\Code.exe")) { if (Test-Path $c) { $p = $c } } }
    $d = '없어도 실습됩니다 (약 350MB)'; if ($p) { $d = $p }
    Set-Result 'vscode' 'VS Code' '선택' ([bool]$p) $d 'code.visualstudio.com' 'https://code.visualstudio.com/'
}

function Check-Chrome {
    $p = $null
    foreach ($c in @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")) { if (Test-Path $c) { $p = $c } }
    $d = '네이버 블로그·Google Flow 스킬이 실제 Chrome 을 씁니다'; if ($p) { $d = $p }
    Set-Result 'chrome' 'Google Chrome (블로그·이미지 스킬용)' '선택' ([bool]$p) $d 'google.com/chrome' 'https://www.google.com/chrome/'
}

function Check-FlowLogin {
    $prof = Join-Path $USERHOME '.codex\.image-flow-profile'
    $ok = (Test-Path $prof) -and (@(Get-ChildItem $prof -Force -ErrorAction SilentlyContinue).Count -gt 0)
    $d = '아직 로그인 안 함 (Gemini 구독 계정 필요, 세션 약 8시간)'; if ($ok) { $d = "로그인 기록 있음 — $prof" }
    Set-Result 'flow-login' 'Google Flow 로그인 (이미지 스킬)' '선택' $ok $d "`"$PYTHON314`" flow-image-JJ\scripts\flow_login.py" 'https://labs.google/fx/tools/flow'
}

function Check-NaverLogin {
    $state = Join-Path $KIT 'naver-blog\.naver-state.json'
    $ok = Test-Path $state
    $d = '아직 로그인 안 함'; if ($ok) { $d = '세션 파일 있음 (.naver-state.json)' }
    Set-Result 'naver-login' '네이버 블로그 로그인 (블로그 스킬)' '선택' $ok $d "`"$PYTHON314`" naver-blog\naver_draft.py login --blog-id 내아이디" 'https://blog.naver.com/'
}

# ── 4. 고치기 (설치·로그인) ───────────────────────────────────
function Install-WithWinget([string]$id, [string]$label, [string]$override = '') {
    if ($SkipInstall) { return }
    Write-Info "$label 설치를 확인합니다 (묻지 않습니다)."
    $arguments = @('install', '--exact', '--id', $id, '--accept-package-agreements', '--accept-source-agreements', '--silent', '--disable-interactivity')
    if ($override) { $arguments += @('--override', $override) }
    try { & winget @arguments | Out-Host } catch { Write-Warn "$label 설치 실행 실패" }
    Refresh-Path
}

function Fix-Programs {
    if ($SkipInstall) { Write-Info '(-SkipInstall) 프로그램 설치 생략'; return }
    $todo = @()
    if (-not (Is-Ok 'node') -or -not (Is-Ok 'npm')) { $todo += @{ id='OpenJS.NodeJS.LTS'; label='Node.js LTS (22 이상)'; url='https://nodejs.org/ko/download' } }
    if (-not (Is-Ok 'git')) { $todo += @{ id='Git.Git'; label='Git'; url='https://git-scm.com/download/win' } }
    foreach ($item in $todo) {
        if (Has-Cmd 'winget') { Install-WithWinget $item.id $item.label }
        else { Write-Warn "winget이 없어 $($item.label) 자동 설치 불가"; Open-Url $item.url }
    }
    Check-Node | Out-Null
    Check-Npm | Out-Null
    Check-Git | Out-Null
}

function Fix-Python {
    if ($SkipInstall) { Write-Info '(-SkipInstall) Python 설치·설정 생략'; return }
    if (Has-Cmd 'winget') {
        # 3.14가 있더라도 설치 상태를 확인합니다. 다른 Python과 공존하며 기본 실행기를 바꾸지 않습니다.
        $options = '/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_pip=1 Include_test=0 TargetDir="' + (Split-Path $PYTHON314) + '"'
        Install-WithWinget 'Python.Python.3.14' 'Python 3.14' $options
    } elseif (-not (Is-Ok 'python')) {
        Write-Warn 'winget이 없어 Python 3.14 자동 설치 불가 — 표준 사용자 경로에 설치하세요.'
        Open-Url 'https://www.python.org/downloads/windows/'
    }
    Check-Python | Out-Null
    Check-Pip | Out-Null
}

function Fix-Codex {
    if ($SkipInstall -or (Is-Ok 'codex')) { return }
    if (-not (Is-Ok 'node') -or -not (Is-Ok 'npm')) { Write-Warn 'Node.js 22 이상과 npm.cmd가 먼저 필요합니다.'; return }
    Write-Step 'Codex CLI 자동 설치 — npm.cmd install -g @openai/codex'
    try { & npm.cmd install -g '@openai/codex' | Out-Host } catch { Write-Warn 'Codex CLI 설치 실행 실패' }
    Refresh-Path
    Check-Codex | Out-Null
}

function Fix-CodexLogin {
    if ((Is-Ok 'codex-login') -or -not (Is-Ok 'codex')) { return }
    if ($SkipLogin) { Write-Info '(-SkipLogin) 로그인 생략'; return }
    Write-Step 'Codex CLI 로그인 — 새 창과 브라우저가 열립니다'
    Write-Info '브라우저에서 본인의 ChatGPT 계정으로 로그인하세요. 무료 계정도 가능하지만 사용량 제한이 있습니다.'
    Write-Info '이 창은 로그인이 끝나는 걸 자동으로 감지합니다 (최대 10분).'
    Open-NewWindow 'Codex-로그인' 'codex.cmd login'
    $deadline = (Get-Date).AddMinutes(10)
    $logged = $false
    while ((Get-Date) -lt $deadline) {
        if (Check-CodexLogin -Quiet) { $logged = $true; break }
        Write-Host -NoNewline '.' -ForegroundColor DarkGray
        Start-Sleep -Seconds 5
    }
    Write-Host ''
    if (-not $logged) { Write-Warn '10분 안에 로그인이 확인되지 않았습니다. 로그인 후 다시 실행하세요.' }
    Check-CodexLogin | Out-Null
}

function Fix-PyPackages {
    if ($SkipInstall -or -not $script:PythonExe) { return }
    $requirements = Join-Path $KIT 'slack-server\requirements.txt'
    if (-not (Test-Path -LiteralPath $requirements)) { Write-Warn 'requirements.txt가 없습니다.'; return }
    Write-Step 'Python 3.14 꾸러미 자동 설치·실제 import 확인'
    try {
        & $script:PythonExe -m ensurepip --upgrade | Out-Host
        & $script:PythonExe -m pip install --disable-pip-version-check -r $requirements playwright | Out-Host
    } catch { Write-Warn '꾸러미 설치 실행 실패 — 아래 import 결과를 확인하세요.' }
    Check-Pip | Out-Null
    Check-PyPackages | Out-Null
    if (-not (Is-Ok 'pypkg')) { Write-Warn '필수 꾸러미를 불러오지 못했습니다. 인터넷·기관 보안정책을 확인하세요.' }
}

function Read-Secret([string]$key) {
    while ($true) {
        $secure = Read-Host "  $key 붙여넣기 (나중에 하려면 s)" -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try { $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer).Trim().Trim('"').Trim("'") }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
        if ($value -eq 's') { return $null }
        if (Test-SlackValue $key $value) { Write-Info "$key 입력됨 (값 비표시)"; return $value }
        Write-Warn "$key 형식을 확인하세요. 값은 화면에 표시하지 않습니다."
    }
}

function Save-SlackValues([string]$Path, [hashtable]$Values) {
    # 줄 단위로 해당 세 키만 갱신합니다. 다른 설정·주석과 템플릿은 유지합니다.
    $source = $Path
    if (-not (Test-Path -LiteralPath $source)) { $source = Join-Path (Split-Path $Path) '.env.example' }
    $lines = @(); if (Test-Path -LiteralPath $source) { $lines = [IO.File]::ReadAllLines($source, [Text.Encoding]::UTF8) }
    $seen = @{}
    $output = New-Object 'System.Collections.Generic.List[string]'
    foreach ($line in $lines) {
        if ($line -match '^\s*(?:export\s+)?(SLACK_BOT_TOKEN|SLACK_APP_TOKEN|OWNER_USER_ID)\s*=') {
            $key = $Matches[1]
            if (-not $seen.ContainsKey($key)) { $output.Add("$key=$($Values[$key])"); $seen[$key] = $true }
        } else { $output.Add($line) }
    }
    foreach ($key in @('SLACK_BOT_TOKEN','SLACK_APP_TOKEN','OWNER_USER_ID')) {
        if (-not $seen.ContainsKey($key)) { $output.Add("$key=$($Values[$key])") }
    }
    [IO.File]::WriteAllText($Path, (($output -join "`n") + "`n"), (New-Object Text.UTF8Encoding($false)))
}

function Fix-Slack {
    if ($SkipSlack -or $SkipLogin -or (Is-Ok 'slack')) { return }
    Write-Step '준비한 슬랙 열쇠 3개 입력 — 화면에는 가려집니다'
    $values = @{}
    foreach ($key in @('SLACK_BOT_TOKEN','SLACK_APP_TOKEN','OWNER_USER_ID')) {
        $value = Read-Secret $key
        if (-not $value) { Write-Info '입력을 생략했습니다. 기존 .env는 그대로 유지됩니다.'; return }
        $values[$key] = $value
    }
    try {
        Save-SlackValues (Join-Path $KIT 'slack-server\.env') $values
        Write-Info '.env 저장됨 (UTF-8 BOM 없음, 기존 다른 설정 유지)'
    } catch { Write-Warn '.env 저장 실패 — 폴더 쓰기 권한을 확인하세요.'; return }
    finally { $values.Clear(); $value = $null }
    Check-SlackEnv | Out-Null
}

function Test-SlackLive {
    if ($SkipSlack -or $SkipLogin) {
        Set-Result 'slack-live' '슬랙 실제 인증' '필수' $false '옵션으로 생략 — 외부 연결하지 않음'; return
    }
    if (-not (Is-Ok 'slack') -or -not (Is-Ok 'pypkg') -or -not $script:PY) {
        Set-Result 'slack-live' '슬랙 실제 인증' '필수' $false '열쇠 3개와 Python 꾸러미를 먼저 준비하세요'; return
    }
    $check = Join-Path $KIT 'slack-server\slack_check.py'
    if (-not (Test-Path -LiteralPath $check)) { Set-Result 'slack-live' '슬랙 실제 인증' '필수' $false 'slack_check.py 누락'; return }
    $result = Invoke-Cmd "$($script:PY) -X utf8 `"$check`"" 60
    # 검사 도구의 출력에도 원문 응답이나 열쇠가 섞일 수 있어 결과에는 고정 문구만 사용합니다.
    $detail = 'slack_check.py 인증 검사 통과'
    if (-not $result.ok) { $detail = "인증 검사 실패 (종료코드 $($result.code)). .env와 앱 설정·인터넷을 확인하세요." }
    Set-Result 'slack-live' '슬랙 실제 인증' '필수' $result.ok $detail 'slack_check.py를 직접 실행하여 항목별 오류 안내를 확인하세요'
}

function Test-Server {
    if ($NoServerTest -or $SkipSlack -or $SkipLogin) {
        Set-Result 'server' '슬랙 서버 첫 기동·Socket Mode 연결' '필수' $false '옵션으로 생략 — 기동하지 않음'; return
    }
    if (-not (Is-Ok 'slack-live') -or -not $script:PythonExe) {
        Set-Result 'server' '슬랙 서버 첫 기동·Socket Mode 연결' '필수' $false '실제 인증 검사를 먼저 통과하세요'; return
    }
    Write-Step '슬랙 서버 첫 기동 시험 (최대 90초, 시험 프로세스만 종료)'
    $stdout = [IO.Path]::GetTempFileName()
    $stderr = [IO.Path]::GetTempFileName()
    $process = $null; $ok = $false; $detail = '90초 안에 Socket Mode 실제 연결을 확인하지 못했습니다.'
    try {
        $process = Start-Process -FilePath $script:PythonExe -ArgumentList '-X','utf8','-u','server.py','--startup-test' -WorkingDirectory (Join-Path $KIT 'slack-server') -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
        $null = $process.Handle
        $deadline = (Get-Date).AddSeconds(90)
        while ((Get-Date) -lt $deadline) {
            $text = [IO.File]::ReadAllText($stdout, [Text.Encoding]::UTF8) + [IO.File]::ReadAllText($stderr, [Text.Encoding]::UTF8)
            if ($text -match '(?m)^WD_SOCKET_CONNECTED\s*$') { $ok = $true; $detail = '서버가 Socket Mode 연결을 확인했습니다 (WD_SOCKET_CONNECTED).'; break }
            if ($process.HasExited) { $detail = "연결 확인 전 서버 종료 (종료코드 $($process.ExitCode))"; break }
            Start-Sleep -Seconds 1
        }
    } catch { $detail = '서버 실행 또는 연결 확인 실패 — Python 경로·파일·권한을 확인하세요.' }
    finally {
        if ($process) { if (-not $process.HasExited) { try { $process.Kill(); $process.WaitForExit() } catch {} }; $process.Dispose() }
        Remove-Item -LiteralPath $stdout,$stderr -ErrorAction SilentlyContinue
    }
    Set-Result 'server' '슬랙 서버 첫 기동·Socket Mode 연결' '필수' $ok $detail '환경점검을 다시 실행하거나 서버 시작 창의 오류 안내를 확인하세요'
}

function Install-SlackAutostart {
    if ($NoServerTest -or $SkipSlack -or $SkipLogin) {
        Set-Result 'slack-autostart' '슬랙 서버 숨김 자동 시작' '필수' $false '옵션으로 생략 — 자동 시작을 설치하지 않음'; return
    }
    if (-not (Is-Ok 'server')) {
        Set-Result 'slack-autostart' '슬랙 서버 숨김 자동 시작' '필수' $false 'Socket Mode 연결 시험을 먼저 통과하세요'; return
    }
    $installer = Join-Path $KIT 'slack-server\install_autostart.ps1'
    if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
        Set-Result 'slack-autostart' '슬랙 서버 숨김 자동 시작' '필수' $false 'install_autostart.ps1 누락'; return
    }
    Write-Step '슬랙 서버 숨김 자동 시작 등록'
    try {
        $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer 2>&1
        $ok = ($LASTEXITCODE -eq 0) -and (($output -join "`n") -match 'WD_AUTOSTART_OK')
        $detail = if ($ok) { 'Windows 로그인 시 자동 시작·종료 시 자동 재시작 등록됨 (검은 창 없음)' } else { '예약 작업 등록 실패 — Windows 작업 스케줄러 권한을 확인하세요' }
        Set-Result 'slack-autostart' '슬랙 서버 숨김 자동 시작' '필수' $ok $detail 'install_autostart.ps1을 PowerShell에서 다시 실행하세요'
    } catch {
        Set-Result 'slack-autostart' '슬랙 서버 숨김 자동 시작' '필수' $false "등록 실패: $($_.Exception.Message)" 'install_autostart.ps1을 PowerShell에서 다시 실행하세요'
    }
}

function Fix-OptionalLogins {
    if ($SkipLogin -or -not $OptionalLogins) { return }
    if (-not ((Is-Ok 'python') -and (Is-Ok 'playwright') -and (Is-Ok 'chrome'))) { return }
    if (-not (Is-Ok 'flow-login')) {
        $script_ = Join-Path $KIT 'flow-image-JJ\scripts\flow_login.py'
        if (Test-Path $script_) {
            Open-NewWindow 'Google-Flow-로그인' "$($script:PY) `"$script_`"" (Split-Path $script_)
            Wait-Enter '크롬 창에서 Google 로그인을 마치고 "[OK] 로그인 완료" 가 뜨면'
            Check-FlowLogin | Out-Null
        }
    }
    if (-not (Is-Ok 'naver-login')) {
        $script_ = Join-Path $KIT 'naver-blog\naver_draft.py'
        if (Test-Path $script_) {
            $bid = Read-Host '  ? 네이버 블로그 아이디 (blog.naver.com/뒤에 오는 것, 비우면 건너뜀)'
            if ($bid -match '^[A-Za-z0-9_-]+$') {
                Open-NewWindow 'Naver-Blog-로그인' "$($script:PY) `"$script_`" login --blog-id $($bid.Trim())" (Split-Path $script_)
                Wait-Enter '크롬 창에서 네이버 로그인을 마치고 "[OK]" 가 뜨면'
                Check-NaverLogin | Out-Null
            }
        }
    }
}

# ── 5. 결과 HTML ─────────────────────────────────────────────
$WD_SYMBOL_B64 = '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'

function Html([string]$s) { return [System.Net.WebUtility]::HtmlEncode($s) }

function Write-Report {
    $req = @($script:Results | Where-Object { $_.Group -ne '선택' })
    $opt = @($script:Results | Where-Object { $_.Group -eq '선택' })
    $reqOk = @($req | Where-Object { $_.Ok }).Count
    $optOk = @($opt | Where-Object { $_.Ok }).Count
    $allOk = ($reqOk -eq $req.Count)
    $verdict = '아직 준비가 덜 됐습니다 — ❌ 줄만 고치면 됩니다'
    $verdictClass = 'bad'
    if ($allOk) { $verdict = '출발 준비 완료! 강의 당일 바로 시작할 수 있습니다'; $verdictClass = 'good' }

    $sb = New-Object System.Text.StringBuilder
    $null = $sb.Append(@"
<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>환경 점검 결과 — 에이전트팀 만들기</title>
<style>
:root{--p:#7B2D8E;--deep:#3D1249;--dark:#5A1E6B;--band:#F8F5FA;--line:#E8DEF0;--ok:#1E9E5A;--no:#E84393;--gold:#F5A623;--ink:#1f1a24}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:var(--ink);font-family:"Noto Sans KR","Noto Sans Korean","Noto Sans CJK KR","NotoSansKR","Malgun Gothic","맑은 고딕",sans-serif;line-height:1.55}
code,pre{font-family:"Noto Sans KR","Noto Sans Korean","Noto Sans CJK KR","NotoSansKR","Malgun Gothic","맑은 고딕",sans-serif}
.nav{display:flex;align-items:center;gap:12px;padding:14px 32px;border-bottom:1px solid var(--line)}
.nav img{height:38px;width:auto}
.nav .t{font-weight:700;color:var(--deep)}
.nav .s{color:#6b6470;font-size:13px;margin-left:auto}
.wrap{max-width:960px;margin:0 auto;padding:48px 24px 80px}
h1{margin:0 0 8px;font-size:30px;color:var(--deep);letter-spacing:-.01em}
.lede{margin:0 0 28px;color:#5c5661}
.verdict{border-radius:16px;padding:22px 26px;margin:0 0 36px;font-size:19px;font-weight:700;display:flex;align-items:center;gap:14px}
.verdict.good{background:#eaf7ef;color:#155c36;border:1px solid #bfe6cf}
.verdict.bad{background:#fdeef5;color:#8a1e4f;border:1px solid #f6c6dc}
.verdict .n{font-size:14px;font-weight:500;margin-left:auto;opacity:.8}
h2{font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:var(--p);margin:36px 0 12px}
table{width:100%;border-collapse:collapse;border:1px solid var(--line);border-radius:16px;overflow:hidden}
th{background:var(--dark);color:#fff;text-align:left;font-weight:600;font-size:13px;padding:10px 14px}
td{padding:12px 14px;border-top:1px solid var(--line);vertical-align:top;font-size:14px}
tr:nth-child(even) td{background:var(--band)}
td.m{width:44px;text-align:center;font-size:18px}
td.name{font-weight:600;width:34%}
.detail{color:#5c5661}
.fix{color:var(--deep);margin-top:4px;font-size:13px}
.fix a{color:var(--p);font-weight:600;text-decoration:none}
.fix a:hover{text-decoration:underline}
.slab{margin-top:56px;background:var(--deep);color:#eadff0;border-radius:16px;padding:28px 30px}
.slab b{color:#A855F7}
.slab ol{margin:8px 0 0 18px;padding:0}
.foot{margin-top:18px;font-size:12px;color:#8a8390}
@media print{.nav{border:0}.slab{background:#fff;color:#000;border:1px solid #ccc}}
</style></head><body>
<div class="nav"><img alt="WITH DREAM" src="data:image/png;base64,$WD_SYMBOL_B64"><span class="t">에이전트팀 만들기 과정</span><span class="s">환경 점검 · $($STARTED.ToString('yyyy-MM-dd HH:mm'))</span></div>
<div class="wrap">
<h1>출발선 점검 결과</h1>
<p class="lede">$(Html $env:COMPUTERNAME) · $(Html $KIT)</p>
<div class="verdict $verdictClass"><span>$(if($allOk){'🎉'}else{'🛠'})</span><span>$verdict</span><span class="n">필수 $reqOk/$($req.Count) · 선택 $optOk/$($opt.Count)</span></div>
"@)

    foreach ($grp in @(@('필수 — 이게 다 ✅ 여야 수업을 시작할 수 있습니다', $req), @('선택 — 없어도 실습되지만, 집에서 스킬을 쓰려면 필요합니다', $opt))) {
        $null = $sb.Append("<h2>$($grp[0])</h2><table><tr><th></th><th>항목</th><th>확인 결과</th></tr>")
        foreach ($r in $grp[1]) {
            $m = '❌'; if ($r.Ok) { $m = '✅' }
            $fix = ''
            if (-not $r.Ok -and ($r.Fix -or $r.Url)) {
                $fix = '<div class="fix">→ ' + (Html $r.Fix)
                if ($r.Url) { $fix += " <a href=`"$($r.Url)`" target=`"_blank`" rel=`"noopener`">$(Html $r.Url)</a>" }
                $fix += '</div>'
            }
            $null = $sb.Append("<tr><td class=`"m`">$m</td><td class=`"name`">$(Html $r.Name)</td><td><div class=`"detail`">$(Html $r.Detail)</div>$fix</td></tr>")
        }
        $null = $sb.Append('</table>')
    }

    $null = $sb.Append(@"
<div class="slab"><b>다음 할 일</b>
<ol>
<li>❌ 가 있으면 그 줄의 안내대로 고치고 <b>환경점검.bat</b> 을 다시 더블클릭합니다.</li>
<li>전부 ✅ 면 검은 창에서 <b>&amp; &quot;$PYTHON314&quot; 점검.py 0</b> 으로 한 번 더 확인하고, 프롬프트카드.md 의 모듈 0 부터 시작합니다.</li>
<li>슬랙 열쇠 3개는 <b>교안 2~3쪽에서 먼저 준비</b>합니다. Google Flow·네이버 로그인은 집에서 스킬을 쓸 때 하면 됩니다.</li>
</ol>
<div class="foot">입력한 열쇠는 .env에만 저장하며 화면과 보고서에는 표시하지 않습니다.  로그인은 항상 본인이 직접 합니다. · 위드드림컨설팅</div>
</div>
</div></body></html>
"@)
    [IO.File]::WriteAllText($REPORT, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
}

# ── 6. 실행 ──────────────────────────────────────────────────
Write-Host ''
Write-Host '  ┌──────────────────────────────────────────────────┐' -ForegroundColor Magenta
Write-Host '  │   에이전트팀 만들기 과정 — 출발선 자동 점검      │' -ForegroundColor Magenta
Write-Host '  └──────────────────────────────────────────────────┘' -ForegroundColor Magenta
Write-Info "스타터킷: $KIT"
if ($PretendMissing.Count) { Write-Warn "테스트 모드 — 없는 것으로 가정: $($PretendMissing -join ', ')" }

$script:PY = $null

Write-Info 'npm.cmd·codex.cmd를 사용하므로 사용자 실행 정책을 영구 변경하지 않습니다.'
Write-Step '1/6 기본 확인'
Check-Internet | Out-Null
Check-Disk | Out-Null

Write-Step '2/6 프로그램 확인'
Check-Node | Out-Null
Check-Npm | Out-Null
Check-Python | Out-Null
Check-Pip | Out-Null
Check-Git | Out-Null
Check-Codex | Out-Null
Check-VSCode | Out-Null
Check-Chrome | Out-Null
Fix-Programs
Fix-Python
Fix-Codex

Write-Step '3/6 Codex CLI 로그인'
Check-CodexLogin | Out-Null
Fix-CodexLogin

Write-Step '4/6 파이썬 꾸러미'
Check-PyPackages | Out-Null
Fix-PyPackages

Write-Step '5/6 스타터킷 · 슬랙'
Check-Folders | Out-Null
Check-MyData | Out-Null
Check-CodexHooks | Out-Null
Check-SlackEnv | Out-Null
Fix-Slack
Test-SlackLive | Out-Null
Test-Server | Out-Null
Install-SlackAutostart | Out-Null

Write-Step '6/6 선택 항목 (OptionalLogins 지정 시에만 로그인)'
Check-FlowLogin | Out-Null
Check-NaverLogin | Out-Null
Fix-OptionalLogins

# ── 7. 최종 체크리스트 ───────────────────────────────────────
Write-Host ''
Write-Host '  ══════════════════ 체크리스트 ══════════════════' -ForegroundColor Magenta
$req = @($script:Results | Where-Object { $_.Group -ne '선택' })
$opt = @($script:Results | Where-Object { $_.Group -eq '선택' })
Write-Host '  [필수]' -ForegroundColor White
foreach ($r in $req) { $m = $NOM; $c = 'Red'; if ($r.Ok) { $m = $OKM; $c = 'Green' }; Write-Host "  $m $($r.Name)" -ForegroundColor $c; if (-not $r.Ok) { Write-Host "        └ $($r.Detail)" -ForegroundColor DarkGray; if ($r.Fix) { Write-Host "        └ 고치기: $($r.Fix)" -ForegroundColor Yellow } } }
Write-Host '  [선택]' -ForegroundColor White
foreach ($r in $opt) { $m = $NOM; $c = 'Red'; if ($r.Ok) { $m = $OKM; $c = 'Green' }; Write-Host "  $m $($r.Name)" -ForegroundColor $c }
$reqOk = @($req | Where-Object { $_.Ok }).Count
$optOk = @($opt | Where-Object { $_.Ok }).Count
Write-Host '  ─────────────────────────────────────────────────' -ForegroundColor Magenta
if ($reqOk -eq $req.Count) {
    Write-Host "  🎉 필수 $reqOk/$($req.Count) 전부 통과 · 선택 $optOk/$($opt.Count) — 출발 준비 완료! codex.cmd 실행 → 프로젝트 신뢰 → /hooks 검토·신뢰." -ForegroundColor Green
} else {
    Write-Host "  필수 $reqOk/$($req.Count) 통과 · 선택 $optOk/$($opt.Count) — ❌ 표시된 것만 고치고 다시 실행하세요." -ForegroundColor Yellow
}

try { Write-Report; Write-Info "결과 파일: $REPORT"; if (-not $NoBrowser) { Start-Process $REPORT } } catch { Write-Warn "HTML 저장 실패: $_" }
Write-Info ("소요 {0:n0}초" -f ((Get-Date) - $STARTED).TotalSeconds)

if (-not $NoPause) { $null = Read-Host '  창을 닫으려면 Enter' }
if ($reqOk -eq $req.Count) { exit 0 } else { exit 1 }



