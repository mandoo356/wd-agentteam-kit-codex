# 강사 프로필 덱 전체 CSS (범용 · facts.md 색 적용)

아래 블록을 `<style>` 안에 **그대로** 붙여넣는다. `:root` 의 네 값만
`workspace/memory/facts.md` 에 적힌 색으로 바꾸고, 그 외 임의 색상은 추가하지 않는다.

```css
* { margin:0; padding:0; box-sizing:border-box; }

:root{
  --main:#메인색; --deep:#진한색; --accent:#강조색; --pale:#옅은색;
  --f:"Noto Sans KR","Noto Sans Korean","Noto Sans CJK KR","NotoSansKR","Malgun Gothic","맑은 고딕",sans-serif;
  --deck-bg: linear-gradient(135deg, var(--deep) 0%, var(--main) 100%);
}
body { font-family:var(--f); background:#111; color:#333; }

.slide {
  width:1920px; height:1080px; margin:20px auto; position:relative;
  overflow:hidden; background:#fff; page-break-after:always;
  box-shadow:0 4px 24px rgba(0,0,0,.25);
}
@media print { body{background:#fff;} .slide{box-shadow:none; margin:0 auto;} }

/* ==================== 공통 헤더 / 마크 ==================== */
.sec-head { position:absolute; top:44px; left:64px; display:flex; align-items:center; gap:16px; z-index:5; }
.sec-bar  { width:7px; height:42px; background:var(--accent); border-radius:4px; }
.sec-title{ font-size:40px; font-weight:800; color:#fff; letter-spacing:-1px; }
.sec-title.dark { color:var(--deep); }
.sec-bar.dark { background:var(--main); }
.sec-sub  { position:absolute; top:100px; left:80px; font-family:var(--f); font-size:30px;
            color:rgba(255,255,255,.88); letter-spacing:.5px; z-index:5; }
.sec-sub em{ font-style:normal; color:var(--accent); }
.dots { position:absolute; top:52px; right:64px; display:flex; gap:9px; z-index:5; }
.dots i{ width:9px; height:9px; border-radius:50%; background:rgba(255,255,255,.42); }
.dots.dark i{ background:color-mix(in srgb, var(--main) 35%, transparent); }
.brand-mark { position:absolute; bottom:38px; right:56px; z-index:6;
              font-size:15px; font-weight:800; color:rgba(255,255,255,.75); letter-spacing:.5px; }
.page-num { position:absolute; bottom:30px; left:64px; font-size:16px; font-weight:600; color:rgba(255,255,255,.45); z-index:5; }
.page-num.dark { color:#bbb; }

/* 공통 컴포넌트 */
.pill { display:inline-block; padding:9px 30px; border-radius:40px; background:rgba(255,255,255,.14);
        border:1px solid rgba(255,255,255,.22); color:#fff; font-size:20px; font-weight:700; letter-spacing:1px; }
.pill.solid { background:var(--main); border-color:transparent; }
.logo-tile { background:rgba(255,255,255,.93); border-radius:14px; display:flex; align-items:center;
             justify-content:center; padding:14px 18px; box-shadow:0 2px 12px rgba(0,0,0,.16); }
.logo-tile img { max-height:62%; max-width:78%; object-fit:contain; }
.logo-tile span { font-size:26px; font-weight:800; color:var(--deep); letter-spacing:-.5px; }
/* 흰 배경에서 사라지는 로고(흰 글자형)는 다크 타일을 쓴다 */
.logo-tile.dark { background:rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.16);
                  box-shadow:none; backdrop-filter:blur(2px); }
.logo-tile.dark span { color:#fff; }

/* ==================== 1. 표지 ==================== */
.p-cover { background:var(--deck-bg); display:flex; align-items:center; }
.p-cover::before{ content:''; position:absolute; width:1250px; height:1250px; border-radius:50%;
  right:-330px; top:-220px; background:radial-gradient(circle at 35% 35%, color-mix(in srgb, var(--accent) 34%, transparent), transparent 68%); }
.p-cover::after{ content:''; position:absolute; width:1000px; height:1000px; border-radius:50%;
  left:-300px; bottom:-430px; background:radial-gradient(circle at 60% 40%, color-mix(in srgb, var(--main) 30%, transparent), transparent 70%); }
.cv-body { position:relative; z-index:3; padding-left:118px; max-width:1180px; }
.cv-lead { font-size:44px; font-weight:700; color:#fff; margin-bottom:10px; letter-spacing:-1px; }
.cv-lead span { color:var(--accent); }
.cv-name { font-size:132px; font-weight:800; color:#fff; line-height:1.05; letter-spacing:-5px; margin-bottom:26px; }
.cv-tag  { font-size:23px; font-weight:500; color:rgba(255,255,255,.82); letter-spacing:.5px; }
.cv-rule { position:absolute; left:118px; right:118px; bottom:150px; height:1px; background:rgba(255,255,255,.28); z-index:3; }
.cv-logo { position:absolute; top:52px; right:64px; z-index:6;
           font-size:22px; font-weight:800; color:#fff; letter-spacing:.5px; opacity:.92; }

/* ==================== 2. 강사 소개 ==================== */
.p-intro { background:var(--deck-bg); display:flex; align-items:flex-end; }
.p-intro::before{ content:''; position:absolute; width:900px; height:900px; border-radius:50%;
  left:-320px; top:-160px; background:radial-gradient(circle, color-mix(in srgb, var(--main) 26%, transparent), transparent 70%); }
.in-photo { position:relative; z-index:3; width:600px; height:1080px; display:flex; align-items:flex-end; justify-content:center; }
.in-photo img { max-height:1000px; max-width:100%; object-fit:contain; object-position:bottom; }
.in-right { position:relative; z-index:3; flex:1; padding:196px 84px 74px 20px; }
.in-catch { font-size:37px; font-weight:700; color:var(--accent); margin-bottom:6px; letter-spacing:-1px; }
.in-catch span { color:#fff; }
.in-name  { font-size:74px; font-weight:800; color:#fff; letter-spacing:-3px; margin-bottom:40px; }
.in-cols  { display:flex; gap:56px; margin-bottom:38px; }
.in-col   { flex:1; }
.in-col .pill { margin-bottom:22px; }
.in-list  { list-style:none; }
.in-list li { font-size:21px; color:rgba(255,255,255,.86); line-height:2.0; }
.in-list li.now { font-weight:800; color:#fff; }
.in-cert  { display:grid; grid-template-columns:1fr 1fr; column-gap:34px; }
.in-cert li{ font-size:20px; }
.in-logos { display:flex; gap:26px; }
.in-logos .logo-tile { flex:1; height:96px; }

/* ==================== 3. 강의 이력 ==================== */
.p-history { background:var(--deck-bg); padding:150px 74px 96px;
             display:flex; flex-direction:column; }
.hs-top { display:flex; gap:26px; }
.hs-body { flex:1; display:flex; flex-direction:column; justify-content:center; gap:54px; }
.hs-top .logo-tile { flex:1; height:112px; }
.hs-row { display:flex; align-items:flex-start; gap:34px; }
.hs-row .pill { flex:0 0 210px; text-align:center; margin-top:6px; }
.hs-text { flex:1; font-size:21px; line-height:1.9; color:rgba(255,255,255,.9); word-break:keep-all; }

/* ============ 3-B. 강의 분야 (선택) ============ */
.p-domain { background:var(--deck-bg); padding:150px 74px 88px;
            display:flex; flex-direction:column; }
.dm-grid { flex:1; display:grid; grid-template-columns:repeat(3,1fr); gap:34px; }
.dm-card { background:rgba(255,255,255,.09); border:1px solid rgba(255,255,255,.16);
           border-radius:20px; padding:44px 38px; display:flex; flex-direction:column; }
.dm-card h4 { font-size:33px; font-weight:800; color:#fff; letter-spacing:-1px; margin-bottom:8px; }
.dm-card .dm-en { font-size:17px; font-weight:600; color:var(--accent);
                  letter-spacing:3px; text-transform:uppercase; margin-bottom:26px; }
.dm-list { list-style:none; flex:1; display:flex; flex-direction:column;
            justify-content:space-between; }
.dm-list li { font-size:22px; line-height:1.5; color:rgba(255,255,255,.9);
              flex:1; display:flex; align-items:center;
              padding:0 0 0 24px; position:relative;
              border-bottom:1px solid rgba(255,255,255,.10); }
.dm-list li:last-child { border-bottom:none; }
.dm-list li::before { content:''; position:absolute; left:0; top:50%; margin-top:-4px;
                      width:8px; height:8px; border-radius:50%; background:var(--accent); }

/* ==================== 4. 언론 보도 ==================== */
.p-press { background:var(--deck-bg); padding:150px 64px 86px;
           display:flex; flex-direction:column; }
.p-press .pr-grid { flex:1; align-content:center; }
.pr-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:28px; }
.pr-card { display:flex; flex-direction:column; gap:18px; }
.pr-shot { height:730px; background:#fff; border-radius:14px; overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,.28); }
.pr-shot img { width:100%; height:100%; object-fit:cover; object-position:top; }
/* 책 표지·포스터처럼 잘리면 안 되는 이미지 */
.pr-shot.fit { height:640px; background:var(--pale); display:flex; align-items:center;
                justify-content:center; padding:26px; }
.pr-shot.fit img { width:auto; height:auto; max-width:100%; max-height:100%; object-fit:contain;
                   box-shadow:0 4px 16px rgba(0,0,0,.18); }
/* 여러 표지를 나란히 놓을 때는 이미지들을 같은 종횡비로 패딩해 두어야 크기가 맞는다. */
.pr-cap { padding:15px 10px; border-radius:40px; background:var(--main); color:#fff;
          font-size:20px; font-weight:700; text-align:center; }

/* 밝은 면 위 플레이스홀더 */
.ph-dark { width:100%; height:100%; display:flex; align-items:center; justify-content:center;
           background:linear-gradient(180deg, var(--pale), #fff); color:var(--deep); font-size:20px; }

/* ==================== 5. WHY (화이트 배경) ==================== */
.p-why { background:linear-gradient(160deg, #fff 0%, var(--pale) 100%); padding:150px 96px 104px;
         display:flex; flex-direction:column; justify-content:space-between; }
.why-q { font-size:54px; font-weight:800; color:var(--deep); text-align:center; letter-spacing:-2px; }
.why-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:36px; }
.why-card { background:#fff; border-radius:22px; padding:60px 32px; text-align:center;
            box-shadow:0 4px 22px color-mix(in srgb, var(--main) 12%, transparent); }
.why-ico { font-size:76px; margin-bottom:30px; }
/* 이모지 대신 쓰는 브랜드 넘버 뱃지 */
.why-num { width:86px; height:86px; margin:0 auto 26px; border-radius:50%;
           background:linear-gradient(135deg, var(--main), var(--accent));
           display:flex; align-items:center; justify-content:center;
           color:#fff; font-size:34px; font-weight:800; letter-spacing:-1px; }
.why-pre { font-size:24px; color:#666; margin-bottom:8px; }
.why-key { font-size:40px; font-weight:800; color:var(--deep); letter-spacing:-1px; }
.why-key span { color:var(--accent); }
.why-badges { display:grid; grid-template-columns:repeat(3,1fr); gap:36px; }
.why-col { display:flex; flex-direction:column; gap:22px; }
.why-badge { background:var(--pale); border-radius:14px; padding:26px 20px; text-align:center;
             font-size:21px; font-weight:600; color:var(--deep); line-height:1.45; }
.why-badge strong { color:var(--accent); font-weight:800; }

/* ==================== 6. 교육 후기 ==================== */
.p-review { background:var(--deck-bg); padding:146px 96px 66px;
            display:flex; flex-direction:column; }
.rv-lead { font-family:var(--f); font-size:46px; color:#fff; text-align:center;
           line-height:1.5; margin-bottom:34px; }
.rv-lead em { font-style:normal; color:var(--accent); }
.rv-grid { flex:1; display:flex; gap:64px; justify-content:center; align-items:stretch; }
/* 기기 목업은 상·하 베젤을 모두 닫는다. 아래가 잘리면 잘못된 것이다. */
.phone { width:424px; border-radius:46px; background:#1b1b1b; padding:15px;
         box-shadow:0 12px 36px rgba(0,0,0,.42); position:relative; }
.phone::before { content:''; position:absolute; top:26px; left:50%; transform:translateX(-50%);
                 width:112px; height:9px; border-radius:6px; background:#333; z-index:2; }
.phone-in { height:100%; background:var(--pale); border-radius:33px; padding:46px 18px 22px;
            overflow:hidden; }
.rv-tag { display:block; margin:0 auto 20px; width:78%; padding:11px 0; border-radius:40px;
          background:var(--deep); color:#fff; font-size:21px; font-weight:700; text-align:center; }
.rv-bubble { background:#fff; border-radius:16px; padding:17px 19px; margin-bottom:13px;
             font-size:16.5px; line-height:1.62; color:#333; white-space:pre-line; }
.rv-bubble b { color:var(--deep); }

/* ==================== 7. 교육 현장 (반복) ==================== */
.p-field { background:var(--deck-bg); padding:164px 64px 88px; }
.fd-grid { display:grid; grid-template-columns:repeat(4,1fr); grid-template-rows:repeat(2,1fr);
           gap:20px; height:744px; }
.fd-cell { border-radius:12px; overflow:hidden; background:rgba(255,255,255,.08); }
.fd-cell img { width:100%; height:100%; object-fit:cover; }
.fd-foot { position:absolute; bottom:34px; left:0; width:100%; text-align:center;
           font-size:23px; font-weight:700; color:rgba(255,255,255,.9); }
.fd-foot span { color:var(--accent); }

/* ==================== 8. 감사 ==================== */
.p-thanks { background:var(--deck-bg); display:flex; align-items:flex-end; }
.p-thanks::before{ content:''; position:absolute; width:1100px; height:1100px; border-radius:50%;
  right:-260px; bottom:-380px; background:radial-gradient(circle, color-mix(in srgb, var(--accent) 28%, transparent), transparent 70%); }
.tk-photo { position:relative; z-index:3; width:620px; height:1080px; display:flex; align-items:flex-end; justify-content:center; }
.tk-photo img { max-height:960px; max-width:100%; object-fit:contain; object-position:bottom; }
.tk-right { position:relative; z-index:3; flex:1; align-self:center; padding:0 120px 40px 20px; text-align:center; }
.tk-lead { font-family:var(--f); font-size:38px; color:#fff; margin-bottom:12px; }
.tk-lead em { font-style:normal; color:var(--accent); }
.tk-big { font-size:118px; font-weight:800; color:rgba(255,255,255,.94); letter-spacing:-4px; margin-bottom:46px; }
.tk-chip { display:block; width:520px; margin:0 auto 22px; padding:19px 0; border-radius:44px;
           background:rgba(255,255,255,.92); color:var(--deep);
           font-size:25px; font-weight:700; text-align:center; }
```

## 사진이 없을 때 (플레이스홀더 규칙)

인물 사진 미제공 시 `<img>` 대신 아래를 쓴다. 서양인 스톡 사진 금지.

```html
<div class="in-photo">
  <div style="width:420px;height:820px;border-radius:210px 210px 0 0;
       background:linear-gradient(180deg,rgba(255,255,255,.20),rgba(255,255,255,.04));
       display:flex;align-items:center;justify-content:center;
       font-size:23px;color:rgba(255,255,255,.55);">강사 사진 영역</div>
</div>
```
