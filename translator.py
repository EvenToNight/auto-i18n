import os
import re
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

def translate_content(text, src, tgt):
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

        translated = GoogleTranslator(source=src, target=tgt).translate(stripped)
        return f"{quote}{translated}{quote}"

    return re.sub(pattern, replacer, text)

output_dir = input_path.parent
file_ext = input_path.suffix

for tgt_lang in target_langs:
    translated_text = translate_content(content, source_lang, tgt_lang)
    output_file = output_dir / f"{tgt_lang}{file_ext}"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(translated_text)
    print(f"Translated '{input_file}' -> '{output_file}'")
