import os
import re
import requests
import subprocess
from pathlib import Path
from markdown_utils import protect_text, restore_text

# =========================
# INPUTS (GitHub Action)
# =========================
API = os.environ["DIACRITICS_API"]
DIACRITICS_FILE = os.environ.get("DIACRITICS_FILE", "").strip()
MODEL = os.environ["DIACRITICS_MODEL"]

# ======================================================================================
# ADD DIACRITICS IN FILE
# Sends file content to Korektor API and replaces original content with corrected text.
#
# (cs)
# Odešle obsah souboru do Korektor API a nahradí původní obsah opraveným textem.
# ======================================================================================
def restore_file(path: Path):
    print(f"***** Working on {path} *****")

    text = path.read_text(encoding="utf-8")
    original, protected = protect_text(text)

    print(f"Caution: Language correction only for cs language")
    print(f"Info: Protected elements {len(protected)}")

    response = requests.post(
        API,
        data={
            "data": original,
            "model": MODEL
        },
        timeout=60
    )

    response.raise_for_status()
    result = response.json()["result"]
    result = restore_text(result, protected)

    if text == result:
        print("Info: No changes required")
    else:
        original_words = text.split()
        result_words = result.split()

        for old, new in zip(original_words, result_words):
            if old != new:
                print(f"Changes: {old} -> {new}", flush=True)

    path.write_text(result, encoding="utf-8")

    print(f"***** Finished *****")

# =======================================================================================
# GET FILES CHANGED IN CURRENT PUSH
# Uses git history to find only files modified between previous and current commit.
#
# (cs)
# Pomocí historie Git zjistí pouze soubory změněné mezi předchozím a aktuálním commitem.
# =======================================================================================
def get_changed_files():
    result = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            "HEAD^",
            "HEAD"
        ],
        text=True
    )

    return [
        Path(file)
        for file in result.splitlines()
    ]

# ===============================================
# FILE SELECTION LOGIC (priority)
# 1. DIACRITICS_FILE defined:
#    - process only this file
#    - only if it was changed
# 2. DIACRITICS_FILE empty:
#    - process all changed Markdown files
#
# (cs)
# 1. DIACRITICS_FILE vyplněné:
#    - zpracuje pouze tento soubor
#    - pouze pokud byl změněn
# 2. DIACRITICS_FILE prázdné:
#    - zpracuje všechny změněné Markdown soubory
# ===============================================
changed_files = get_changed_files()

if DIACRITICS_FILE:
    files = [
        Path(DIACRITICS_FILE)
    ] if Path(DIACRITICS_FILE) in changed_files else []
else:
    source_language = os.environ["LANGUAGE_SOURCE"]
    language_directory = Path(os.environ["PATH_LANGUAGE_OTHER"])

    if source_language == "en":
        source_directory = Path(".")
    else:
        source_directory = (
            language_directory /
            source_language
        )

    files = [
        file
        for file in source_directory.glob("*.md")
        if file in changed_files
    ]

if not files:
    print(" ")
    print("No files to repair")
    print("Done")
    exit(0)

for file in files:
    if file.is_file():
        restore_file(file)

print(" ")
print("Done")
