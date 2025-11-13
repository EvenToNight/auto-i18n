import os
import subprocess
from pathlib import Path
from typing import Optional
from utils.git_utils import find_changed_keys
from utils.translation_utils import extract_translations_info, translate_content

source_lang = os.getenv("INPUT_SOURCE")
targets = os.getenv("INPUT_TARGETS", "")
target_langs = [lang.strip() for lang in targets.split(",") if lang.strip()]
input_file = os.getenv("INPUT_INPUT_FILE")
previous_head = os.getenv("INPUT_PREVIOUS_HEAD", "")
current_head = os.getenv("INPUT_CURRENT_HEAD", "")
evaluate_changes = os.getenv("INPUT_EVALUATE_CHANGES", "true").lower() == "true"

def main():
    input_path = Path(input_file)
    if not input_path.is_file():
        print(f"File '{input_file}' does not exist")
        exit(1)

    input_content = input_path.read_text(encoding="utf-8")
    changed_keys = get_changed_keys(input_file, previous_head, current_head, evaluate_changes)
    output_dir = input_path.parent
    file_ext = input_path.suffix

    for tgt_lang in target_langs:
        output_file = output_dir / f"{tgt_lang}{file_ext}"
        ignored_key_lines = get_ignored_keys_and_lines(output_file, tgt_lang, changed_keys)
        translated_text = translate_content(input_content, source_lang, tgt_lang, ignored_key_lines, changed_keys)
        output_file.write_text(translated_text, encoding="utf-8")
        if changed_keys:
            print(f"✓ Updated {len(changed_keys)} translation(s) in '{output_file}'")
        else:
            print(f"✓ Translated '{input_file}' -> '{output_file}'")

def get_changed_keys(input_file: str, previous_head: str, current_head: str, evaluate_changes: bool) -> Optional[set]:
    if evaluate_changes:
        try:
            changed_keys = find_changed_keys(input_file, previous_head, current_head)
            if changed_keys is None:
                exit(0)
            return changed_keys
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not check git diff (error: {e}). Proceeding with full translation.")
        except FileNotFoundError:
            print("Warning: git command not found. Proceeding with full translation.")
    else:
        print("Change evaluation disabled. Proceeding with full translation.")
    return None

def get_ignored_keys_and_lines(output_file: Path, tgt_lang: str, changed_keys: Optional[set]) -> dict:
    ignored_key_lines = {}

    if output_file.exists():
        output_content = output_file.read_text(encoding="utf-8")
        ignored_keys, ignored_key_lines, existing_translations = extract_translations_info(output_content)

        if changed_keys:
            print(f"Translating only changed keys for '{tgt_lang}': {', '.join(sorted(changed_keys))}")
            for key, line in existing_translations.items():
                if key not in changed_keys and key not in ignored_keys:
                    ignored_key_lines[key] = line
        else:
            print(f"Translating all keys for '{tgt_lang}'")

        if ignored_keys:
            print(f"Found {len(ignored_keys)} key(s) marked with [ignorei18n] in '{output_file}' - will preserve")

    return ignored_key_lines

if __name__ == "__main__":
    main()