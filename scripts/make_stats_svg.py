"""stats.svg - replaces the hosted stats/streak/quote widgets.

One self-contained card with the numbers that actually help a profile:
contributions, streaks, best day, active days, and the language mix of the
public repositories. Nothing here is fetched at render time: it all comes
from data/stats.json, so the image is served straight from the repo.

Usage:
    python scripts/make_stats_svg.py
"""

import json
import sys

import config
from common import ROOT, animate, animate_transform, mono_width, rect, svg, t, text, write_svg

WIDTH = 860
HEIGHT = 210
MARGIN = 40
TILE_TOP = 34
TILE_HEIGHT = 66
TILE_GAP = 10
BAR_TOP = 152
BAR_HEIGHT = 12
LEGEND_Y = 186
BAR_WIDTH = WIDTH - MARGIN * 2


def load_stats():
    path = ROOT / "data" / "stats.json"
    if not path.exists():
        print("error: data/stats.json missing - run scripts/fetch_stats.py first",
              file=sys.stderr)
        raise SystemExit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def days_label(count):
    if count is None:
        return "-"
    return f"{count} day" if count == 1 else f"{count} days"


def number(value):
    return f"{value:,}" if isinstance(value, int) else "-"


def kpi_tiles(data):
    """Five equal tiles, the first one highlighted."""
    totals = data.get("totals", {})
    streaks = data.get("streaks", {})
    best = data.get("best_day") or {}
    stats = [
        ("contributions", number(totals.get("contributions")), "LAST 12 MONTHS", True),
        ("current streak", days_label(streaks.get("current")), "CURRENT STREAK", False),
        ("longest streak", days_label(streaks.get("longest")), "LONGEST STREAK", False),
        ("best day", number(best.get("count")), "BUSIEST DAY", False),
        ("active days", number(totals.get("active_days")), "ACTIVE DAYS", False),
    ]

    width = (BAR_WIDTH - TILE_GAP * (len(stats) - 1)) / len(stats)
    body = []
    for index, (_, value, caption, highlight) in enumerate(stats):
        x = MARGIN + index * (width + TILE_GAP)
        border = config.ACCENT if highlight else config.BORDER
        body.append(
            f'<g opacity="0">{animate("opacity", "0;1", begin=0.2 + index * 0.12, dur=0.55)}'
            f'<g>{animate_transform("0 8;0 0", begin=0.2 + index * 0.12, dur=0.55)}'
            + rect(x, TILE_TOP, width, TILE_HEIGHT, config.CARD, rx=10)
            + f'<rect x="{t(x + 0.5)}" y="{t(TILE_TOP + 0.5)}" width="{t(width - 1)}" '
              f'height="{t(TILE_HEIGHT - 1)}" rx="10" fill="none" stroke="{border}"/>'
            + text(x + 14, TILE_TOP + 24, caption, size=10, fill=config.MUTED, font=config.FONT_MONO,
                   extra='letter-spacing="0.8"')
            + text(x + 14, TILE_TOP + 52, value, size=25, weight="700",
                   fill=config.PALE if highlight else config.TEXT)
            + "</g></g>"
        )
    return body


def language_bar(data):
    """Stacked bar plus legend, built from repo counts (not bytes)."""
    languages = [item for item in data.get("languages", []) if item.get("repos")]
    legend_y = LEGEND_Y
    if not languages:
        return [
            text(MARGIN, BAR_TOP + 10, "No public repositories with a detected language",
                 size=11, fill=config.MUTED, font=config.FONT_MONO)
        ]

    top = languages[:5]
    if len(languages) > len(top):
        other = sum(item["repos"] for item in languages[len(top):])
        top.append({"name": "Other", "repos": other, "share": other / sum(
            item["repos"] for item in languages)})

    total_repos = sum(item["repos"] for item in languages)
    offsets, cursor = [], 0.0
    for index, item in enumerate(top):
        width = item["share"] * BAR_WIDTH if index < len(top) - 1 else BAR_WIDTH - cursor
        offsets.append((cursor, width))
        cursor += width

    segments = "".join(
        rect(x, 0, width, BAR_HEIGHT, config.LANG_COLORS[index % len(config.LANG_COLORS)])
        for index, (x, width) in enumerate(offsets)
    )

    legend, cursor_x = [], float(MARGIN)
    for index, (item, (_, width)) in enumerate(zip(top, offsets)):
        color = config.LANG_COLORS[index % len(config.LANG_COLORS)]
        label = f"{item['name']} {item['repos']}"
        legend.append(f'<circle cx="{t(cursor_x + 4)}" cy="{t(legend_y - 4)}" r="4" fill="{color}"/>')
        legend.append(text(cursor_x + 14, legend_y, label, size=11, fill=config.MUTED,
                           font=config.FONT_MONO))
        cursor_x += 14 + mono_width(label, 11) + 18

    # Grow the whole stack from its left edge; the clip keeps the rounded ends.
    bar = (
        f'<clipPath id="bar-clip">'
        f'<rect x="{t(MARGIN)}" y="{t(BAR_TOP)}" width="{t(BAR_WIDTH)}" '
        f'height="{t(BAR_HEIGHT)}" rx="{t(BAR_HEIGHT / 2)}"/></clipPath>'
    )
    grow = (
        f'<g clip-path="url(#bar-clip)">'
        f'<g transform="translate({t(MARGIN)} {t(BAR_TOP)})" opacity="0">'
        f'{animate("opacity", "0;1", begin=0.75, dur=0.4)}'
        f'<g><animateTransform attributeName="transform" type="scale" values="0 1;1 1" '
        f'begin="0.75s" dur="0.9s" fill="freeze"/>{segments}</g>'
        f"</g></g>"
    )
    return bar, [
        text(MARGIN, BAR_TOP - 12, "PUBLIC REPOSITORIES BY LANGUAGE", size=10,
             fill=config.MUTED, font=config.FONT_MONO, extra='letter-spacing="0.8"'),
        grow,
        *legend,
        text(WIDTH - MARGIN, legend_y, f"{total_repos} PUBLIC REPOS", size=10,
             fill=config.MUTED, font=config.FONT_MONO, anchor="end",
             extra='letter-spacing="0.8"'),
    ]


def build():
    data = load_stats()
    first_year = (data.get("profile") or {}).get("first_year")
    stamp = (data.get("generated_at") or "")[:10]

    bar_defs, bar_body = language_bar(data)
    defs = (
        bar_defs
        + f'<linearGradient id="card-edge" x1="0%" y1="0%" x2="100%" y2="0%">'
          f'<stop offset="0%" stop-color="{config.ACCENT}"/>'
          f'<stop offset="100%" stop-color="{config.INDIGO}"/></linearGradient>'
        + f'<clipPath id="edge-clip"><rect x="{t(MARGIN)}" y="0" width="0" height="3" rx="1.5">'
          f'{animate("width", f"0;{t(WIDTH - MARGIN * 2)}", begin=0.1, dur=0.9)}'
          f"</rect></clipPath>"
    )

    meta = " · ".join(
        part for part in [
            f"since {first_year}" if first_year else None,
            f"updated {stamp}" if stamp else None,
            config.USERNAME,
        ] if part
    )

    body = [
        rect(0, 0, WIDTH, HEIGHT, config.BG, rx=16),
        f'<rect x="0.5" y="0.5" width="{t(WIDTH - 1)}" height="{t(HEIGHT - 1)}" rx="16" '
        f'fill="none" stroke="{config.BORDER}"/>',
        # Accent rule that wipes across the top edge of the card.
        f'<g opacity="0">{animate("opacity", "0;1", begin=0.1, dur=0.5)}'
        f'<g clip-path="url(#edge-clip)">'
        f'{rect(MARGIN, 0, WIDTH - MARGIN * 2, 3, "url(#card-edge)", rx=1.5)}</g></g>',
        *kpi_tiles(data),
        *bar_body,
        text(WIDTH / 2, HEIGHT - 8, meta, size=10, fill=config.MUTED, anchor="middle",
             font=config.FONT_MONO, opacity=0.75),
    ]

    return svg(WIDTH, HEIGHT, "\n".join(body), defs=defs,
               title=f"GitHub stats for {config.USERNAME}",
               description="Contributions, streaks and language mix.")


def main():
    write_svg("stats.svg", build())


if __name__ == "__main__":
    main()
