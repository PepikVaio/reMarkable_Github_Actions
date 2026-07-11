import os
import re
import uuid

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
# Temporarily replaces technical elements with placeholders before translation.
# Prevents the translation model from modifying code, paths, extensions, and project specific names.
#
# Temporarily replaces Markdown syntax elements with placeholders before sending text to the correction API.
# This prevents the API from modifying links, badges, alerts, HTML tags, and other non-text parts of the document.
# Placeholders are restored after correction to keep the original Markdown structure.
#
# (cs)
# Dočasně nahradí technické prvky zástupnými značkami před překladem.
# Zabrání překladači upravovat kód, cesty, přípony a názvy projektů.
#
# Dočasně nahradí prvky Markdownu zástupnými značkami před odesláním textu do API.
# Zabrání tak úpravám odkazů, odznaků, upozornění, HTML tagů a dalších částí dokumentu, které nemají být opravovány.
# Po dokončení opravy se zástupné značky obnoví zpět na původní obsah a zachová se původní struktura Markdownu.
# ============================================================
def protect_text(text):

    protected = {}

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

        key = f"⟪VAR_{uuid.uuid4().hex[:8]}⟫"
        protected[key] = match.group(0)

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
