import os
import re

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

from pathlib import Path
from transformers import MarianMTModel, MarianTokenizer
from markdown_utils import protect_text, restore_text

# =========================
# INPUTS (GitHub Action)
# =========================

# SOURCE_FILE = Path(os.environ["TRANSLATE_SOURCE"])
# SOURCE_LANGUAGE = os.environ["TRANSLATE_SOURCE_LANGUAGE"]
SOURCE_DIRECTORY = Path(os.environ["TRANSLATE_SOURCE"])
SOURCE_LANGUAGE = os.environ["TRANSLATE_SOURCE_LANGUAGE"]

# SOURCE_FILES = sorted(SOURCE_DIRECTORY.glob("*.cs.md"))
SOURCE_FILES = sorted(SOURCE_DIRECTORY.glob("*.md"))

MAIN_OUTPUT_ENV = os.environ.get("TRANSLATE_OUTPUT_MAIN", "")
MAIN_OUTPUT = Path(MAIN_OUTPUT_ENV) if MAIN_OUTPUT_ENV else None

if MAIN_OUTPUT:
    MAIN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

MAIN_LANGUAGE = os.environ.get("TRANSLATE_OUTPUT_MAIN_LANGUAGE" ) or SOURCE_LANGUAGE

OTHER_OUTPUT_PATH = Path(os.environ["TRANSLATE_OUTPUT_OTHER"])
OTHER_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

OTHER_LANGUAGES = [
    lang.strip()
    for lang in os.environ["TRANSLATE_OUTPUT_OTHER_LANGUAGE"].split(",")
    if lang.strip()
]

# -------------------------------------------------
# Translation direction
#
# If main output exists:
#   SOURCE -> MAIN
#   MAIN -> OTHER LANGUAGES
#
# If no main output:
#   SOURCE -> OTHER LANGUAGES
# -------------------------------------------------

MAIN_MODEL = None

if MAIN_LANGUAGE != SOURCE_LANGUAGE:
    MAIN_MODEL = (f"Helsinki-NLP/opus-mt-{SOURCE_LANGUAGE}-{MAIN_LANGUAGE}")

TRANSLATION_BASE_LANGUAGE = (
    MAIN_LANGUAGE
    if MAIN_LANGUAGE != SOURCE_LANGUAGE
    else SOURCE_LANGUAGE
)

OTHER_MODELS = {
    language: (
        f"Helsinki-NLP/opus-mt-"
        f"{TRANSLATION_BASE_LANGUAGE}-{language}"
    )
    for language in OTHER_LANGUAGES
}

# if not SOURCE_FILE.exists():
#     print(f"Info: No file {SOURCE_FILE}")
#     exit(0)

# if not SOURCE_FILES:
#     print(f"Info: No *.cs.md files in {SOURCE_DIRECTORY}")
#     exit(0)

if not SOURCE_FILES:
    print(f"Info: No Markdown files in {SOURCE_DIRECTORY}")
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

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    translated = model.generate(
        **inputs,
        max_length=512,
        num_beams=4
    )

    return tokenizer.decode(
        translated[0],
        skip_special_tokens=True
    )

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

            result.append(
                prefix + translate_text(content, tokenizer, model)
            )
            continue

        if not line.strip():
            result.append(line)
            continue

        result.append(
            translate_text(line, tokenizer, model)
        )

        if index % 10 == 0 or index == total:
            print(f"Progress: {index}/{total} lines ({index/total:.0%})", flush=True)

    translated = "\n".join(result)

    return restore_text(
        translated,
        protected
    )

# =============================================================================================================
# READ SOURCE FILE AND WRITE TRANSLATED OUTPUT
# Reads the source Markdown file, translates its content, and saves the translated version to the output file.
#
# (cs)
# Načte zdrojový Markdown soubor, přeloží jeho obsah a uloží přeloženou verzi do výstupního souboru.
# =============================================================================================================
# text = SOURCE_FILE.read_text(
#     encoding="utf-8"
# )

# print(" ")
# print(f"***** Working on {SOURCE_FILE} *****")

# if MAIN_OUTPUT and MAIN_MODEL:

#     print(f"Info: Translation from {SOURCE_LANGUAGE} → {MAIN_LANGUAGE}")

#     tokenizer, model = load_model(MAIN_MODEL)
#     translated = translate_markdown(text, tokenizer, model)

#     MAIN_OUTPUT.write_text(
#         translated,
#         encoding="utf-8"
#     )

#     text = translated

#     print(f"***** Finished *****")

# # Other translations
# for language, model_name in OTHER_MODELS.items():

#     print(" ")
#     print(f"***** Working on: {SOURCE_FILE} *****")
#     print(f"Info: Translation from {SOURCE_LANGUAGE} → {language}")

#     tokenizer, model = load_model(model_name)
#     translated = translate_markdown(text, tokenizer, model)
#     output_file = OTHER_OUTPUT_PATH / f"README.{language}.md"

#     output_file.write_text(
#         translated,
#         encoding="utf-8"
#     )

#     print(f"***** Finished: *****")

# print(" ")
# print("Done")

for SOURCE_FILE in SOURCE_FILES:

    text = SOURCE_FILE.read_text(
        encoding="utf-8"
    )

    print(" ")
    print(f"***** Working on {SOURCE_FILE} *****")


    if MAIN_OUTPUT and MAIN_MODEL:

        print(
            f"Info: Translation from {SOURCE_LANGUAGE} → {MAIN_LANGUAGE}"
        )

        tokenizer, model = load_model(MAIN_MODEL)

        translated = translate_markdown(
            text,
            tokenizer,
            model
        )

        # main_file = Path(
        #     f"{SOURCE_FILE.name.replace('.cs.md', '.md')}"
        # )

        main_file = Path(
            SOURCE_FILE.name
        )

        main_file.write_text(
            translated,
            encoding="utf-8"
        )

        text = translated

        print("***** Finished main language *****")

    for language, model_name in OTHER_MODELS.items():

        print(" ")
        print(
            f"Info: Translation from {SOURCE_LANGUAGE} → {language}"
        )

        tokenizer, model = load_model(
            model_name
        )

        translated = translate_markdown(
            text,
            tokenizer,
            model
        )

        # output_file = (
        #     OTHER_OUTPUT_PATH /
        #     SOURCE_FILE.name.replace(
        #         ".cs.md",
        #         f".{language}.md"
        #     )
        # )


        language_directory = (
            OTHER_OUTPUT_PATH /
            language
        )

        language_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            language_directory /
            SOURCE_FILE.name
        )



        output_file.write_text(
            translated,
            encoding="utf-8"
        )

        print(
            f"***** Finished: {output_file} *****"
        )

print(" ")
print("Done")