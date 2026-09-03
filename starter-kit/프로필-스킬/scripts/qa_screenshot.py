#!/usr/bin/env python3
"""전 슬라이드를 캡처하고 넘침(overflow)을 검사한다. 육안 QA 게이트."""
import sys, os, asyncio
from playwright.async_api import async_playwright

# Windows 콘솔은 기본이 cp949라 이모지·특수문자 출력 중 죽는 경우가 있다. UTF-8로 강제한다.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

OUT = "workspace/결과물/qa_profile"


async def run(path):
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        # 시스템 Chrome을 그대로 쓴다 — 번들 Chromium을 따로 받지 않아도 된다
        # (다른 스킬의 naver_draft.py / flow-image-JJ 와 같은 방식).
        b = await p.chromium.launch(channel="chrome")
        pg = await b.new_page(viewport={"width": 1960, "height": 1120})
        await pg.goto("file://" + os.path.abspath(path))
        await pg.wait_for_timeout(3000)
        slides = await pg.query_selector_all(".slide")
        bad = 0
        for i, s in enumerate(slides):
            cls = (await s.get_attribute("class")).replace("slide ", "")
            box = await s.bounding_box()
            # 장식용 가상요소(::before/::after)는 overflow:hidden으로 잘리므로
            # 실제 콘텐츠(직계 자식) 기준으로만 넘침을 판정한다.
            m = await s.evaluate("""e => {
                const r = e.getBoundingClientRect(); let b = 0, w = 0;
                for (const c of e.children) {
                  const cr = c.getBoundingClientRect();
                  b = Math.max(b, cr.bottom - r.top); w = Math.max(w, cr.right - r.left);
                }
                return {b: Math.round(b), w: Math.round(w)};
            }""")
            flag = ""
            if m["b"] > 1081 or m["w"] > 1921:
                flag = f"  <== OVERFLOW (content {m['w']}x{m['b']})"; bad += 1
            if box and (round(box["width"]) != 1920 or round(box["height"]) != 1080):
                flag += f"  <== SIZE {round(box['width'])}x{round(box['height'])}"; bad += 1
            f = f"{OUT}/{i+1:02d}_{cls}.png"
            await s.screenshot(path=f)
            print(f"{i+1:02d} {cls:12s} -> {f}{flag}")
        await b.close()
        print(f"\n캡처 {len(slides)}장 완료. 문제 {bad}건.")
        print("반드시 이미지를 직접 열어 확인한 뒤 전달할 것.")
        return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: qa_screenshot.py <file.html>"); sys.exit(2)
    sys.exit(asyncio.run(run(sys.argv[1])))
