#!/usr/bin/env python3
"""Build microsite pages from brew new-formulae JSON (0 28 --json --desc).

Reads one JSON file (last 28 days), splits by date into yesterday / last 7 days /
last 28 days, and writes docs/index.html, docs/28-days.html, docs/yesterday.html
from a single template with top nav.

Usage:
    python3 build_homepage.py <path-to-new-formulae-28.json>
    python3 build_homepage.py new-formulae-28.json

Run from repo root. Template: docs/page.html.template. Output: docs/.
"""

import argparse
import html
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse


def parse_iso_to_utc_date(iso_str: str):
    """Parse tap_added_time (ISO) to UTC date. Handles Z and +00:00."""
    s = iso_str.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date()


def load_and_split(json_path: Path):
    """Load JSON and split into yesterday, last_7_days, last_28_days (all)."""
    with open(json_path, encoding="utf-8") as f:
        records = json.load(f)
    if not isinstance(records, list):
        records = []

    today_utc = datetime.now(timezone.utc).date()
    yesterday_utc = today_utc - timedelta(days=1)
    cutoff_7 = today_utc - timedelta(days=7)

    yesterday_list = []
    last_7_list = []
    last_28_list = []

    for r in records:
        try:
            d = parse_iso_to_utc_date(r["tap_added_time"])
        except (KeyError, TypeError, ValueError):
            continue
        last_28_list.append(r)
        if d >= cutoff_7 and d <= today_utc:
            last_7_list.append(r)
        if d == yesterday_utc:
            yesterday_list.append(r)

    # Sort each by date newest first
    def by_date(x):
        try:
            return parse_iso_to_utc_date(x["tap_added_time"]), x["tap_added_time"]
        except (KeyError, TypeError, ValueError):
            return (today_utc, "")

    for lst in (yesterday_list, last_7_list, last_28_list):
        lst.sort(key=by_date, reverse=True)

    return yesterday_list, last_7_list, last_28_list


def _safe_homepage_url(url: str) -> str | None:
    """Return URL if it is a safe http/https URL for hyperlinking; else None."""
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    try:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return url
    except Exception:
        pass
    return None


def render_list(records: list, empty_message: str) -> str:
    """Render records as HTML fragment. Hyperlink formula name when homepage present; [Formula]/[Cask] only when linked to tap source repo."""
    if not records:
        return f'<p class="formula-meta">{html.escape(empty_message)}</p>'
    parts = []
    for r in records:
        name = html.escape(r.get("formula", ""))
        tap = html.escape(r.get("tap", ""))
        kind = r.get("type", "Formula")
        date_str = r.get("tap_added_time", "")[:10]
        desc = (r.get("description") or "").strip()
        if desc:
            desc = " – " + html.escape(desc[:200])
        homepage = _safe_homepage_url(r.get("homepage") or "")
        if homepage:
            href = html.escape(homepage, quote=True)
            name_block = f'<a href="{href}" class="formula-name" rel="noopener noreferrer">{name}</a>'
        else:
            name_block = f'<span class="formula-name">{name}</span>'
        tap_url = _safe_homepage_url(r.get("tap_url") or "")
        if tap_url:
            kind_href = html.escape(tap_url, quote=True)
            kind_block = f' <a href="{kind_href}" class="formula-tap" rel="noopener noreferrer">[{kind}]</a>'
        else:
            kind_block = ""
        parts.append(
            f'<div class="formula-item">'
            f'{name_block}{kind_block}'
            f'<div class="formula-meta">{date_str} · {tap}{desc}</div>'
            f"</div>"
        )
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Build 7d / 28d / yesterday microsite pages from brew new-formulae JSON.",
    )
    parser.add_argument(
        "json_path",
        type=Path,
        help="Path to JSON file (output of brew new-formulae 0 28 --json --desc)",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs"),
        help="Directory containing template and output (default: docs)",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=None,
        help="Template path (default: <docs-dir>/page.html.template)",
    )
    args = parser.parse_args()

    json_path = args.json_path.resolve()
    if not json_path.is_file():
        raise SystemExit(f"Not a file: {json_path}")

    docs_dir = args.docs_dir.resolve()
    template_path = (args.template or docs_dir / "page.html.template").resolve()
    if not template_path.is_file():
        raise SystemExit(f"Template not found: {template_path}")

    yesterday_list, last_7_list, last_28_list = load_and_split(json_path)

    with open(template_path, encoding="utf-8") as f:
        template = f.read()

    pages = [
        (
            "index.html",
            "New formulae (last 7 days)",
            last_7_list,
            "No new formulae in the last 7 days.",
            ' aria-current="page"',
            "",
            "",
        ),
        (
            "28-days.html",
            "New formulae (last 28 days)",
            last_28_list,
            "No new formulae in the last 28 days.",
            "",
            ' aria-current="page"',
            "",
        ),
        (
            "yesterday.html",
            "New formulae (yesterday)",
            yesterday_list,
            "No new formulae added yesterday.",
            "",
            "",
            ' aria-current="page"',
        ),
    ]

    for filename, page_title, records, empty_msg, nav_7, nav_28, nav_yest in pages:
        list_html = render_list(records, empty_msg)
        out = (
            template.replace("{{PAGE_TITLE}}", html.escape(page_title))
            .replace("{{NAV_7DAYS_ATTR}}", nav_7)
            .replace("{{NAV_28DAYS_ATTR}}", nav_28)
            .replace("{{NAV_YESTERDAY_ATTR}}", nav_yest)
            .replace("{{NEW_FORMULAE_LIST}}", list_html)
        )
        out_path = docs_dir / filename
        out_path.write_text(out, encoding="utf-8")
        print(f"Wrote {out_path}", flush=True)


if __name__ == "__main__":
    main()
