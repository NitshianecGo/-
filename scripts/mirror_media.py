#!/usr/bin/env python3
"""Optionally mirror RSS preview images to Cloudflare R2 as optimized WebP files.

This script is opt-in. Without all R2 environment variables it exits successfully
and leaves the news feed untouched. Videos are deliberately not copied: video
players (for example YouTube's privacy-enhanced embed) stay embedded on the site.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "data" / "news.json"
UA = "AzerothPulse/1.0 (+news thumbnail cache)"
MAX_DOWNLOAD = 8 * 1024 * 1024
MAX_ITEMS_PER_RUN = int(os.environ.get("R2_MAX_IMAGES_PER_RUN", "120"))
TIMEOUT = 18


def settings():
    account = os.environ.get("R2_ACCOUNT_ID", "").strip()
    key = os.environ.get("R2_ACCESS_KEY_ID", "").strip()
    secret = os.environ.get("R2_SECRET_ACCESS_KEY", "").strip()
    bucket = os.environ.get("R2_BUCKET_NAME", "").strip()
    public_base = os.environ.get("R2_PUBLIC_BASE_URL", "").strip().rstrip("/")
    return account, key, secret, bucket, public_base


def fetch_image(url: str) -> bytes:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("not an HTTP(S) image URL")
    host = parts.hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1", "metadata.google.internal"} or host.endswith(".local"):
        raise ValueError("local image hosts are not allowed")
    request = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "image/avif,image/webp,image/png,image/jpeg,image/gif,*/*;q=0.5",
    })
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_DOWNLOAD:
            raise ValueError("source image exceeds size limit")
        raw = response.read(MAX_DOWNLOAD + 1)
        if len(raw) > MAX_DOWNLOAD:
            raise ValueError("source image exceeds size limit")
        if content_type and not content_type.startswith("image/"):
            raise ValueError(f"source returned {content_type}, not an image")
        return raw


def optimize_image(raw: bytes) -> bytes:
    from PIL import Image, ImageOps

    with Image.open(io.BytesIO(raw)) as image:
        # RSS thumbnails only: use the first frame if the source is animated.
        image.seek(0)
        image = ImageOps.exif_transpose(image)
        image.thumbnail((1280, 900), Image.Resampling.LANCZOS)
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            image = image.convert("RGBA")
        else:
            image = image.convert("RGB")
        out = io.BytesIO()
        image.save(out, format="WEBP", quality=78, method=5)
        result = out.getvalue()
        if len(result) > 450 * 1024:
            image.thumbnail((1024, 720), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            image.save(out, format="WEBP", quality=66, method=5)
            result = out.getvalue()
        if not result or len(result) > 450 * 1024:
            raise ValueError("optimized thumbnail is still too large")
        return result


def main() -> int:
    account, access_key, secret, bucket, public_base = settings()
    if not all((account, access_key, secret, bucket, public_base)):
        print("[info] Cloudflare R2 not configured; external image URLs remain in the feed.")
        return 0
    if not FEED_PATH.exists():
        print("[error] news.json does not exist yet.")
        return 1

    import boto3
    from botocore.exceptions import ClientError

    data = json.loads(FEED_PATH.read_text(encoding="utf-8"))
    items = data.get("items", []) if isinstance(data, dict) else data
    client = boto3.client(
        "s3",
        endpoint_url=f"https://{account}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret,
        region_name="auto",
    )

    seen: dict[str, str] = {}
    cached = 0
    skipped = 0
    changed = False
    examined = 0

    for item in items:
        source_url = (item.get("image_origin") or item.get("image") or "").strip()
        if not source_url:
            continue
        if source_url.startswith(public_base + "/"):
            continue
        if source_url in seen:
            item["image_origin"] = source_url
            item["image"] = seen[source_url]
            item["image_cached"] = True
            changed = True
            continue
        if examined >= MAX_ITEMS_PER_RUN:
            skipped += 1
            continue
        examined += 1

        object_name = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:40] + ".webp"
        object_key = f"news/{object_name}"
        public_url = f"{public_base}/{object_key}"

        try:
            exists = False
            try:
                client.head_object(Bucket=bucket, Key=object_key)
                exists = True
            except ClientError as exc:
                status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                code = str(exc.response.get("Error", {}).get("Code", ""))
                if status != 404 and code not in {"404", "NoSuchKey", "NotFound"}:
                    raise

            if not exists:
                raw = fetch_image(source_url)
                optimized = optimize_image(raw)
                client.put_object(
                    Bucket=bucket,
                    Key=object_key,
                    Body=optimized,
                    ContentType="image/webp",
                    CacheControl="public, max-age=31536000, immutable",
                    Metadata={"source-sha256": hashlib.sha256(source_url.encode("utf-8")).hexdigest()},
                )
                print(f"[cached] {source_url} -> {object_key} ({len(optimized)} bytes)")
            else:
                print(f"[hit] {object_key}")

            seen[source_url] = public_url
            item["image_origin"] = source_url
            item["image"] = public_url
            item["image_cached"] = True
            changed = True
            cached += 1
        except Exception as exc:
            # Keep the original thumbnail URL so one blocked source cannot break the feed.
            print(f"[skip-image] {source_url}: {str(exc)[:180]}")
            skipped += 1
            time.sleep(0.05)

    if changed:
        if isinstance(data, dict):
            data["items_count"] = len(items)
        FEED_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[done] cached or reused {cached} image(s); skipped {skipped}; processed {examined}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
