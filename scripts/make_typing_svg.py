"""typing.svg - replaces the readme-typing-svg.demolab.com widget.

One tagline at a time, wiped in left to right by an animated clip, with a
blinking block cursor riding the wipe edge. The cycle repeats forever, which
is what the original widget did.

Timing is expressed as fractions of the total cycle because SMIL keyTimes are
normalised to [0, 1].
"""

import config
from common import animate, animate_transform, mono_width, rect, svg, t, text, write_svg

WIDTH = 900
HEIGHT = 64
FONT_SIZE = 22
TEXT_CENTER = 480        # nudged right to clear the window dots
CURSOR_WIDTH = 11
CURSOR_HEIGHT = 26
LEAD_IN = 0.35           # seconds before the first character appears
CHAR_SECONDS = 0.045     # per-character wipe speed
HOLD_SECONDS = 1.5
FADE_SECONDS = 0.4
BLINK_SECONDS = 1.0


def slots():
    """Per-tagline (start, wipe, fade_start, end) timings, in seconds."""
    timeline, clock = [], LEAD_IN
    for line in config.TAGLINES:
        wipe = max(0.7, min(1.8, len(line) * CHAR_SECONDS))
        timeline.append((clock, wipe, clock + wipe + HOLD_SECONDS,
                         clock + wipe + HOLD_SECONDS + FADE_SECONDS))
        clock = timeline[-1][3]
    return timeline, clock


def fractions(values, total):
    """Normalise to keyTimes: clamp to [0,1], keep strictly increasing."""
    out = [min(1.0, max(0.0, value / total)) for value in values]
    for index in range(1, len(out)):
        if out[index] <= out[index - 1]:
            out[index] = min(1.0, out[index - 1] + 1e-4)
    return out


def build():
    timeline, cycle = slots()
    defs, body = [], []

    defs.append(f'<clipPath id="dot-clip"><rect x="0" y="0" width="{t(WIDTH)}" '
                f'height="{t(HEIGHT)}" rx="12"/></clipPath>')

    for index, (start, wipe, fade_start, end) in enumerate(timeline):
        line = config.TAGLINES[index]
        width = mono_width(line, FONT_SIZE) + 8
        left = TEXT_CENTER - mono_width(line, FONT_SIZE) / 2 - 4

        # The clip wipes the character row in, then stays open until the fade.
        wipe_anim = animate(
            "width", f"0;0;{t(width)};{t(width)}", begin=0, dur=cycle,
            key_times=fractions([0, start, start + wipe, cycle], cycle),
            repeat="indefinite", freeze=False,
        )
        defs.append(
            f'<clipPath id="wipe{index}">'
            f'<rect x="{t(left)}" y="14" width="0" height="{t(CURSOR_HEIGHT + 8)}">'
            f"{wipe_anim}</rect></clipPath>"
        )

        # The gate hides the whole line outside its slot and fades it out.
        gate = ["0", "1", "1", "0", "0"]
        times = [0, start, fade_start, end, cycle]
        if start > 0.1:                      # needs an explicit "still hidden" point
            gate = ["0", "0", "1", "1", "0", "0"]
            times = [0, start - 0.05, start, fade_start, end, cycle]
        gate_anim = animate(
            "opacity", ";".join(gate), begin=0, dur=cycle,
            key_times=fractions(times, cycle), repeat="indefinite", freeze=False,
        )

        cursor_move = animate_transform(
            f"0 0;0 0;{t(width)} 0;{t(width)} 0", begin=0, dur=cycle,
            key_times=fractions([0, start, start + wipe, cycle], cycle),
            repeat="indefinite", freeze=False,
        )
        cursor_blink = animate(
            "fill-opacity", "1;1;0.1;1", begin=0, dur=BLINK_SECONDS,
            repeat="indefinite", freeze=False,
        )

        body.append(
            f'<g opacity="0">{gate_anim}'
            f'<g clip-path="url(#wipe{index})">'
            f"{text(TEXT_CENTER, 40, line, size=FONT_SIZE, fill=config.PALE, anchor='middle', font=config.FONT_MONO)}"
            f"</g>"
            f'<rect x="{t(left)}" y="17" width="{t(CURSOR_WIDTH)}" height="{t(CURSOR_HEIGHT)}" '
            f'rx="2" fill="{config.LIGHT}">{cursor_move}{cursor_blink}</rect>'
            f"</g>"
        )

    dots = "".join(
        f'<circle cx="{t(26 + offset * 20)}" cy="{t(HEIGHT / 2)}" r="5" fill="{color}" '
        f'opacity="0.9"/>'
        for offset, color in enumerate([config.ACCENT, config.PRIMARY, config.INDIGO])
    )
    panel = (
        rect(0, 0, WIDTH, HEIGHT, config.CARD, rx=12)
        + f'<rect x="0.5" y="0.5" width="{t(WIDTH - 1)}" height="{t(HEIGHT - 1)}" rx="12" '
          f'fill="none" stroke="{config.BORDER}"/>'
        + f'<g clip-path="url(#dot-clip)">{dots}</g>'
    )
    return svg(
        WIDTH, HEIGHT, panel + "\n".join(body), defs="\n".join(defs),
        title=", ".join(config.TAGLINES),
        description="Self-typing terminal panel cycling through taglines.",
    )


def main():
    write_svg("typing.svg", build())


if __name__ == "__main__":
    main()
