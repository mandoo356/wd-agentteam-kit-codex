# flow-image-JJ 설치 안내

Google Flow에서 이미지를 대량 생성해 자동 다운로드하는 Codex CLI 스킬입니다.
API 키가 아니라 **본인 Google 계정(구독)** 으로 동작하므로 추가 비용 없이 쓸 수 있습니다.

## 1. 사전 조건 (설치 전에 꼭 확인!)

| 필요한 것 | 설명 |
|---|---|
| **Python 3.10 이상** | `python --version` 으로 확인. 없으면 python.org에서 설치 (Windows는 설치 시 "Add Python to PATH" 체크) |
| **playwright 패키지** | 터미널에서 `pip install playwright` |
| **Chrome 브라우저** | PC에 설치된 일반 Chrome을 그대로 사용합니다 (별도 브라우저 다운로드 불필요) |
| **Google Flow를 쓸 수 있는 Google 계정** | https://labs.google/fx/tools/flow 에 로그인해서 이미지 생성이 되는 계정이어야 합니다 (Google AI/Gemini 구독 필요) |

## 2. 스킬 설치

압축을 풀어 `flow-image-JJ` 폴더를 통째로 Codex CLI 스킬 폴더에 넣습니다.

- Windows: `C:\Users\<사용자명>\.agents\skills\flow-image-JJ`
- macOS/Linux: `~/.agents/skills/flow-image-JJ`

설치 후 Codex CLI를 재시작하고 프롬프트에 `$flow-image-JJ`를 적어 명시적으로 호출할 수 있습니다.

## 3. 최초 1회 — 본인 Google 계정 등록 (필수)

**반드시 본인 Google 계정을 1개 이상 등록해야 스킬이 동작합니다.**

```bash
python ~/.agents/skills/flow-image-JJ/scripts/flow_login.py
```

크롬 창이 뜨면 **본인이 직접** Google 계정으로 로그인하세요.
로그인 세션은 전용 프로필에 저장되며 약 8시간 유효합니다 (만료 시 같은 명령 재실행).

등록 확인:

```bash
python ~/.agents/skills/flow-image-JJ/scripts/flow_probe.py
```

`SESSION: <내 이메일>` 이 출력되면 준비 완료입니다.

## 4. 사용

Codex CLI에서 이렇게 요청하면 됩니다:

- "구글 플로우로 이미지 만들어줘"
- "카드뉴스 이미지 4장 뽑아줘"
- "이 사진 참고해서 이미지 생성해줘 (경로: C:\...\photo.jpg)"

Codex가 스타일 20종 샘플 페이지(https://jj-aiedu.vercel.app/style/card-styles.html)를
먼저 열어서 보여준 뒤, **스타일 번호(1~20)** 와 **사이즈(16:9 / 4:3 / 1:1 / 3:4 / 9:16)** 를
물어보고 생성을 시작합니다. 결과는 다운로드 폴더의 `image-flow\<프로젝트명>` 에 저장됩니다.

## 주의사항

- 생성 중에는 크롬 창이 떠 있어야 합니다 (창 없이 돌리면 Google이 403으로 차단).
- 이미지 모델에는 일일 생성 한도가 있습니다. 한도에 걸리면 다음 날 다시 시도하거나
  다른 계정을 추가 등록해 이어서 뽑을 수 있습니다 (SKILL.md의 다계정 절 참조).
- 이 스킬은 자격증명을 저장하거나 대신 입력하지 않습니다 — 로그인은 항상 본인이 직접 합니다.
