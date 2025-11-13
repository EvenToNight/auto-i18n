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

# Regex pattern for key-value pairs
KEY_VALUE_PATTERN = r'["\']?(\w+)["\']?\s*:\s*["\']([^"\']+)["\']'

def extract_ignored_keys_info(text):
    """Extract keys marked with [ignorei18n] and their full lines"""
    ignored_keys = set()
    key_lines = {}

    for line in text.split('\n'):
        if '[ignorei18n]' in line:
            match = re.search(KEY_VALUE_PATTERN, line)
            if match:
                key = match.group(1)
                ignored_keys.add(key)
                key_lines[key] = line

    return ignored_keys, key_lines

def translate_content(text, src, tgt, ignored_keys, ignored_key_lines):
    """Translate content, preserving lines marked with [ignorei18n] in destination"""
    # First pass: replace entire lines for ignored keys from destination
    lines = text.split('\n')
    result_lines = []

    for line in lines:
        match = re.search(KEY_VALUE_PATTERN, line)
        if match:
            key = match.group(1)
            # Use preserved line from destination if key is ignored
            if key in ignored_keys and key in ignored_key_lines:
                result_lines.append(ignored_key_lines[key])
                continue

        result_lines.append(line)

    text = '\n'.join(result_lines)

    # Second pass: translate all non-ignored string values
    def replacer(match):
        original = match.group(0)
        quote = original[0]
        stripped = original[1:-1]

        # Skip empty strings
        if not stripped.strip():
            return original

        # Find the line containing this match
        start, end = match.span()
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        if line_end == -1:
            line_end = len(text)
        line = text[line_start:line_end]

        # Skip if line has [ignorei18n] (already preserved in first pass)
        if '[ignorei18n]' in line:
            return original

        # Translate
        translated = GoogleTranslator(source=src, target=tgt).translate(stripped)

        # Escape quotes to match the quote type
        if quote == "'":
            translated = translated.replace("'", "\\'")
        else:
            translated = translated.replace('"', '\\"')

        return f"{quote}{translated}{quote}"

    return re.sub(r"(\".*?\"|'.*?')", replacer, text)

output_dir = input_path.parent
file_ext = input_path.suffix

for tgt_lang in target_langs:
    output_file = output_dir / f"{tgt_lang}{file_ext}"

    # Load ignored keys from destination file if it exists
    ignored_keys = set()
    ignored_key_lines = {}

    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
            ignored_keys, ignored_key_lines = extract_ignored_keys_info(existing_content)

            if ignored_keys:
                print(f"Found {len(ignored_keys)} key(s) marked with [ignorei18n] in '{output_file}' - will preserve")

    # Translate, preserving ignored keys and their comments
    translated_text = translate_content(content, source_lang, tgt_lang, ignored_keys, ignored_key_lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(translated_text)
    print(f"✓ Translated '{input_file}' -> '{output_file}'")
