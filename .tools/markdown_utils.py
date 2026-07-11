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



def protect_text(text):

    protected = {}
    counter = 0

    pattern = re.compile(
        r"(?m)"
        r"^>\s*\[!.*?\].*$"          # GitHub alerts
        r"|^\[!\[.*?\]\(.*?\)\].*$"  # badges
        r"|\[[^\]]+\]\([^)]+\)"      # Markdown links
        r"|!\[[^\]]*\]\([^)]+\)"     # Markdown images
        r"|<[^>]+>"                  # HTML tags
        r"|`[^`]+`"                  # Inline code
        r"|/[A-Za-z0-9_./-]+"        # Paths
        r"|\.[A-Za-z0-9]+"           # File extensions
        r"|\bXovi\b"
        r"|\bQt\b"
        r"|\bQML\b"
    )

    def replace(match):

        nonlocal counter

        key = f"rM_{counter}"

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
