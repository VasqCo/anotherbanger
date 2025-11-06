#!/usr/bin/env python3
import json
import os
import re
import secrets
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests
import yaml

try:
    import tweepy
except ImportError:
    tweepy = None


DEFAULT_FEATURES = {
    "responsive_web_home_pinned_timelines_enabled": False,
    "rweb_lists_timeline_redesign_enabled": False,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
    "responsive_web_edit_tweet_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_blue_subscription_verification_badge_is_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
    "standardized_nudges_misinfo": True,
    "tweet_awards_web_tipping_enabled": False,
    "responsive_web_media_download_video_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "responsive_web_promoted_badge_is_enabled": True,
    "responsive_web_graphql_refetch_enabled": True,
    "responsive_web_graphql_send_comment_to_h2_enabled": False,
    "responsive_web_grok_imagine_annotation_enabled": False,
    "profile_label_improvements_pcf_label_in_post_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": False,
    "responsive_web_jetfuel_frame": False,
    "graphql_is_translatable_rweb_tweet_is_translatable": False,
    "responsive_web_profile_redirect_enabled": False,
    "responsive_web_grok_analysis_button_from_backend": False,
    "responsive_web_twitter_article_tweet_consumption_enabled": False,
    "responsive_web_grok_share_attachment_enabled": False,
    "rweb_tipjar_consumption": False,
    "responsive_web_grok_community_note_auto_translation_is_enabled": False,
    "c9s_tweet_anatomy_moderator_badge_enabled": False,
    "responsive_web_grok_analyze_post_followups_enabled": False,
    "articles_preview_enabled": False,
    "premium_content_api_read_enabled": False,
    "responsive_web_grok_image_annotation_enabled": False,
    "payments_enabled": False,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": False,
    "view_counts_everywhere_api_enabled": False,
    "creator_subscriptions_quote_tweet_preview_enabled": False,
}


DEFAULT_FIELD_TOGGLES = {
    "withAuxiliaryUserLabels": False,
    "withArticleRichContentState": False,
}


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
    entries: list[Path] = []
    for line in new_posts_file.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_file():
            entries.append(path)
    return entries


def determine_mode() -> str:
    mode = os.getenv("TWITTER_MODE", "web").strip().lower()
    if mode not in {"api", "web"}:
        raise SystemExit(f"Unsupported TWITTER_MODE: {mode}")
    return mode


def load_json_from_env(name: str, default: dict[str, Any]) -> dict[str, Any]:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Unable to parse {name} as JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit(f"Environment variable {name} must contain a JSON object")
    merged = default.copy()
    merged.update(parsed)
    return merged


def create_api_client() -> Any:
    if tweepy is None:
        raise SystemExit("tweepy is not installed; install it or use TWITTER_MODE=web")

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
        raise SystemExit(f"Missing Twitter API credentials: {joined}")

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    return tweepy.API(auth)


def post_status_via_api(client: Any, status: str) -> None:
    client.update_status(status=status)


def post_status_via_web(status: str) -> None:
    auth_token = os.getenv("TWITTER_AUTH_TOKEN")
    ct0_token = os.getenv("TWITTER_CT0")
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    query_id = os.getenv("TWITTER_QUERY_ID", "MtyT_TbO2PpwaFHNPK2qoQ").strip()

    missing = [
        name
        for name, value in (
            ("TWITTER_AUTH_TOKEN", auth_token),
            ("TWITTER_CT0", ct0_token),
            ("TWITTER_BEARER_TOKEN", bearer_token),
            ("TWITTER_QUERY_ID", query_id),
        )
        if not value
    ]
    if missing:
        raise SystemExit(f"Missing web session secrets: {', '.join(missing)}")

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Origin": "https://x.com",
        "Referer": "https://x.com/compose/tweet",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "X-Csrf-Token": ct0_token,
        "X-Twitter-Active-User": "yes",
        "X-Twitter-Auth-Type": "OAuth2Session",
        "X-Twitter-Client-Language": "en",
        "X-Twitter-Client-Name": "Twitter Web App",
        "X-Twitter-Client-Version": "9.66.0",
    }

    extra_cookie_string = os.getenv("TWITTER_COOKIE_STRING", "")
    cookies: dict[str, str] = {
        "auth_token": auth_token,
        "ct0": ct0_token,
    }
    if extra_cookie_string:
        for part in extra_cookie_string.split(";"):
            name, _, value = part.strip().partition("=")
            if name and value:
                cookies[name] = value
    features = load_json_from_env("TWITTER_FEATURES_JSON", DEFAULT_FEATURES)
    field_toggles = load_json_from_env("TWITTER_FIELD_TOGGLES_JSON", DEFAULT_FIELD_TOGGLES)

    variables = {
        "tweet_text": status,
        "dark_request": False,
        "media": {
            "media_entities": [],
            "possibly_sensitive": False,
        },
        "semantic_annotation_ids": [],
    }

    payload = {
        "queryId": query_id,
        "variables": variables,
        "features": features,
        "fieldToggles": field_toggles,
    }

    transaction_id = secrets.token_urlsafe(16)
    headers["X-Client-Transaction-Id"] = transaction_id

    endpoint = f"https://x.com/i/api/graphql/{query_id}/CreateTweet"
    response = requests.post(
        endpoint,
        headers=headers,
        cookies=cookies,
        json=payload,
        timeout=15,
    )

    if response.status_code != 200:
        snippet = response.text[:280]
        raise SystemExit(f"Failed to post tweet via web session: {response.status_code} {snippet}")


def main() -> int:
    base_url = os.getenv("SITE_BASE_URL", "").rstrip("/")
    if not base_url:
        raise SystemExit("SITE_BASE_URL is not set; cannot build canonical URLs")

    posts = load_new_posts_list()
    if not posts:
        print("No new posts detected; skipping tweet")
        return 0

    mode = determine_mode()
    client = create_api_client() if mode == "api" else None

    for post_path in posts:
        print(f"Sharing post: {post_path}")
        front_matter, body = load_post(post_path)
        url = build_post_url(base_url, post_path, front_matter)
        status = build_status(front_matter, body, url)
        if mode == "api":
            post_status_via_api(client, status)
            print("Tweet posted via Twitter API")
        else:
            post_status_via_web(status)
            print("Tweet posted via web session")

    return 0


if __name__ == "__main__":
    sys.exit(main())
