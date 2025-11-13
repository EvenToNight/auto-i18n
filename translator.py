import os
import re
import subprocess
from pathlib import Path
from deep_translator import GoogleTranslator

source_lang = os.getenv("INPUT_SOURCE")
targets = os.getenv("INPUT_TARGETS", "")
target_langs = [lang.strip() for lang in targets.split(",") if lang.strip()]
input_file = os.getenv("INPUT_INPUT_FILE")
previous_head = os.getenv("INPUT_PREVIOUS_HEAD", "")
current_head = os.getenv("INPUT_CURRENT_HEAD", "")
evaluate_changes = os.getenv("INPUT_EVALUATE_CHANGES", "true").lower() == "true"
update_only_new = os.getenv("INPUT_UPDATE_ONLY_NEW", "true").lower() == "true"

input_path = Path(input_file)
if not input_path.is_file():
    print(f"File '{input_file}' does not exist")
    exit(1)

if evaluate_changes:
    print(f"Checking for changes in '{input_file}' since {previous_head[:7]}...")
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", previous_head, current_head, str(input_path)],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.getcwd()
        )
        
        if not result.stdout.strip():
            print(f"✓ No changes detected in '{input_file}'. Skipping translation.")
            exit(0)
        else:
            print(f"✓ Changes detected in '{input_file}'. Proceeding with translation.")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not check git diff (error: {e}). Proceeding with translation anyway.")
    except FileNotFoundError:
        print("Warning: git command not found. Proceeding with translation anyway.")
else:
    print("Change evaluation disabled. Proceeding with translation.")

with open(input_path, "r", encoding="utf-8") as f:
    content = f.read()

def extract_key_value_pairs(text):
    """Extract key-value pairs from i18n file"""
    # Match: key: "value" or "key": "value"
    pattern = r'["\']?(\w+)["\']?\s*:\s*["\']([^"\']+)["\']'
    return {match.group(1): match.group(2) for match in re.finditer(pattern, text)}

def translate_content(text, src, tgt, existing_translations=None):
    """Translate content, preserving existing translations from target file"""
    if existing_translations is None:
        existing_translations = {}

    pattern = r"(\".*?\"|'.*?')"

    def replacer(match):
        original = match.group(0)
        quote = original[0]
        stripped = original[1:-1]

        start, end = match.span()
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        if line_end == -1:
            line_end = len(text)
        line = text[line_start:line_end]

        after_string = line[end - line_start:]
        if "//" in after_string and "[ignorei18n]" in after_string:
            return original

        if stripped.strip() == "":
            return original

        # Check if the line contains a key that exists in existing translations
        key_match = re.search(r'["\']?(\w+)["\']?\s*:\s*', line)
        if key_match:
            key = key_match.group(1)
            if key in existing_translations:
                # Use existing translation for this key
                existing_value = existing_translations[key]
                # Escape quotes in existing translation to match the quote type
                if quote == "'":
                    existing_value = existing_value.replace("'", "\\'")
                else:
                    existing_value = existing_value.replace('"', '\\"')
                return f"{quote}{existing_value}{quote}"

        # Translate new or updated strings
        translated = GoogleTranslator(source=src, target=tgt).translate(stripped)

        # Escape quotes in translated string to match the quote type
        if quote == "'":
            translated = translated.replace("'", "\\'")
        else:
            translated = translated.replace('"', '\\"')

        return f"{quote}{translated}{quote}"

    return re.sub(pattern, replacer, text)

output_dir = input_path.parent
file_ext = input_path.suffix

for tgt_lang in target_langs:
    output_file = output_dir / f"{tgt_lang}{file_ext}"

    # Load existing translations if the target file already exists and update_only_new is enabled
    existing_translations = {}
    if update_only_new and output_file.exists():
        print(f"Loading existing translations from '{output_file}'...")
        with open(output_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
            existing_translations = extract_key_value_pairs(existing_content)
            print(f"  Found {len(existing_translations)} existing translation(s) to preserve")
    elif not update_only_new:
        print(f"Re-translating all keys for '{output_file}'...")

    translated_text = translate_content(content, source_lang, tgt_lang, existing_translations)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(translated_text)
    print(f"✓ Translated '{input_file}' -> '{output_file}'")