"""Identity, copy and palette for the profile art.

This is the only file you need to edit when your details or colors change.
Re-run the scripts (or dispatch the GitHub Action) afterwards.
"""

USERNAME = "aleexdiiasz"
FULL_NAME = "Alejandro Díaz Silva"
ROLE = "Full Stack Developer | Software Engineer"
LOCATION = "Mexico City"

# Cycled one line at a time by typing.svg, in this order.
TAGLINES = [
    "Building scalable enterprise software",
    "ASP.NET Core | React | Laravel | AWS",
    "SaaS Multi-Tenant Architecture",
    "Backend Engineering | Cloud | Automation",
    "Turning business problems into reliable products",
]

QUOTE = "Great software transforms complex business problems into simple, reliable experiences."

# ---------------------------------------------------------------------------
# Palette: the same purple ramp already used across the README badges.
# ---------------------------------------------------------------------------
BG = "#0D1117"        # page/card background, matches the badges' background
CARD = "#111428"      # slightly lighter panel
BORDER = "#2E2A66"
DEEP = "#312E81"
PRIMARY = "#6D28D9"
ACCENT = "#7C3AED"
INDIGO = "#4F46E5"
LIGHT = "#A78BFA"
PALE = "#C4B5FD"
TEXT = "#E7E7F5"
MUTED = "#8C90A8"

# Heatmap ramp: level 0 (no activity) -> level 4 (busiest day), matching the
# five levels GitHub itself uses in the contribution calendar.
HEATMAP_LEVELS = ["#161B22", DEEP, INDIGO, ACCENT, LIGHT]

# Segments of the stacked "public repositories by language" bar.
LANG_COLORS = [ACCENT, PRIMARY, INDIGO, LIGHT, PALE, DEEP]

# SVG images are rendered in an isolated document: external fonts and
# stylesheets are NOT loaded, so only generic/system stacks work here.
FONT_MONO = "ui-monospace, SFMono-Regular, 'Cascadia Mono', Consolas, 'Liberation Mono', Menlo, monospace"
FONT_SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

USER_AGENT = f"{USERNAME}-profile-art/1.0 (+https://github.com/{USERNAME})"
