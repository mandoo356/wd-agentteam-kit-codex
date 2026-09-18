# 위드드림 AI 에이전트팀 — 스타터킷

「에이전트팀 만들기 과정」 수강생용 스타터킷입니다. 프로그램을 내려받아 설치하는 게 아니라, **명령어 한 줄**로 설치합니다.

## 설치 (한 줄)

1. 시작 메뉴에서 **PowerShell** 을 엽니다. (Windows PowerShell / 관리자 권한 필요 없음)
2. 아래 한 줄을 붙여넣고 Enter. (붙여넣기는 **마우스 오른쪽 클릭**)

```powershell
irm https://raw.githubusercontent.com/mandoo356/wd-agentteam-kit-codex/main/install.ps1 | iex
```

## 기본 설치 — PowerShell 또는 CMD 한 줄

PowerShell:
```powershell
irm https://raw.githubusercontent.com/mandoo356/wd-agentteam-kit-codex/main/install.ps1 | iex
```
CMD(명령 프롬프트):
```bat
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/mandoo356/wd-agentteam-kit-codex/main/install.ps1 | iex"
```
Node.js 설치 후 Codex만 설치할 때는 두 창 모두 `npm.cmd install -g @openai/codex`를 사용합니다. 로그인은 `codex.cmd login`입니다.
PowerShell 자체가 기관 정책으로 차단되면 CMD 한 줄도 작동하지 않습니다. 별책의 수동 설치 절차를 참고하고, 훅을 포함한 전 과정 실습은 PowerShell을 사용할 수 있는 Windows 노트북에서 진행합니다.

별책: `05_검은창_매뉴얼_CMD와PowerShell_WD.html` (배포본에서는 `docs/`)

## 이 한 줄이 하는 일

| 단계 | 내용 | 걸리는 시간 |
|---|---|---|
| 1 | 깃허브에서 스타터킷을 받는다 (약 3MB, `node_modules`·비밀키 없음) | 수 초 |
| 2 | `C:\Agent\01_KIT\starter-kit` 에 표준 설치한다. `C:\Agent\MyData\`도 같이 만든다 | 수 초 |
| 3 | 환경점검을 이어서 돌린다 — Node·Git·Python·Codex CLI가 없으면 **명령어(winget/npm)로 설치**하고 ChatGPT 로그인을 연다 | 없는 것에 따라 몇 분 |

기존 설치가 있으면 사용자 작업·비밀키는 보존하고 실행 파일을 최신 Codex판으로 갱신합니다. 인터넷이 켜져 있어야 합니다.

## 설치 후

- `C:\Agent\01_KIT\starter-kit\README.md` — 폴더 설명과 카드 사용법
- `C:\Agent\MyData\` — **제안서 3개·블로그 글 3개·회사 로고**를 수업 전에 넣어 두는 곳 (`Proposal\` 제안서 · `Blog\` 블로그 · `Logo\` 로고 · `Profile\` 프로필)
- `프롬프트카드.md` — 강의장에서 모듈 0~6 순서대로
- 가상 오피스(`office/`)는 모듈 5에서 `npm ci` 로 의존성을 내려받습니다 (약 690MB, 인터넷 속도에 따라 다름)

## 이 저장소에 없는 것

`.env`(슬랙 열쇠), 로그인 상태, `node_modules`, 캐시·로그는 들어 있지 않습니다. 보안상 정상입니다.

---
위드드림컨설팅 교육용 · `starter-kit/` 원본은 강사 PC에서 `03_깃허브_배포_갱신.bat` 으로 갱신됩니다.

## 자동 기록·저장·위험 작업 확인 — Codex판

1. 설치 후 `01_Codex_YOLO_시작.bat`에서 프로젝트를 신뢰하고 `/hooks`를 엽니다. 새로 추가·변경된 5개 이벤트를 검토하고 신뢰합니다. 업데이트 뒤에도 다시 확인합니다.
2. `workspace/기록/작업기록_날짜.md`에 **Codex 훅 실행 확인**이 남는지 확인합니다. 파일 존재 점검만으로 작동을 보증하지 않습니다.
3. 요청 접수·도구 종료·변경 파일·차단 이유가 한글로 기록됩니다. 요청 원문과 명령 인수는 비밀키 노출을 줄이기 위해 기록하지 않습니다.
4. `git init` 후 답변 종료 시 결과물·직원·스킬·팀 규약 변경을 자동 커밋합니다. 변경이 없거나 사용자가 이미 스테이징한 파일이 있으면 생략합니다. 기록 파일만으로 커밋을 만들지 않습니다. 전체 회사 보관은 `02_내작업_백업.bat`을 사용합니다.
5. 삭제·이동·되돌리기·셸 덮어쓰기·보호 파일 편집은 훅이 **차단**합니다. Codex의 PreToolUse 훅은 `ask` 확인창을 지원하지 않습니다. 대상을 확인하고 백업한 뒤 사람이 별도 터미널에서 직접 명령을 실행합니다. 슬랙에서는 터미널로 안내합니다.
6. 일반 문서는 `apply_patch`로 수정하고, 최초 직원·스킬·규약 파일 생성은 허용합니다. 보호 대상은 `.codex/`, `.agents/`, `AGENTS.md`, `workspace/memory/`, 회사 설정·열쇠입니다.
7. 훅은 보조 안전장치입니다. 임의 프로그램·모든 외부 도구를 완벽히 통제하지 않으며, YOLO는 운영체제 샌드박스를 해제합니다. 훅을 신뢰하지 않았거나 꺼 두면 보호·기록이 작동하지 않습니다.

설치 위치를 옮겼으면 `powershell -NoProfile -ExecutionPolicy Bypass -File configure_hooks.ps1`을 실행한 뒤 `/hooks`에서 다시 신뢰하세요. 자동화는 이미 설치하는 **Node.js 22 이상**으로 실행하여 Python 실행기 버전 충돌을 줄였습니다.

확인 명령: `git log --oneline -10`. 복원은 `git diff`로 변경을 살펴보고 백업한 뒤 `git restore --source=커밋번호 -- 파일경로`를 사람이 직접 실행합니다.

공식 근거: https://learn.chatgpt.com/docs/hooks

---

## 저작권

© 2026 **위드드림컨설팅**(With Dream Consulting) · 김민주. All rights reserved.

「에이전트팀 만들기 과정」 수강생용 자료입니다. **본인 업무에는 마음껏 쓰십시오** —
고쳐 쓰셔도 되고, 이걸로 만든 제안서·교재·블로그 글을 상업적으로 쓰셔도 됩니다.

다만 아래는 **사전 서면 허락이 필요합니다.**

- 스타터킷을 제3자에게 배포·공유하는 것 (원본이든 고친 것이든)
- 이 자료로 교육·강의·워크숍·컨설팅을 제공하는 것
- 교안·프롬프트 카드를 복제·전재·2차 저작하는 것

> 공개 저장소에 올려둔 것은 **수강생의 한 줄 설치를 위한 것**이며, 누구나
> 재배포해도 된다는 뜻이 아닙니다. 자세한 내용은 [LICENSE](LICENSE) 를 보세요.
> 재배포·협업을 원하시면 연락 주십시오 — 막으려는 게 아니라 **이야기하고 쓰자**는 뜻입니다.
