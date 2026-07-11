import re


# ============================================================
# COMMON MARKDOWN PROTECTION
#
# Protects Markdown elements that must not be modified:
# - GitHub alerts
# - badges
# - links
# - images
# - HTML tags
# - inline code
#
# Additional patterns can be added from individual scripts.
# ============================================================

BASE_PATTERNS = [
    r"^>\s*\[!.*?\].*$",          # GitHub alerts
    r"^\[!\[.*?\]\(.*?\)\].*$",   # badges
    r"\[[^\]]+\]\([^)]+\)",       # Markdown links
    r"!\[[^\]]*\]\([^)]+\)",      # Markdown images
    r"<[^>]+>",                   # HTML tags
    r"`[^`]+`",                   # Inline code
]


def protect_markdown(text, extra_patterns=None):

    global _counter

    protected = {}

    patterns = BASE_PATTERNS.copy()

    if extra_patterns:
        patterns.extend(extra_patterns)

    pattern = re.compile(
        "(?m)" + "|".join(patterns)
    )

    def replace(match):

        global _counter

        key = f"<<<RM_{_counter}>>>"

        protected[key] = match.group(0)

        _counter += 1

        return key

    result = pattern.sub(
        replace,
        text
    )

    return result, protected

def restore_markdown(text, protected):

    for key in sorted(
        protected.keys(),
        key=len,
        reverse=True
    ):
        text = text.replace(
            key,
            protected[key]
        )

    return text