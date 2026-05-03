#!/usr/bin/env python3
"""Generate brand images for LUMKO landing using DefAPI or OpenAI Images API.

Uses DefAPI gpt-image-2 when DEFAPI, DEFAPI_API_KEY, or DEFAPI_KEY is set.
Falls back to OpenAI gpt-image-2, gpt-image-1.5, and gpt-image-1 when available.
Reads API keys from ../.env (KEY=VALUE format).
Saves outputs to ../assets/ai/.
"""
from __future__ import annotations

import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
OUT = ROOT / "assets" / "ai"
OUT.mkdir(parents=True, exist_ok=True)


def load_env() -> dict[str, str]:
    if not ENV.exists():
        sys.exit(f"missing {ENV}")
    values: dict[str, str] = {}
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def request_openai_image(api_key: str, model: str, prompt: str, size: str) -> bytes:
    payload = {"model": model, "prompt": prompt, "size": size, "n": 1}
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read())
    item = body["data"][0]
    if "b64_json" in item and item["b64_json"]:
        return base64.b64decode(item["b64_json"])
    if "url" in item and item["url"]:
        with urllib.request.urlopen(item["url"], timeout=120) as r:
            return r.read()
    raise RuntimeError(f"unexpected response: {body}")


def request_json(url: str, api_key: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key.removeprefix('Bearer ')}",
            "Content-Type": "application/json",
        },
        method="GET" if payload is None else "POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code} from {url}: {body[:500]}") from e


def request_defapi_image(api_key: str, prompt: str, size: str, quality: str = "high") -> bytes:
    payload = {
        "model": "openai/gpt-image-2",
        "prompt": prompt,
        "size": size,
        "quality": quality,
    }
    created = request_json("https://api.defapi.org/api/gpt-image/gen", api_key, payload)
    task_id = (created.get("data") or {}).get("task_id") if isinstance(created.get("data"), dict) else None
    if not task_id:
        raise RuntimeError(f"unexpected DefAPI create response: {created}")
    print(f"  DefAPI task {task_id}: created", flush=True)

    query = "https://api.defapi.org/api/task/query?" + urllib.parse.urlencode({"task_id": task_id})
    for attempt in range(60):
        time.sleep(5 if attempt else 2)
        try:
            body = request_json(query, api_key)
        except RuntimeError as e:
            if "HTTP 404" in str(e) and attempt < 6:
                print(f"  DefAPI task {task_id}: not indexed yet", flush=True)
                continue
            raise
        data = body.get("data")
        if not isinstance(data, dict):
            raise RuntimeError(f"unexpected DefAPI task response: {body}")

        status = data.get("status")
        if status in {"pending", "in_progress"}:
            print(f"  DefAPI task {task_id}: {status}", flush=True)
            continue
        if status == "failed":
            raise RuntimeError(f"DefAPI task failed: {data.get('status_reason')}")
        if status == "success":
            result = data.get("result")
            if not isinstance(result, list) or not result:
                raise RuntimeError(f"DefAPI task succeeded with no result: {body}")
            image_url = result[0].get("image") if isinstance(result[0], dict) else None
            if not image_url:
                raise RuntimeError(f"DefAPI result missing image URL: {body}")
            print(f"  DefAPI task {task_id}: downloading result", flush=True)
            image_req = urllib.request.Request(
                str(image_url),
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                    ),
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                },
            )
            try:
                with urllib.request.urlopen(image_req, timeout=180) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"HTTP {e.code} downloading DefAPI result: {body[:500]}") from e

        raise RuntimeError(f"unexpected DefAPI task status: {body}")
    raise TimeoutError(f"DefAPI task timed out: {task_id}")


def resolve_out_path(out_name: str) -> Path:
    if "/" in out_name:
        path = ROOT / out_name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return OUT / out_name


def generate_defapi(api_key: str, prompt: str, out_name: str, size: str) -> Path:
    print(f"[{out_name}] requesting DefAPI openai/gpt-image-2 {size} ...", flush=True)
    data = request_defapi_image(api_key, prompt, size)
    path = resolve_out_path(out_name)
    path.write_bytes(data)
    print(f"[{out_name}] saved ({len(data)//1024} KB) via DefAPI openai/gpt-image-2")
    return path


def generate_openai(api_key: str, prompt: str, out_name: str, size: str) -> Path:
    last_err: Exception | None = None
    for model in ("gpt-image-2", "gpt-image-1.5", "gpt-image-1"):
        try:
            print(f"[{out_name}] requesting {model} {size} ...", flush=True)
            data = request_openai_image(api_key, model, prompt, size)
            path = resolve_out_path(out_name)
            path.write_bytes(data)
            print(f"[{out_name}] saved ({len(data)//1024} KB) via {model}")
            return path
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"[{out_name}] {model} -> HTTP {e.code}: {err_body[:240]}", flush=True)
            last_err = e
        except Exception as e:  # noqa: BLE001
            print(f"[{out_name}] {model} -> {type(e).__name__}: {e}", flush=True)
            last_err = e
    raise RuntimeError(f"all models failed for {out_name}: {last_err}")


def generate(env: dict[str, str], prompt: str, out_name: str, size: str = "1536x1024") -> Path:
    defapi_key = (
        env.get("DEFAPI")
        or env.get("DEFAPI_API_KEY")
        or env.get("DEFAPI_KEY")
        or env.get("DefAPIkey")
    )
    if defapi_key:
        return generate_defapi(defapi_key, prompt, out_name, size)

    openai_key = env.get("OPENAI_API_KEY")
    if not openai_key:
        sys.exit("Set DEFAPI, DEFAPI_API_KEY, DEFAPI_KEY, or OPENAI_API_KEY in .env")
    return generate_openai(openai_key, prompt, out_name, size)


JOBS = [
    {
        "name": "assets/hero/homebanner.png",
        "size": "1536x1024",
        "prompt": (
            "Premium editorial wide hero photograph for a boutique web design studio. "
            "A single modern silver laptop sits OPEN on a refined warm cream desk, but photographed FROM A DISTANCE — "
            "the laptop occupies only the right third of the frame, small in scale, surrounded by lots of empty space and clean negative area. "
            "On the laptop screen there is a clean abstract website layout using only the brand colors: deep teal (#22b8ad / #62bcb3 mint) and soft mint accents on a near-white interface — no readable text, no logos, no brand names visible. "
            "Wide cinematic 3:2 composition, very generous negative space on the LEFT TWO THIRDS of the frame for large headline typography overlay, warm off-white / cream background that fades into a soft dark vignette on the left so white text overlays read clearly, subtle ambient studio lighting, soft long shadows, shallow but elegant depth of field, no people, no clutter, no decorative props, minimal sophisticated magazine aesthetic, photographic realism. "
            "Very airy, calm, breathable, premium feel."
        ),
    },
    {
        "name": "assets/services/personal.png",
        "size": "1536x1024",
        "prompt": (
            "Premium editorial wide flat-lay photograph evoking an intimate personal creative workspace — NO laptop, NO computer. "
            "On the right portion of the frame, beautifully styled personal items on a warm cream linen surface: an open leather-bound journal with handwritten-style ink swirls (no readable text), a slim matte fountain pen resting beside it, a single ceramic cappuccino mug with light steam, a small printed mood-board card with subtle teal (#22b8ad) and soft mint (#62bcb3) abstract geometric shapes, a folded pair of round acetate glasses, a single dried eucalyptus stem. "
            "Wide cinematic 3:2 composition shot from slightly above, very generous negative space on the LEFT TWO THIRDS of the frame for large white headline typography overlay, warm cream background fading into a soft dark vignette on the left so white text reads clearly, soft natural window light from the right with long gentle shadows, shallow elegant depth of field, no people, no logos, no readable text, no brand names, no laptops or screens or phones, magazine lifestyle photography aesthetic, photographic realism. "
            "Intimate, calm, breathable, premium feel."
        ),
    },
    {
        "name": "assets/services/business.png",
        "size": "1536x1024",
        "prompt": (
            "Premium editorial wide architectural interior photograph evoking a sleek modern business / corporate environment — NO laptop, NO computer, NO desk gadgets. "
            "On the right portion of the frame, the corner of a minimalist contemporary office space: a single curved cream leather lounge chair facing tall floor-to-ceiling windows with soft natural sunlight streaming in, a slim brushed metal floor lamp, a small abstract sculptural art piece in soft mint (#62bcb3) and deep teal (#22b8ad) on a low side console, polished travertine floor. "
            "Wide cinematic 3:2 composition, very generous negative space on the LEFT TWO THIRDS of the frame for large white headline typography overlay, warm cream / sand-colored walls fading into a soft dark vignette on the left so white text reads clearly, soft late-afternoon ambient light, shallow elegant depth of field, no people, no readable text, no logos, no signage, no brand names, magazine architectural / interior photography aesthetic, photographic realism. "
            "Sophisticated, calm, professional, premium feel."
        ),
    },
    {
        "name": "assets/services/restaurante.png",
        "size": "1536x1024",
        "prompt": (
            "Premium editorial wide photograph of an elegant boutique restaurant interior — NO laptop, NO computer, NO menus visible. "
            "On the right portion of the frame, a single beautifully styled empty dining table for two: pristine ivory linen tablecloth, two matte cream ceramic plates with subtle teal (#22b8ad) hand-painted detail, two folded linen napkins held by slim brass rings, two slender wine glasses, a single tall ivory taper candle softly lit, a low arrangement of soft mint (#62bcb3) eucalyptus and small white flowers. The defocused background shows warm wooden chairs and softly glowing pendant lights creating warm bokeh. "
            "Wide cinematic 3:2 composition, very generous negative space on the LEFT TWO THIRDS of the frame for large white headline typography overlay, warm cream and amber tones fading into a soft dark vignette on the left so white text reads clearly, intimate warm restaurant ambient lighting, shallow elegant depth of field, no people, no readable text, no logos, no signs, magazine hospitality / fine-dining photography aesthetic, photographic realism. "
            "Elegant, refined, premium feel."
        ),
    },
    {
        "name": "assets/services/eventos.png",
        "size": "1536x1024",
        "prompt": (
            "Premium editorial wide photograph of an elegant event venue, soft romantic ambience — NO laptop, NO computer, NO clutter. "
            "On the right portion of the frame, a section of a beautifully styled banquet — a long ivory linen runner stretching diagonally toward the background, low lush arrangements of soft mint (#62bcb3) eucalyptus and pale cream-colored garden roses with subtle teal (#22b8ad) accent ribbons, three tall slim ivory taper candles softly lit, polished gold cutlery glinting. The defocused background shows warm bokeh of overhead string lights and a gauzy ivory drapery, suggesting a wedding or upscale celebration. "
            "Wide cinematic 3:2 composition, very generous negative space on the LEFT TWO THIRDS of the frame for large white headline typography overlay, warm cream and golden tones fading into a soft dark vignette on the left so white text reads clearly, romantic warm soft lighting with abundant subtle bokeh, shallow elegant depth of field, no people, no readable text, no logos, no signage, no balloons, no confetti, magazine wedding / events photography aesthetic, photographic realism. "
            "Elegant, romantic, festive but sophisticated, premium feel."
        ),
    },
    {
        "name": "assets/services/ecommerce.png",
        "size": "1536x1024",
        "prompt": (
            "Premium editorial wide photograph of a small premium online boutique packaging scene — NO laptop, NO computer, NO screens. "
            "On the right portion of the frame, a beautifully styled product fulfillment vignette on a warm cream studio surface: a stack of two unbranded craft-paper kraft shipping boxes tied with soft mint (#62bcb3) silk ribbons, a folded cream cotton garment partially visible inside an open box, a folded kraft paper shopping bag with a deep teal (#22b8ad) handle, a small printed cream thank-you card with a subtle teal abstract geometric mark (no readable text), a roll of kraft paper, scattered loose bits of crumpled tissue paper. "
            "Wide cinematic 3:2 composition shot slightly from above at 35-degree angle, very generous negative space on the LEFT TWO THIRDS of the frame for large white headline typography overlay, warm cream background fading into a soft dark vignette on the left so white text reads clearly, soft natural studio lighting with gentle long shadows, shallow elegant depth of field, no people, no logos, no readable text, no brand names, magazine e-commerce / lifestyle still-life photography aesthetic, photographic realism. "
            "Calm, refined, premium feel."
        ),
    },
    {
        "name": "assets/hero/homebanner-mobile.png",
        "size": "1024x1536",
        "prompt": (
            "Premium editorial vertical hero photograph for a boutique web design studio, portrait 2:3 composition. "
            "A single modern silver laptop sits OPEN on a refined warm cream desk in the LOWER THIRD of the vertical frame, small in scale, photographed slightly from above and at distance, with lots of empty space around it. "
            "On the laptop screen there is a clean abstract website layout using only the brand colors: deep teal (#22b8ad) and soft mint (#62bcb3) accents on a near-white interface — no readable text, no logos, no brand names visible. "
            "The TOP TWO THIRDS of the image are generous negative space — a clean warm cream / off-white wall fading into a soft darker vignette at the very top so large white headline typography overlays read clearly. "
            "Subtle ambient studio lighting, soft long shadows behind the laptop, shallow elegant depth of field, no people, no clutter, no decorative props, minimal sophisticated magazine aesthetic, photographic realism. "
            "Vertical, calm, airy, premium feel, designed for a phone screen background."
        ),
    },
    {
        "name": "studio-vibe.png",
        "size": "1024x1024",
        "prompt": (
            "Premium abstract illustration of a modern web design studio essence. "
            "Floating geometric and organic forms — a glowing soft mint (#6fcbc7) liquid orb, "
            "a deep teal (#33596c) curved ribbon, light gray (#d9d9d9) thin grid lines, "
            "warm cream (#faf6ef) background. 3D soft-render, clay material, depth of field, "
            "luxurious and minimalist, no text, no logos, square composition, art-gallery quality."
        ),
    },
    {
        "name": "process-bg.png",
        "size": "1536x1024",
        "prompt": (
            "Ultra wide cinematic minimal background. Warm cream (#faf6ef) base, large soft "
            "mint (#6fcbc7) gradient blob in lower-left, subtle deep teal (#33596c) flowing line "
            "across the middle, very faint dotted grid texture, premium editorial feel, "
            "lots of negative space, no text, no objects, ready to host typography."
        ),
    },
    {
        "name": "cta-bg.png",
        "size": "1536x1024",
        "prompt": (
            "Premium magazine-style background. Deep teal (#33596c) base, smooth gradient to a "
            "mint (#6fcbc7) glow on the right, subtle abstract liquid waves, very high-end, "
            "minimal, calm, sophisticated, no text, no logos, ample empty space for headline."
        ),
    },
]


def main() -> int:
    env = load_env()
    filters = [a.lower() for a in sys.argv[1:]]
    failures = 0
    for job in JOBS:
        if filters and not any(f in job["name"].lower() for f in filters):
            continue
        try:
            generate(env, job["prompt"], job["name"], job["size"])
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {job['name']}: {e}")
            failures += 1
    return failures


if __name__ == "__main__":
    sys.exit(main())
