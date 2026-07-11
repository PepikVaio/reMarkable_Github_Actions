import re
import os

# =========================
# INPUTS (GitHub Action)
# =========================
CUSTOM_PROTECTED_WORDS = [
    word.strip()
    for word in os.environ.get("PROTECTED_WORDS", "").split(",")
    if word.strip()
]

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



def protect_text(text):

    protected = {}
    counter = 0

    patterns = [
        r"^>\s*\[!.*?\].*$",
        r"^\[!\[.*?\]\(.*?\)\].*$",
        r"\[[^\]]+\]\([^)]+\)",
        r"!\[[^\]]*\]\([^)]+\)",
        r"<[^>]+>",
        r"`[^`]+`",
        r"/[A-Za-z0-9_./-]+",
        r"\.[A-Za-z0-9]+",
    ]

    for word in CUSTOM_PROTECTED_WORDS:
        patterns.append(
            rf"\b{re.escape(word)}\b"
        )

    pattern = re.compile(
        r"(?m)" + "|".join(patterns)
    )


    def replace(match):

        nonlocal counter

        # key = f"MARKDOWN_PLACEHOLDER_{counter}"
        key = f"XOVI_{counter}"

        protected[key] = match.group(0)

        counter += 1

        return key

    result = pattern.sub(
        replace,
        text
    )

    return result, protected

def restore_text(text, protected):

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
