"""header.svg and footer.svg - replaces the capsule-render.vercel.app images.

A purple banner with a slow, seamless wave drift and a one-shot print-in
animation for the text. Both files are static: they only change when
scripts/config.py changes.
"""

import config
from common import (
    animate, animate_transform, rect, svg, t, text, wave_path, write_svg,
)

WIDTH = 1000
HEADER_HEIGHT = 230
FOOTER_HEIGHT = 150
HALF_PERIOD = 100          # 2 * HALF_PERIOD must divide WIDTH exactly
WAVE_CYCLE = 26            # seconds for one full drift
MONO = config.FONT_MONO


def gradient(ident, stops, x1="0%", y1="0%", x2="100%", y2="100%"):
    body = "".join(
        f'<stop offset="{offset}" stop-color="{color}"/>' for offset, color in stops
    )
    return (
        f'<linearGradient id="{ident}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
        f"{body}</linearGradient>"
    )


def drift_wave(y, amplitude, fill, opacity, height=HEADER_HEIGHT):
    """A tiled wave, twice as wide as the banner, scrolling left forever.

    The shape is drawn over [0, 2*WIDTH] and translated by -WIDTH, so the
    visible half is always covered and the loop point is invisible.
    """
    top = wave_path(WIDTH * 2, y, amplitude, HALF_PERIOD)
    path = f"{top} L {t(WIDTH * 2)} {t(height)} L 0 {t(height)} Z"
    return (
        f'<g opacity="{t(opacity)}">'
        f'<path d="{path}" fill="{fill}"/>'
        f'{animate_transform(f"0 0;-{t(WIDTH)} 0", dur=WAVE_CYCLE, repeat="indefinite", freeze=False)}'
        f"</g>"
    )


def build_header():
    defs = (
        gradient("hdr", [("0%", config.DEEP), ("45%", config.PRIMARY), ("100%", config.ACCENT)])
        + f'<clipPath id="rule"><rect x="430" y="128" width="0" height="5" rx="2.5">'
        f'{animate("width", "0;0;140", begin=0.9, dur=0.7, freeze=False)}'
        f"</rect></clipPath>"
    )

    body = [
        rect(0, 0, WIDTH, HEADER_HEIGHT, "url(#hdr)"),
        drift_wave(196, 13, "#FFFFFF", 0.08),
        drift_wave(209, 9, config.PALE, 0.16),
        f'<g opacity="0">{animate("opacity", "0;1", begin=0.15, dur=0.8)}'
        + text(500, 62, f"{config.USERNAME}@github ~ $ whoami", size=13, fill=config.PALE,
               anchor="middle", font=MONO, extra='letter-spacing="1.5"', opacity=0.8)
        + "</g>",
        f'<g opacity="0">{animate("opacity", "0;1", begin=0.45, dur=0.7)}'
        + text(500, 116, config.FULL_NAME, size=46, weight="700", fill="#FFFFFF", anchor="middle")
        + "</g>",
        f'<g clip-path="url(#rule)">{rect(430, 128, 140, 5, config.LIGHT, rx=2.5)}</g>',
        f'<g opacity="0">{animate("opacity", "0;1", begin=1.1, dur=0.7)}'
        + text(500, 168, config.ROLE, size=19, fill="#E9E5FF", anchor="middle",
               extra='letter-spacing="0.6"')
        + "</g>",
    ]
    return svg(
        WIDTH, HEADER_HEIGHT, "\n".join(body), defs=defs,
        title=f"{config.FULL_NAME} - {config.ROLE}",
        description="Animated purple banner with name and role.",
    )


def build_footer():
    defs = (
        gradient("ftr", [("0%", config.DEEP), ("50%", config.PRIMARY), ("100%", config.ACCENT)])
        + gradient("ftr-wave", [("0%", config.ACCENT), ("100%", config.PRIMARY)])
    )
    body = [
        rect(0, 0, WIDTH, FOOTER_HEIGHT, "url(#ftr)"),
        drift_wave(16, 8, "url(#ftr-wave)", 0.35, height=FOOTER_HEIGHT),
        *[
            f'<g opacity="0">{animate("opacity", "0;1", begin=0.2 + index * 0.25, dur=0.8)}'
            f"{element}</g>"
            for index, element in enumerate(
                [
                    text(500, 78, f'"{config.QUOTE}"', size=17, fill="#FFFFFF", anchor="middle"),
                    text(500, 112, f"{config.USERNAME} · {config.LOCATION} · "
                                   f"github.com/{config.USERNAME}",
                         size=13, fill="#E9E5FF", anchor="middle", font=MONO, opacity=0.85),
                ]
            )
        ],
    ]
    return svg(
        WIDTH, FOOTER_HEIGHT, "\n".join(body), defs=defs,
        title="Footer", description="Animated purple footer with a personal quote.",
    )


def main():
    write_svg("header.svg", build_header())
    write_svg("footer.svg", build_footer())


if __name__ == "__main__":
    main()
