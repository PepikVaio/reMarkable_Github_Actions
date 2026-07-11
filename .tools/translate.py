import os
import re

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

from pathlib import Path
from transformers import MarianMTModel, MarianTokenizer
from markdown_utils import protect_text, restore_text

# =========================
# INPUTS (GitHub Action)
# =========================
LANGUAGE_SOURCE = os.environ["LANGUAGE_SOURCE"]
PATH_LANGUAGE_OTHER = Path(os.environ["PATH_LANGUAGE_OTHER"])
TRANSLATE_FILE = os.environ.get("TRANSLATE_FILE", "").strip()

LANGUAGE_TRANSLATE = [
    lang.strip()
    for lang in os.environ["LANGUAGE_TRANSLATE"].split(",")
    if lang.strip()
]

if LANGUAGE_SOURCE == "en":
    SOURCE_DIRECTORY = Path(".")
else:
    SOURCE_DIRECTORY = (
        PATH_LANGUAGE_OTHER /
        LANGUAGE_SOURCE
    )

if TRANSLATE_FILE:
    SOURCE_FILES = [Path(TRANSLATE_FILE)]
else:
    SOURCE_FILES = sorted(SOURCE_DIRECTORY.glob("*.md"))

OTHER_LANGUAGES = [
    lang
    for lang in LANGUAGE_TRANSLATE
    if lang != LANGUAGE_SOURCE
]

if LANGUAGE_SOURCE != "en" and "en" not in OTHER_LANGUAGES:
    OTHER_LANGUAGES.insert(0, "en")

TRANSLATION_BASE_LANGUAGE = LANGUAGE_SOURCE

OTHER_MODELS = {
    language: (
        f"Helsinki-NLP/opus-mt-"
        f"{TRANSLATION_BASE_LANGUAGE}-{language}"
    )
    for language in OTHER_LANGUAGES
}

if not SOURCE_FILES:
    print(" ")
    print("Info: No files to translate")
    exit(0)

def load_model(model_name):
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)

    return tokenizer, model

# ===========================================================================
# TRANSLATE TEXT
# Translates a single text block while keeping protected elements unchanged.
#
# (cs)
# Přeloží jeden blok textu a zachová chráněné prvky beze změny.
# ===========================================================================
def translate_text(text, tokenizer, model):
    if not text.strip():
        return text

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    translated = model.generate(**inputs, max_length=512, num_beams=4)

    return tokenizer.decode(translated[0], skip_special_tokens=True)

# ==============================================================================================
# TRANSLATE MARKDOWN DOCUMENT
# Processes Markdown line by line while preserving Markdown formatting.
# Code blocks are skipped, headings keep their original markers, and empty lines are preserved.
#
# (cs)
# Zpracuje Markdown dokument řádek po řádku při zachování formátování Markdownu.
# Bloky kódu se přeskočí, nadpisy zachovají své značky a prázdné řádky zůstanou.
# ==============================================================================================
def translate_markdown(text, tokenizer, model):
    protected_text, protected = protect_text(text)
    result = []
    lines = protected_text.splitlines()
    total = len(lines)
    in_code = False

    for index, line in enumerate(lines, start=1):

        if line.startswith("```"):
            in_code = not in_code
            result.append(line)
            continue

        if in_code:
            result.append(line)
            continue

        if line.startswith("#"):
            prefix = re.match(r"^#+\s*", line).group()
            content = line[len(prefix):]

            result.append(prefix + translate_text(content, tokenizer, model))
            continue

        if not line.strip():
            result.append(line)
            continue

        result.append(translate_text(line, tokenizer, model))

        if index % 10 == 0 or index == total:
            print(f"Progress: {index}/{total} lines ({index/total:.0%})", flush=True)

    translated = "\n".join(result)

    return restore_text(translated, protected)

# =============================================================================================================
# READ SOURCE FILE AND WRITE TRANSLATED OUTPUT
# Reads the source Markdown file, translates its content, and saves the translated version to the output file.
#
# (cs)
# Načte zdrojový Markdown soubor, přeloží jeho obsah a uloží přeloženou verzi do výstupního souboru.
# =============================================================================================================
for SOURCE_FILE in SOURCE_FILES:
    text = SOURCE_FILE.read_text(encoding="utf-8")

    print(" ")
    print(f"***** Working on {SOURCE_FILE} *****")

    for language, model_name in OTHER_MODELS.items():
        print(f"Info: Translation from {LANGUAGE_SOURCE} → {language}")

        tokenizer, model = load_model(model_name)
        translated = translate_markdown(
            SOURCE_FILE.read_text(encoding="utf-8"),
            tokenizer,
            model
        )

        if language == "en":
            output_directory = Path(".")
        else:
            output_directory = (
                PATH_LANGUAGE_OTHER /
                language
            )

        output_directory.mkdir(parents=True, exist_ok=True)

        output_file = (
            output_directory /
            SOURCE_FILE.name
        )

        output_file.write_text(translated, encoding="utf-8")

    print(f"***** Finished: *****")

print(" ")
print("Done")
