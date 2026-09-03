# Google Flow 내부 구조 (실측 기반)

헤드리스/헤드풀 Playwright로 직접 확인한 내용.
UI가 바뀌어 스크립트가 깨지면 `flow_probe.py` 로 재파악한 뒤 이 문서를 갱신할 것.

## 목차
- [로그인 판정](#로그인-판정)
- [헤드리스는 생성이 차단된다](#-헤드리스는-생성이-차단된다)
- [화면 진입 경로](#화면-진입-경로)
- [설정 패널](#설정-패널)
- [생성 및 완료 감지](#생성-및-완료-감지)
- [이미지 수집과 다운로드](#이미지-수집과-다운로드)
- [내부 API 엔드포인트](#내부-api-엔드포인트)
- [한도](#한도)

## 로그인 판정

**DOM 텍스트로 판정하면 반드시 오탐한다.** 실측된 함정:

| 화면 | 미로그인 상태 동작 |
|---|---|
| `labs.google/fx/tools/flow` | 마케팅 랜딩 페이지가 **정상 렌더** (로그인 여부 구분 불가) |
| `labs.google/fx/tools/flow/project` | 앱 셸이 뜨고 "There doesn't seem to be anything here" 표시 |

유일하게 신뢰 가능한 근거:

```
GET https://labs.google/fx/api/auth/session
  로그인:   {"user":{"email":"...","name":"..."},"expires":"..."}
  미로그인: {}
```

`flow_common.get_session(ctx)` 가 이걸 감싼다. **세션 유효기간은 약 8시간**이므로
장시간 배치나 하루 이상 지난 뒤 실행할 때는 `flow_login.py` 재실행이 필요할 수 있다.

## ⛔ 헤드리스는 생성이 차단된다

**Google이 헤드리스 브라우저의 이미지 생성 요청을 403으로 거부한다.** 창을 띄우면 정상 동작한다.

증상:
- UI에는 `문제가 발생했습니다. 다시 시도해 주세요.` + `다시 시도` 버튼
- '다시 시도'를 몇 번 눌러도 계속 실패
- 네트워크: **`POST aisandbox-pa.googleapis.com/v1/flowCreationAgent:streamChat` → 403**

진단 포인트 — 이 403은 **인증 만료가 아니다**:
- `/fx/api/auth/session` 은 정상적으로 user 를 반환
- 다른 aisandbox·tRPC 호출은 전부 200
- 오직 생성 엔드포인트만 403

즉 **일일 캡 소진이나 로그인 문제로 오진하기 쉽다.** 같은 계정을 일반 브라우저로 열면
그 순간에도 생성이 잘 된다는 점이 결정적 단서다.

→ `flow_generate.py` 는 **창을 띄우는 것이 기본**이다. `--headless` 는 DOM 정찰 용도로만 남겨둔다
(읽기 계열 API는 헤드리스에서도 200이라 정찰은 가능하다).

## 화면 진입 경로

**프로젝트 URL로 직접 goto 하면 `Application error: a client-side exception has occurred` 로 죽는다.**
반드시 SPA 라우팅으로 들어갈 것:

```
labs.google/fx/tools/flow
  → 버튼 "Create with Google Flow" 클릭
  → 앱 홈 (labs.google/fx/{locale}/tools/flow)
  → a[href*='/tools/flow/project/'] 클릭  또는  button:has-text('add_2') (새 프로젝트)
  → 프로젝트 편집기
```

로케일은 **계정 설정을 따른다**. `launch(locale="en-US")` 나 URL에 `/en/` 을 넣어도
계정 언어로 리다이렉트된다. → **한국어/영어 양쪽에서 동작하는 셀렉터를 써야 한다.**

### 언어 무관 셀렉터 전략 (핵심)

Flow는 Material Symbols 아이콘 폰트를 쓰므로 버튼 안에 **ligature 텍스트**가 그대로 들어있다.
이 문자열은 UI 언어와 무관하게 항상 동일하다 — 셀렉터로 이것을 쓸 것.

| 요소 | 셀렉터 | 한국어 라벨 |
|---|---|---|
| 새 프로젝트 | `button:has-text('add_2')` | 만들기 |
| 설정 패널 열기 | `button:has-text('tune')` | 설정 |
| 프롬프트 제출 | `button:has-text('arrow_forward')` | 만들기 |
| 생성 중지(=생성 중 표시) | `button:has-text('stop')` | 중지 |
| 프롬프트 입력 | `[contenteditable=true]` (첫 번째) | 무엇을 만들고 싶으신가요? |

예외: **저장 버튼은 라벨이 언어별**(`저장` / `Save`)이라 둘 다 시도해야 한다.

⚠️ ligature 매칭에 `:has-text()` (부분 일치)를 쓰면 안 되는 곳이 있다 —
생성 후 채팅에 나타나는 `arrow_forward_ios` 버튼이 `arrow_forward` 에 걸린다.
`flow_generate.icon()` 은 `:text-is()` (정확 일치)를 쓴다.

## 설정 패널

`tune` 클릭 시 열린다. **이미지 섹션과 동영상 섹션이 같은 구조로 두 번** 나오며,
DOM 상 이미지 섹션이 먼저다 → 항상 `.first` 사용.

### 이미지 비율 (5종 전부 지원)

`button[role=tab]` 의 ligature로 식별:

| 비율 | ligature |
|---|---|
| 16:9 | `crop_16_9` |
| 4:3 | `crop_landscape` |
| 1:1 | `crop_square` |
| 3:4 | `crop_portrait` |
| 9:16 | `crop_9_16` |

동영상 섹션에는 16:9 / 9:16 만 있고 `crop_square` 가 없다 →
`crop_square` 로 잡으면 자연히 이미지 섹션에 걸린다.

### 출력 장수

`button[role=tab]`: `x1`~`x4` (UI 개편으로 `1x` → `x1` 로 바뀐 적 있어 스크립트는 양쪽을 시도).
기본값 x2.

### 이미지 모델

`button:has-text('Nano Banana')` 클릭 → `role=menuitem` 3종:

- `🍌 Nano Banana Pro`
- `🍌 Nano Banana 2`
- `🍌 Nano Banana 2 Lite` ← Flow 기본값

## 생성 및 완료 감지

이 버전의 Flow는 **에이전트 주도형**이다. 프롬프트 바에 이미지/동영상 모드 토글이 없고,
에이전트가 프롬프트 내용을 보고 판단한 뒤 설정 패널의 해당 섹션 값을 사용한다.

→ **프롬프트를 `Generate an image: ...` 로 시작**시켜 이미지 생성을 확실히 유도할 것
(스크립트가 자동으로 붙인다).

완료 감지: 제출 직후 `arrow_forward` 버튼이 `stop` 으로 바뀌고, 생성이 끝나면 되돌아온다.
`stop` 의 존재 여부가 언어 무관 진행 상태 신호다.

소요 시간: nano-banana-2 / 1:1 / 4장 기준 **약 1~3분**.

## 이미지 수집과 다운로드

**생성 이미지는 `lh3.googleusercontent.com` 이 아니다.** (그 호스트는 계정 아바타용)

실제 `<img>` src 형식:

```
https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=<uuid>
```

- 썸네일이 아니라 원본 해상도다
- 세션 쿠키를 가진 `context.request.get(url)` 으로 그대로 받으면 `image/jpeg`
- 리다이렉트는 Playwright가 자동 추적하므로 별도 처리 불필요

수집 방법: **생성이 시작된 뒤** src 집합을 스냅샷 → 차집합.
(제출 전에 기준선을 잡으면, 업로드한 참고 이미지가 같은 media URL 로 렌더되므로
참고 사진이 생성 결과로 오인된다 — 실측된 버그, 스크립트에 반영됨.)

## 내부 API 엔드포인트

생성 1회 중 캡처된 것들 (`aisandbox-pa.googleapis.com`, `labs.google/fx/api/trpc`):

| 엔드포인트 | 용도 |
|---|---|
| `v1/flowCreationAgent:streamChat` | 에이전트 대화 + 생성 요청 (SSE 스트리밍) |
| `v1/flowCreationAgent/sessions` | 세션 생성/조회 |
| `v1/credits` | 크레딧 잔량 |
| `trpc/media.getMediaUrlRedirect` | 미디어 ID → 실제 이미지 |
| `trpc/flow.projectInitialData` | 프로젝트 초기 데이터 |
| `trpc/project.searchUserProjects` | 프로젝트 목록 |
| `trpc/videoFx.getUserSettings` | 사용자 설정(모델/비율/장수) |

`streamChat` 을 직접 재생하면 DOM 없이 배치가 가능하지만 SSE 파싱 + 인증 헤더가 필요하고
엔드포인트가 예고 없이 바뀐다. 현재 스크립트는 **DOM 구동 + 이미지 URL 직접 다운로드**의
하이브리드로, 안정성과 속도의 균형을 잡았다.

## 프로젝트 재사용

한 프로젝트 안에서 에이전트 대화로 계속 생성할 수 있다.

프로젝트 카드에서 이름을 읽을 때 함정: **`<a>` 의 innerText 는 비어 있다.**
제목은 앵커 바깥 형제 요소에 있다. 해결: **프로젝트 링크를 정확히 1개만 포함하는
최근접 조상**까지 올라가면 그 카드의 제목만 얻는다 (`flow_generate.open_project` 참조).

홈의 프로젝트 목록은 **lazy-load** 된다 — 초기 렌더에는 화면에 보이는 몇 개만 DOM에 있다.
이름으로 못 찾았다고 프로젝트가 없다고 단정하지 말 것.

## 비율 — 프롬프트 문구가 설정을 덮어쓴다 (실측)

설정 패널의 비율은 **에이전트에게 주는 기본값일 뿐**이고, 프롬프트에 방향/비율 표현이 있으면
에이전트가 그쪽을 우선한다. 대조 실험:

| 설정 | 프롬프트 | 결과 |
|---|---|---|
| `3:4` | `... vertical composition ...` 포함 | 768 × 1376 (**9:16** ❌) |
| `3:4` | 방향 표현 없음 | 896 × 1200 (**3:4** ✅) |

→ 프롬프트에서 `vertical/horizontal/portrait/landscape/square + composition|format|orientation`,
`16:9` 류 비율 문자열, `widescreen` 등을 반드시 제거할 것.
`flow_generate.strip_orientation()` 이 자동 처리한다.

### 비율별 출력 해상도 (참고, 모델에 따라 달라질 수 있음)

| 설정 | 관측된 해상도 |
|---|---|
| 1:1 | 1024 × 1024 |
| 16:9 | 1376 × 768 |
| 3:4 | 896 × 1200 |
| 9:16 | 768 × 1376 |

사용자에게 안내할 때는 **비율 이름만** 쓰고 픽셀 크기를 단정하지 않는다.

## 한도

- Google 공식 크레딧 문서에는 영상 모델 요금표만 있고 **이미지 모델 요금이 없다.**
- 공식 모델 문서: Nano Banana 2 Lite = "available at no charge by default"
- 커뮤니티 보고: Nano Banana Pro는 무료 계정 기준 하루 약 20장 캡

→ 이미지는 크레딧 미터링 대상이 아니고 **모델별 일일 캡**으로 통제되는 것으로 보인다.
정확한 캡은 계정 등급에 따라 다르므로, 대량 배치 전 소량으로 확인할 것.
캡에 걸리면 생성이 조용히 0장으로 끝난다 — `report.json` 의 `error: "flow_error"` 로 판별.
