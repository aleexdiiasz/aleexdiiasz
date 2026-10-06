"""Small SVG toolkit shared by the generators (standard library only).

Everything here assumes one constraint: the SVG is rendered by GitHub inside
an <img> tag. That means no JavaScript, no external stylesheets, no external
fonts, and animations must be SMIL or SVG-internal CSS.
"""

from pathlib import Path

import config

ROOT = Path(__file__).resolve().parent.parent


def esc(text):
    """Escape text for use in XML text nodes and attribute values."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def t(value):
    """Format a number of seconds/coordinates compactly for SMIL attributes."""
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def animate(attr, values, begin=0.0, dur=0.6, key_times=None, repeat=None, freeze=True):
    parts = [
        f'attributeName="{attr}"',
        f'values="{values}"',
        f'begin="{t(begin)}s"',
        f'dur="{t(dur)}s"',
        'fill="freeze"' if freeze else 'fill="remove"',
    ]
    if key_times:
        parts.append(f'keyTimes="{";".join(t(k) for k in key_times)}"')
    if repeat:
        parts.append(f'repeatCount="{repeat}"')
    return f"<animate {' '.join(parts)}/>"


def animate_transform(values, begin=0.0, dur=0.6, key_times=None, repeat=None, freeze=True):
    parts = [
        'attributeName="transform"',
        'type="translate"',
        f'values="{values}"',
        f'begin="{t(begin)}s"',
        f'dur="{t(dur)}s"',
        'fill="freeze"' if freeze else 'fill="remove"',
    ]
    if key_times:
        parts.append(f'keyTimes="{";".join(t(k) for k in key_times)}"')
    if repeat:
        parts.append(f'repeatCount="{repeat}"')
    return f"<animateTransform {' '.join(parts)}/>"


def reveal(begin=0.0, dur=0.5, offset="0 6"):
    """Fade + rise into place, then freeze. Used for every printed element."""
    return [
        animate("opacity", "0;1", begin=begin, dur=dur),
        animate_transform(f"{offset};0 0", begin=begin, dur=dur),
    ]


def text(x, y, value, size=14, fill=None, weight="400", anchor="start", font=None, extra="", opacity=None):
    attrs = [
        f'x="{t(x)}"',
        f'y="{t(y)}"',
        f'font-family="{font or config.FONT_SANS}"',
        f'font-size="{t(size)}"',
        f'font-weight="{weight}"',
        f'fill="{fill or config.TEXT}"',
    ]
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    if extra:
        attrs.append(extra)
    return f"<text {' '.join(attrs)}>{esc(value)}</text>"


def rect(x, y, w, h, fill, rx=0, extra=""):
    r = f' rx="{t(rx)}"' if rx else ""
    e = f" {extra}" if extra else ""
    return (
        f'<rect x="{t(x)}" y="{t(y)}" width="{t(w)}" height="{t(h)}" '
        f'fill="{fill}"{r}{e}/>'
    )


def mono_width(value, size, factor=0.62):
    """Width of a monospace run. Slightly overestimated on purpose: for the
    typing clip that is safe, an underestimate would cut glyphs off."""
    return len(value) * size * factor


def wave_path(width, y, amplitude, half_period, direction=1):
    """A periodic sine-ish wave drawn with cubic segments, closed to the bottom.

    `half_period` divides `width` exactly so the path can be tiled seamlessly
    and scrolled for a looping drift.
    """
    lift = amplitude * 4 / 3
    d = [f"M 0 {t(y)}"]
    x = 0.0
    flip = direction
    while round(x, 6) < width:
        d.append(
            f"c {t(half_period / 3)} {t(-lift * flip)} "
            f"{t(half_period * 2 / 3)} {t(-lift * flip)} {t(half_period)} 0"
        )
        x += half_period
        flip *= -1
    return " ".join(d)


def svg(width, height, body, defs="", title=None, description=None):
    """Wrap body content in a standalone SVG document."""
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{t(width)}" height="{t(height)}"',
        f' viewBox="0 0 {t(width)} {t(height)}" role="img">',
    ]
    if title:
        head.append(f"<title>{esc(title)}</title>")
    if description:
        head.append(f"<desc>{esc(description)}</desc>")
    parts = ["".join(head)]
    if defs:
        parts.append(f"<defs>{defs}</defs>")
    parts.append(body)
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_svg(filename, content):
    path = ROOT / filename
    # newline="\n": keep LF on Windows too, so a local render is byte-identical
    # to the one the Linux runner commits (otherwise every Action run would
    # commit a CRLF/LF flip).
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(ROOT)} ({len(content):,} chars)")
    return path
