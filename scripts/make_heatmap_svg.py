"""contrib-heatmap.svg - replaces the hosted activity graph.

The real 53-week contribution calendar, drawn as rounded boxes that slide in
diagonally and then freeze, plus a Less/More legend and a stats line. Every
box carries a native <title> tooltip, so hovering a day shows its exact count.

Usage:
    python scripts/make_heatmap_svg.py
"""

import json
import sys
from datetime import date

import config
from common import ROOT, animate, animate_transform, rect, svg, t, text, write_svg

WIDTH = 860
HEIGHT = 224
CELL = 11
GAP = 3
PITCH = CELL + GAP
GUTTER = 34                 # room for the Mon/Wed/Fri labels
GRID_TOP = 46
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}
STAGGER = 0.028             # seconds between diagonals
START = 0.35


def load_stats():
    path = ROOT / "data" / "stats.json"
    if not path.exists():
        print("error: data/stats.json missing - run scripts/fetch_stats.py first",
              file=sys.stderr)
        raise SystemExit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def pretty(day):
    parsed = date.fromisoformat(day)
    return f"{MONTHS[parsed.month - 1]} {parsed.day}, {parsed.year}"


def grid(days):
    """Return [(column, row, day)] plus the column count.

    Rows are Sunday..Saturday and columns are weeks, derived from each day's own
    date. That is how GitHub lays the calendar out, and it stays correct even if
    the first or last week is partial.
    """
    ordered = sorted(days, key=lambda item: item["date"])
    origin = date.fromisoformat(ordered[0]["date"])
    cells, columns = [], 0
    for day in ordered:
        offset = (date.fromisoformat(day["date"]) - origin).days
        column, row = offset // 7, offset % 7
        columns = max(columns, column + 1)
        cells.append((column, row, day))
    return cells, columns


def tooltip(day):
    count = day.get("count")
    if count is None:
        return pretty(day["date"])
    if count == 0:
        return f"No contributions on {pretty(day['date'])}"
    plural = "contribution" if count == 1 else "contributions"
    return f"{count} {plural} on {pretty(day['date'])}"


def cell_groups(cells):
    """One animated group per diagonal: 59 animations for all ~370 boxes."""
    by_diagonal = {}
    for column, row, day in cells:
        level = min(int(day.get("level") or 0), len(config.HEATMAP_LEVELS) - 1)
        box = (
            f'<rect x="{t(column * PITCH)}" y="{t(row * PITCH)}" width="{CELL}" '
            f'height="{CELL}" rx="2.5" fill="{config.HEATMAP_LEVELS[level]}">'
            f"<title>{tooltip(day)}</title></rect>"
        )
        by_diagonal.setdefault(column + row, []).append(box)

    groups = []
    for index, diagonal in enumerate(sorted(by_diagonal)):
        begin = START + index * STAGGER
        groups.append(
            f'<g opacity="0">'
            f'{animate("opacity", "0;1", begin=begin, dur=0.45)}'
            f'{animate_transform("0 4;0 0", begin=begin, dur=0.45)}'
            f'{"".join(by_diagonal[diagonal])}</g>'
        )
    return groups


def month_labels(cells, columns, left):
    """A month label above the first column whose week starts in a new month."""
    first_of_column = {}
    for column, _, day in cells:
        first_of_column.setdefault(column, day["date"])

    labels, current = [], None
    for column in range(columns):
        raw = first_of_column.get(column)
        if not raw:
            continue
        month = date.fromisoformat(raw).month
        if month != current:
            current = month
            labels.append(text(left + column * PITCH, GRID_TOP - 10, MONTHS[month - 1],
                               size=10, fill=config.MUTED, font=config.FONT_MONO))
    return labels


def build():
    data = load_stats()
    cells, columns = grid(data["days"])
    grid_width = columns * PITCH - GAP
    grid_height = 7 * PITCH - GAP
    left = max(GUTTER, (WIDTH - grid_width) / 2)

    marks = "".join(
        text(-8, row * PITCH + CELL - 1.5, label, size=10, fill=config.MUTED,
             anchor="end", font=config.FONT_MONO)
        for row, label in DAY_LABELS.items()
    )

    totals = data.get("totals", {})
    streaks = data.get("streaks", {})
    best = data.get("best_day") or {}
    summary = " · ".join(
        part for part in [
            f"{totals.get('contributions', 0):,} contributions in the last year",
            f"{totals.get('active_days', 0)} active days",
            f"longest streak {streaks.get('longest', 0)} days",
            f"best day {best.get('count')}" if best.get("count") else None,
        ] if part
    )

    legend_y = GRID_TOP + grid_height + 18
    step = CELL + 4
    legend_width = 34 + len(config.HEATMAP_LEVELS) * step + 44
    legend_x = (WIDTH - legend_width) / 2
    legend = [
        text(legend_x, legend_y + CELL - 1, "Less", size=10, fill=config.MUTED,
             font=config.FONT_MONO)
    ]
    for index, color in enumerate(config.HEATMAP_LEVELS):
        legend.append(
            f'<g opacity="0">'
            f'{animate("opacity", "0;1", begin=START + index * 0.06, dur=0.4)}'
            f'{rect(legend_x + 34 + index * step, legend_y, CELL, CELL, color, rx=2.5)}</g>'
        )
    legend.append(
        text(legend_x + 34 + len(config.HEATMAP_LEVELS) * step + 6,
             legend_y + CELL - 1, "More", size=10, fill=config.MUTED, font=config.FONT_MONO)
    )

    heading = text(24, 26, "CONTRIBUTION ACTIVITY", size=10, fill=config.MUTED,
                   font=config.FONT_MONO, extra='letter-spacing="1"')

    body = [
        rect(0, 0, WIDTH, HEIGHT, config.BG, rx=16),
        f'<rect x="0.5" y="0.5" width="{t(WIDTH - 1)}" height="{t(HEIGHT - 1)}" rx="16" '
        f'fill="none" stroke="{config.BORDER}"/>',
        f'<g opacity="0">{animate("opacity", "0;1", begin=0.15, dur=0.5)}{heading}</g>',
        f'<g transform="translate({t(left)} {t(GRID_TOP)})">{marks}'
        f'{"".join(cell_groups(cells))}</g>',
        *month_labels(cells, columns, left),
        *legend,
        text(WIDTH / 2, HEIGHT - 12, summary, size=11, fill=config.MUTED, anchor="middle",
             font=config.FONT_MONO),
    ]

    return svg(WIDTH, HEIGHT, "\n".join(body),
               title=f"Contribution activity for {config.USERNAME}",
               description="Animated 53-week contribution calendar.")


def main():
    write_svg("contrib-heatmap.svg", build())


if __name__ == "__main__":
    main()
