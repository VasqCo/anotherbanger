#!/usr/bin/env python3
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import tweepy
import yaml

def load_post(post_path: Path) -> tuple[dict, str]:
    raw = post_path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    data = yaml.safe_load(parts[1])
    return (data or {}), parts[2]

def parse_date(value, fallback: tuple[int, int, int] | None) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        cleaned = value.strip().replace("Z", "+00:00")
        for fmt in (
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
        ):
            try:
                return datetime.strptime(cleaned[: len(fmt)], fmt).date()
            except ValueError:
                continue
    if fallback:
        year, month, day = fallback
        return date(int(year), int(month), int(day))
    raise ValueError("Unable to determine a publication date for the post")

def ensure_slug(front_matter: dict, fallback: str) -> str:
    slug = front_matter.get("slug")
    if isinstance(slug, str) and slug.strip():
        return slug.strip().strip("/")
    title = front_matter.get("title")
    if isinstance(title, str) and title.strip():
        provisional = re.sub(r"[^A-Za-z0-9]+", "-", title.strip()).strip("-")
        if provisional:
            return provisional
    return fallback.strip("/") or "post"

def build_post_url(base_url: str, post_path: Path, front_matter: dict) -> str:
    permalink = front_matter.get("permalink")
    if isinstance(permalink, str) and permalink.strip():
        permalink = permalink.strip()
        if permalink.startswith("http://") or permalink.startswith("https://"):
            return permalink
        return f"{base_url}/{permalink.lstrip('/')}"

    stem = post_path.stem
    parts = stem.split("-")
    if len(parts) < 4:
        raise ValueError(f"Post filename '{post_path}' is missing the expected 'YYYY-MM-DD-title' pattern")

    year, month, day, *slug_parts = parts
    pub_date = parse_date(front_matter.get("date"), (int(year), int(month), int(day)))
    slug_source = "-".join(slug_parts) or slug_parts[0] if slug_parts else "post"
    slug = ensure_slug(front_matter, slug_source)
    return f"{base_url}/blog/{pub_date.year:04d}/{pub_date.month:02d}/{pub_date.day:02d}/{slug}/"

def clean_excerpt(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\{\{[^}]+\}\}", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_excerpt(front_matter: dict, body: str) -> str:
    excerpt = front_matter.get("excerpt")
    if isinstance(excerpt, str) and excerpt.strip():
        return clean_excerpt(excerpt)

    if not body:
        return ""

    paragraphs = re.split(r"\n\s*\n", body.strip())
    for paragraph in paragraphs:
        candidate = clean_excerpt(paragraph)
        if candidate:
            return candidate
    return ""

def truncate_with_ellipsis(text: str, max_length: int) -> str:
    if max_length <= 0:
        return ""
    if len(text) <= max_length:
        return text
    if max_length == 1:
        return "…"
    return text[: max_length - 1].rstrip() + "…"

def build_status(front_matter: dict, body: str, url: str) -> str:
    title_value = front_matter.get("title")
    if not isinstance(title_value, str) or not title_value.strip():
        title_value = "Untitled"
    else:
        title_value = title_value.strip()

    title_prefix = "New Post: "
    title_line = f"{title_prefix}{title_value}"

    excerpt_line = extract_excerpt(front_matter, body)

    def compose(current_title: str, current_excerpt: str) -> str:
        parts = [current_title]
        if current_excerpt:
            parts.append(current_excerpt)
        parts.append(url)
        return "\n".join(parts)

    status = compose(title_line, excerpt_line)
    if len(status) <= 280:
        return status

    max_excerpt_len = 280 - len(title_line) - len(url) - (2 if excerpt_line else 1)
    if excerpt_line and len(excerpt_line) > max_excerpt_len:
        excerpt_line = truncate_with_ellipsis(excerpt_line, max_excerpt_len)
        status = compose(title_line, excerpt_line)
        if len(status) <= 280:
            return status

    max_title_value_len = 280 - len(title_prefix) - len(url) - (2 if excerpt_line else 1)
    if excerpt_line:
        max_title_value_len -= len(excerpt_line)
    title_value = truncate_with_ellipsis(title_value, max_title_value_len)
    title_line = f"{title_prefix}{title_value}" if title_value else title_prefix.rstrip()
    status = compose(title_line, excerpt_line)
    if len(status) <= 280:
        return status

    return compose(title_line, "")

def load_new_posts_list() -> list[Path]:
    new_posts_file = Path("new_posts.txt")
    if not new_posts_file.exists():
        return []
    entries = []
    for line in new_posts_file.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_file():
            entries.append(path)
    return entries

def create_client() -> tweepy.API:
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    missing = [
        name
        for name, value in (
            ("TWITTER_API_KEY", api_key),
            ("TWITTER_API_SECRET", api_secret),
            ("TWITTER_ACCESS_TOKEN", access_token),
            ("TWITTER_ACCESS_TOKEN_SECRET", access_secret),
        )
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing Twitter credentials: {joined}")

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    return tweepy.API(auth)

def main() -> int:
    base_url = os.getenv("SITE_BASE_URL", "").rstrip("/")
    if not base_url:
        raise SystemExit("SITE_BASE_URL is not set; cannot build canonical URLs")

    posts = load_new_posts_list()
    if not posts:
        print("No new posts detected; skipping tweet")
        return 0

    client = create_client()

    for post_path in posts:
        print(f"Sharing post: {post_path}")
        front_matter, body = load_post(post_path)
        url = build_post_url(base_url, post_path, front_matter)
        status = build_status(front_matter, body, url)
        client.update_status(status=status)
        print(f"Tweet posted: {status}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
