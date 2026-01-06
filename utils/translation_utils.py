import re
from deep_translator import GoogleTranslator

from utils.parsing_utils import build_key_paths, normalize_object_syntax, restore_file

def extract_translations_info(text: str, ignore_pattern: str = r'\[ignorei18n\]') -> tuple[set, dict, dict]:
    """Extract all translations and identify which ones are marked with [ignorei18n]

    Returns:
        ignored_keys: Set of keys marked with [ignorei18n]
        ignored_key_lines: Dict mapping ignored keys to their full lines
        all_translations: Dict mapping all keys to their full lines
    """
    ignored_keys = set()
    ignored_key_lines = {}
    all_translations = build_key_paths(text)

    for key, line_info in all_translations.items():
        if re.search(ignore_pattern, line_info["comment"] or ""):
            ignored_keys.add(key)
            ignored_key_lines[key] = line_info

    return ignored_keys, ignored_key_lines, all_translations

def translate_content(text:str, source_lang:str, tgt_lang:str, ignored_key_lines:dict, keys_to_translate:set, pattern = r'["\']?(\w+)["\']?\s*:\s*["\']([^"\']+)["\']', ignore_pattern = r'\[ignorei18n\]') -> str:
    """Translate content, preserving lines marked with [ignorei18n] in destination

    Args:
        text: Source text to translate
        source_lang: Source language code
        tgt_lang: Target language code
        ignored_key_lines: Dict mapping keys to their full lines from destination
        keys_to_translate: Set of specific keys to translate (None or empty set = translate all)
    """
    key_paths = build_key_paths(text)
    result_key_paths = __inject_ignored_line(key_paths, ignored_key_lines)
    final_key_paths = __translate_lines(result_key_paths, ignore_pattern, source_lang, tgt_lang, keys_to_translate)
    outText = restore_file(text, final_key_paths)
    return outText
    
def __inject_ignored_line(lines, ignored_key_lines):
    result_map = {}

    for key, line_info in lines.items():
        if key in ignored_key_lines:
            result_map[key] = ignored_key_lines[key]
        else:
            result_map[key] = line_info
    return result_map

def __translate_lines(lines, ignore_pattern: str, source_lang: str, tgt_lang: str, keys_to_translate: set) -> list:
    def replacer(match):
        original = match.group(0)
        stripped = original[1:-1]
        if not stripped.strip():
            return original
        current_try = 0
        max_tries = 3
        while current_try < max_tries:
            try:
                translated = GoogleTranslator(source=source_lang, target=tgt_lang).translate(stripped)
                break
            except Exception as e:
                current_try += 1
                print(f"Translation attempt {current_try} failed for '{stripped}': {e}")
                if current_try == max_tries:
                    print(f"Max translation attempts reached for '{stripped}'. Using original text.")
                    translated = stripped
        return f"\"{translated}\""
    
    result_map = {}
    for key, line_info in lines.items():        
        hasToBeIgnored = key not in keys_to_translate if keys_to_translate else True
        if re.search(ignore_pattern, line_info["comment"] or "") or hasToBeIgnored:
            result_map[key] = line_info
        else:
            print(f"Translating key: {key} with value: {line_info['value']}")
            translated_line = re.sub(r"(\".*?\"|'.*?')", replacer, line_info["value"])
            result_map[key] = {
                "value": translated_line,
                "comment": line_info["comment"]
            }   

    return result_map