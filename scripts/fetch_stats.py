"""Collect the data every generated SVG needs, into data/stats.json.

Two public, token-free sources:

  * https://github.com/users/<user>/contributions  - the same HTML fragment the
    profile page renders. Gives the full 53-week calendar (level + exact count).
  * https://api.github.com/users/<user>(/repos)    - profile counters and the
    language of each public repository. Unauthenticated, so 60 calls/hour,
    which is far more than this workflow needs.

Nothing here needs a personal access token or a third-party service.

Usage:
    python scripts/fetch_stats.py
    python scripts/fetch_stats.py --from-html cached-page.html   # offline parse
"""

import argparse
import gzip
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import config
from common import ROOT

CONTRIB_URL = "https://github.com/users/{user}/contributions"
API = "https://api.github.com"
STATS_PATH = ROOT / "data" / "stats.json"
DAY_CELL = re.compile(r'<td[^>]*class="ContributionCalendar-day"[^>]*>')
ATTR = re.compile(r'(data-date|data-level|id)="([^"]*)"')
TOOLTIP = re.compile(r'<tool-tip[^>]*for="([^"]*)"[^>]*>([^<]*)</tool-tip>')
# "No contributions on May 5th." / "3 contributions on May 5th."
COUNT = re.compile(r"^\s*([\d,]+)\s+contribution", re.IGNORECASE)


def http_get(url, accept="text/html", timeout=30):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": config.USER_AGENT,
            "Accept": accept,
            # Ask for English so the tooltip text stays parseable.
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        if response.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", "replace")


def http_get_json(url, timeout=30):
    return json.loads(http_get(url, accept="application/vnd.github+json", timeout=timeout))


# ---------------------------------------------------------------------------
# Contribution calendar
# ---------------------------------------------------------------------------
def parse_contributions(html):
    """Return (days, exact_counts_available).

    The page is *not* an API, so this is deliberately defensive: day cells and
    tooltips are joined by the calendar cell id, and days whose count cannot be
    read keep count=None so downstream code can skip them instead of lying.
    """
    counts = {}
    for ref, label in TOOLTIP.findall(html):
        match = COUNT.match(label)
        if match:
            counts[ref] = int(match.group(1).replace(",", ""))

    days = []
    for tag in DAY_CELL.findall(html):
        attrs = dict(ATTR.findall(tag))
        raw_date, raw_level = attrs.get("data-date"), attrs.get("data-level")
        if not raw_date or raw_level is None:
            continue
        days.append(
            {
                "date": raw_date,
                "level": int(raw_level),
                "count": counts.get(attrs.get("id", "")),
            }
        )
    days.sort(key=lambda day: day["date"])

    # A non-zero day without a parsed count means the page layout changed.
    exact = all(day["count"] is not None for day in days if day["level"] > 0)
    return days, exact


def streaks(days):
    """(current, longest) runs of consecutive days with level > 0."""
    active = {date.fromisoformat(day["date"]) for day in days if day["level"] > 0}
    if not active:
        return 0, 0

    ordered = sorted(active)
    longest = run = 1
    for previous, current in zip(ordered, ordered[1:]):
        run = run + 1 if current - previous == timedelta(days=1) else 1
        longest = max(longest, run)

    last = max(date.fromisoformat(day["date"]) for day in days)
    cursor = last if last in active else last - timedelta(days=1)
    current = 0
    while cursor in active:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def parse_header_total(html):
    """The headline "9,376 contributions in the last year" figure, if present."""
    flat = re.sub(r"\s+", " ", html)
    match = re.search(r"([\d,]+) contributions? in the last year", flat, re.IGNORECASE)
    return int(match.group(1).replace(",", "")) if match else None


# ---------------------------------------------------------------------------
# Profile counters and languages
# ---------------------------------------------------------------------------
def fetch_repos(user):
    repos, page = [], 1
    while page <= 4:
        batch = http_get_json(
            f"{API}/users/{user}/repos?per_page=100&page={page}&sort=pushed"
        )
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def language_mix(repos):
    """Share of public repositories per language (forks excluded).

    Repo counts, not bytes: this is what GitHub's own "repos per language"
    card means, and repo size is dominated by vendored dependencies here.
    """
    by_language = {}
    for repo in repos:
        language = repo.get("language")
        if not language or repo.get("fork"):
            continue
        bucket = by_language.setdefault(language, {"bytes": 0, "repos": 0})
        bucket["bytes"] += int(repo.get("size") or 0)
        bucket["repos"] += 1

    total = sum(bucket["repos"] for bucket in by_language.values()) or 1
    ordered = sorted(
        by_language.items(), key=lambda item: (-item[1]["repos"], -item[1]["bytes"])
    )
    return [
        {
            "name": name,
            "bytes": bucket["bytes"],
            "repos": bucket["repos"],
            "share": bucket["repos"] / total,
        }
        for name, bucket in ordered
    ]


def previous_stats():
    """Last known good JSON, so a network hiccup does not blank the cards."""
    if STATS_PATH.exists():
        try:
            return json.loads(STATS_PATH.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-html",
        type=Path,
        help="parse a saved copy of the contributions page instead of fetching",
    )
    parser.add_argument(
        "--skip-profile",
        action="store_true",
        help="skip the api.github.com calls (data/stats.json keeps its old values)",
    )
    args = parser.parse_args(argv)

    if args.from_html:
        html = args.from_html.read_text(encoding="utf-8")
    else:
        html = http_get(CONTRIB_URL.format(user=config.USERNAME))

    days, exact = parse_contributions(html)
    if not days:
        print("error: no contribution cells found - GitHub markup changed?", file=sys.stderr)
        return 1

    total = parse_header_total(html)
    if total is None and exact:
        total = sum(day["count"] for day in days)

    current, longest = streaks(days)
    best = max((day for day in days if day["count"]), key=lambda d: d["count"], default=None)
    active_days = sum(1 for day in days if day["level"] > 0)

    old = previous_stats()
    profile = old.get("profile", {})
    languages = old.get("languages", [])
    if not args.skip_profile:
        user = http_get_json(f"{API}/users/{config.USERNAME}")
        repos = fetch_repos(config.USERNAME)
        profile = {
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "stars": sum(repo.get("stargazers_count", 0) for repo in repos),
            "created_at": user.get("created_at"),
            "first_year": int((user.get("created_at") or "2019-01-01")[:4]),
        }
        languages = language_mix(repos)
        print(f"profile: {profile['public_repos']} repos, {profile['followers']} followers")
        summary = ", ".join(
            f"{item['name']} {item['repos']}x" for item in languages
        )
        print(f"languages: {summary or 'none detected'}")

    data = {
        "username": config.USERNAME,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "totals": {
            "contributions": total,
            "active_days": active_days,
            "days": len(days),
            "exact_counts": exact,
        },
        "streaks": {"current": current, "longest": longest},
        "best_day": {"date": best["date"], "count": best["count"]} if best else None,
        "profile": profile,
        "languages": languages,
        "days": days,
    }

    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        f"wrote {STATS_PATH.relative_to(ROOT)}: {total} contributions, "
        f"{active_days} active days, {len(days)} days, "
        f"streak {current}/{longest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
