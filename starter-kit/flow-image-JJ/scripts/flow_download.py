"""이미지 수집/저장 유틸 — DOM에 의존하지 않는 부분."""
from __future__ import annotations

import base64
import re
from pathlib import Path

SAFE = re.compile(r"[^a-z0-9]+")


def slug(text: str, maxlen: int = 40) -> str:
    s = SAFE.sub("-", text.lower()).strip("-")
    return (s[:maxlen] or "img").rstrip("-")


def save_bytes(data: bytes, out_dir: Path, name: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    n = 1
    while path.exists():
        path = out_dir / f"{path.stem}_{n}{path.suffix}"
        n += 1
    path.write_bytes(data)
    return path


def save_data_url(data_url: str, out_dir: Path, name: str) -> Path | None:
    """data:image/png;base64,... 형태를 파일로 저장."""
    m = re.match(r"data:image/(\w+);base64,(.*)", data_url, re.S)
    if not m:
        return None
    ext, b64 = m.group(1), m.group(2)
    return save_bytes(base64.b64decode(b64), out_dir, f"{Path(name).stem}.{ext}")


def download_url(ctx, url: str, out_dir: Path, name: str, timeout: int = 120_000) -> Path | None:
    """브라우저 세션(쿠키 포함)으로 이미지 URL을 받아 저장."""
    try:
        resp = ctx.request.get(url, timeout=timeout)
        if not resp.ok:
            print(f"    [download fail {resp.status}] {url[:90]}")
            return None
        body = resp.body()
        if len(body) < 1024:  # 에러 페이지/플레이스홀더 방어
            print(f"    [download too small: {len(body)}B] {url[:90]}")
            return None
        ctype = (resp.headers.get("content-type") or "").lower()
        ext = "png"
        if "jpeg" in ctype or "jpg" in ctype:
            ext = "jpg"
        elif "webp" in ctype:
            ext = "webp"
        return save_bytes(body, out_dir, f"{Path(name).stem}.{ext}")
    except Exception as exc:
        print(f"    [download error] {exc}")
        return None


def read_prompts(spec: str) -> list[str]:
    """프롬프트 입력 파싱.

    - 파일 경로(.txt): 빈 줄로 구분된 블록 = 1 프롬프트
    - 그 외 문자열: '||' 또는 개행으로 분리
    """
    p = Path(spec)
    if p.exists() and p.is_file():
        raw = p.read_text(encoding="utf-8")
        blocks = []
        for b in re.split(r"\n\s*\n", raw):
            # 블록 안의 주석 줄(#)만 걷어낸다. 예전에는 블록 첫 줄이 주석이면 블록 전체를
            # 버려서, 주석 바로 아래에 붙여 쓴 프롬프트가 통째로 사라졌다. (실측)
            body = "\n".join(l for l in b.splitlines() if not l.lstrip().startswith("#")).strip()
            if body:
                blocks.append(body)
        return blocks
    parts = [s.strip() for s in re.split(r"\|\||\n", spec)]
    return [s for s in parts if s]
