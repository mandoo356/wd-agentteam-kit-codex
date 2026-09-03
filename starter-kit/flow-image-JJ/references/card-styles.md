# 카드뉴스 이미지 스타일 카탈로그 — 20종

Google Flow로 실제 생성해 검증한 20종.
시각 샘플: https://jj-aiedu.vercel.app/style/card-styles.html
(스타일 번호를 묻기 전에 반드시 이 페이지를 새 창으로 열어 보여준다 — `show_styles.py`)

- 조합 선택("1번+19번")도 가능 = 표지/내지 역할 분담.
- 한 세트(캐러셀 등) 안에서 스타일을 섞지 않는다 (조합 선택의 표지/내지 분담만 예외).

## 공통 카드 문법 (모든 스타일에 항상 포함)

```
Top-left: tiny Korean brand label '<사용자 브랜드명> <섹션명>'.
Lower third: large ultra-bold Korean headline '<훅 문장>' with the key phrase
in the style's accent color. One small muted Korean caption line below.
All text in the image must be Korean, no English except the brand name.
```

- `<사용자 브랜드명>` 은 사용자에게 확인해 넣는다 (없으면 브랜드 라벨 줄을 뺀다).
- 브랜드 라벨/헤드라인이 필요 없는 일반 삽화라면 이 문법을 생략하고 스타일 레시피만 쓴다.
- 고유명사(프로그램명 등)는 캡션에 넣지 않는다 — 생성 오타가 잦다.
- 생성 후 매 장 눈으로 검수하고, 텍스트 깨진 장만 재생성한다.

## 스타일 레시피 (번호 = 대시보드)

| # | 이름 | 프롬프트 핵심 (아트 스타일 + 팔레트 + 강조색) |
|---|---|---|
| 01 | 시네마틱 3D 다크골드 | `premium Instagram card news cover, deep dark navy (#0d1526), cinematic warm golden spot lighting, soft bokeh, cute stylized Pixar-like 3D-rendered scene of <장면>, glossy high-end 3D editorial` · 강조 `#ffc94d` |
| 02 | 클레이 파스텔 3D | `soft pastel mint-cream background, claymation-style chunky clay-textured 3D scene of <장면>, soft studio light, gentle shadows` · 강조 coral orange |
| 03 | 아이소메트릭 오피스 | `bright light-gray background, clean isometric 3D render of <사무실 장면>, soft pastel blue-orange palette` · 강조 blue |
| 04 | 네온 사이버 | `dark futuristic background, neon blue and purple glow, holographic grid floor, glowing 3D wireframe <오브제>, digital particles, cyberpunk premium tech` · 강조 neon cyan |
| 05 | 오브젝트 스튜디오 | `studio product-photo style, solid warm beige background, single elegant <실물 오브제> under soft directional studio light, long soft shadow, photorealistic, minimal premium editorial` · 강조 burnt orange |
| 06 | 레트로 콜라주 | `retro magazine collage, torn paper pieces, halftone-printed photo fragments of <장면>, masking tape, grainy texture, cream and red-orange palette` · 강조 red marker circle |
| 07 | 플랫 벡터 | `clean corporate flat vector illustration, white background, large soft geometric shapes in blue and orange, flat-style <인물 장면>, crisp edges` · 강조 orange |
| 08 | 페이퍼컷 아트 | `layered papercut art, deep teal background, multi-layer paper-cut scene of <장면>, soft shadows between layers, gold paper accents, handcrafted premium` · 강조 gold |
| 09 | 실사 시네마 스틸 | `cinematic photography film still, <인물/공간 장면> at dusk, moody teal-orange color grade, shallow depth of field, photorealistic, movie-subtitle style text` · 강조 warm yellow |
| 10 | 글래스 그라디언트 | `glassmorphism 3D, smooth blue-violet gradient background, frosted translucent glass panels, <유리 오브제> with light refraction, soft glow, sleek modern` · 강조 bright aqua |
| 11 | 토이 브릭 | `toy building-brick diorama, plastic minifigure of <인물> in a tiny brick-built <공간>, colorful bricks, glossy toy photography, shallow depth of field, warm light` · 강조 yellow |
| 12 | 블랙보드 초크 | `dark green-black chalkboard with chalk dust texture, hand-drawn white chalk illustration of <도해>, chalk-lettering headline` · 강조 yellow chalk |
| 13 | 화이트보드 손그림 | `hand-drawn pen illustration, whiteboard-animation style, clean white background, simple drawing of <장면>, blue and orange accents, high contrast` · 강조 blue/orange |
| 14 | 픽셀아트 레트로 | `retro 8-bit pixel art, dark blue pixel night sky, pixel <장면>, game UI frame border, blocky pixel-font headline, nostalgic game feel` · 강조 green |
| 15 | 북커버 에디토리얼 | `elegant book cover design, warm cream background with linen paper texture, small gold-foil emblem, refined Korean serif title, thin gold border frame, literary premium` · 강조 gold |
| 16 | 뉴스 브리핑 | `broadcast news graphics, studio-blue gradient background with subtle world-map motif, glassy panels, red Korean badge, lower-third headline bar, ticker caption, crisp broadcast look` · 강조 yellow |
| 17 | 럭셔리 그린골드 | `luxury editorial, deep emerald green with subtle marble texture, photorealistic golden <오브제> under dramatic spotlight, gold dust, elegant ivory Korean serif, opulent` · 강조 gold |
| 18 | 웹툰 코믹 | `Korean webtoon comic style, single dramatic panel of <인물 상황>, bold comic linework, screentone shading, vivid colors, speech bubble with Korean text` · 강조 red-orange |
| 19 | 3D 인포그래픽 | `3D infographic style, clean light background, floating 3D <차트가 곧 장면> with small 3D Korean figure, glossy blue-orange materials, soft studio light` · 강조 orange |
| 20 | 미니어처 디오라마 | `tilt-shift miniature diorama photography, tiny detailed miniature <세계> seen from above at an angle, warm cozy lighting, shallow depth of field toy-world look` · 강조 warm yellow |

## 콘텐츠 적합 힌트 (추천을 요청받았을 때)

- 강한 주장/훅 표지: 01 04 09 17 · 개념 정리/프레임워크: 03 07 19
- 절차·커리큘럼: 03 12 19 · 현장 후기: 09 20 · 감성·후기 인용: 05 15
- 위트·MZ 타깃: 02 11 14 18 · 보도·사례 발표 톤: 16 · 임원·고급 과정: 15 17
