"""Gemini 이미지 생성 — 블로그 삽화용.

디오라마 스타일을 기본 프리셋으로 둔다. 사진보다 '작은 모형 세계'로 개념을
보여주는 쪽이 눈에 띄고, 실제 인물 사진을 안 써도 되니 초상권 걱정도 없다.

  py -3.14 gen_image.py --topic "AI 교육을 듣는 직장인들" --out img/ai_edu.png
  py -3.14 gen_image.py --prompt "자유 프롬프트" --out x.png --style none

키는 .env 의 GOOGLE_API_KEY 를 쓴다. 키 값은 로그에 찍지 않는다.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import dotenv_values

BASE = Path(__file__).resolve().parent
DEFAULT_MODEL = "gemini-3-pro-image"

# 디오라마 프리셋. 브랜드 톤(퍼플/마젠타)을 은은하게 깔되 과하지 않게.
DIORAMA_STYLE = (
    "A highly detailed miniature diorama scene, tilt-shift photography style, "
    "shallow depth of field, soft studio lighting from above. "
    "Tiny handcrafted figurines with clean simple faces, matte clay-like texture. "
    "Set on a small circular platform floating on a clean light background. "
    "Subtle purple and magenta accent lighting. "
    "Warm, optimistic, professional mood. No text, no letters, no words, "
    "no logos, no watermarks anywhere in the image. "
    "Square composition, centered subject."
)


def load_key() -> str:
    key = (dotenv_values(BASE / ".env").get("GOOGLE_API_KEY") or "").strip()
    if not key:
        print("[img] GOOGLE_API_KEY 가 .env 에 없습니다.", file=sys.stderr)
        sys.exit(2)
    return key


def build_prompt(topic: str, style: str) -> str:
    if style == "none":
        return topic
    return f"{DIORAMA_STYLE}\n\nScene to depict: {topic}"


def generate(prompt: str, out: Path, model: str, key: str) -> int:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[img] HTTP {e.code}: {e.read().decode()[:400]}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"[img] {type(e).__name__}: {e}", file=sys.stderr)
        return 3

    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(base64.b64decode(blob["data"]))
                print(f"[img] 저장: {out}  ({out.stat().st_size:,} bytes)")
                return 0

    # 이미지가 안 왔으면 왜 안 왔는지 남긴다(안전필터 등)
    fb = data.get("promptFeedback") or {}
    fin = [c.get("finishReason") for c in data.get("candidates", [])]
    print(f"[img] 이미지가 반환되지 않았습니다. finishReason={fin} feedback={fb}",
          file=sys.stderr)
    return 4


def main() -> int:
    ap = argparse.ArgumentParser(description="Gemini 이미지 생성 (디오라마 기본)")
    ap.add_argument("--topic", default="", help="장면 설명(한국어 가능)")
    ap.add_argument("--prompt", default="", help="완성된 프롬프트 직접 지정")
    ap.add_argument("--style", default="diorama", choices=["diorama", "none"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    a = ap.parse_args()

    if not a.topic and not a.prompt:
        print("--topic 또는 --prompt 가 필요합니다.", file=sys.stderr)
        return 1
    prompt = a.prompt or build_prompt(a.topic, a.style)
    print(f"[img] model={a.model} style={a.style}")
    return generate(prompt, Path(a.out), a.model, load_key())


if __name__ == "__main__":
    sys.exit(main())
