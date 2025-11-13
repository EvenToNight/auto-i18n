import re
from deep_translator import GoogleTranslator

def extract_translations_info(text: str, pattern: str = r'["\']?(\w+)["\']?\s*:\s*["\']([^"\']+)["\']', ignore_pattern: str = r'\[ignorei18n\]') -> tuple[set, dict, dict]:
    """Extract all translations and identify which ones are marked with [ignorei18n]

    Returns:
        ignored_keys: Set of keys marked with [ignorei18n]
        ignored_key_lines: Dict mapping ignored keys to their full lines
        all_translations: Dict mapping all keys to their full lines
    """
    ignored_keys = set()
    ignored_key_lines = {}
    all_translations = {}

    for line in text.split('\n'):
        match = re.search(pattern, line)
        if match:
            key = match.group(1)
            all_translations[key] = line

            if re.search(ignore_pattern, line):
                ignored_keys.add(key)
                ignored_key_lines[key] = line

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
    lines = text.split('\n')
    result_lines = __inject_ignored_line(lines, ignored_key_lines, pattern)
    final_lines = __translate_lines(result_lines, ignore_pattern, pattern, source_lang, tgt_lang, keys_to_translate)
    return '\n'.join(final_lines)

def __inject_ignored_line(lines, ignored_key_lines, pattern):
    result_lines = []
    for line in lines:
        match = re.search(pattern, line)
        if match:
            key = match.group(1)
            if key in ignored_key_lines:
                result_lines.append(ignored_key_lines[key])
                continue
        result_lines.append(line)
    return result_lines

def __translate_lines(lines: list, ignore_pattern: str, pattern: str, source_lang: str, tgt_lang: str, keys_to_translate: set) -> list:
    result_lines = []
    for line in lines:
        if re.search(ignore_pattern, line):
            result_lines.append(line)
            continue

        key_match = re.search(pattern, line)
        if key_match:
            key = key_match.group(1)
            if keys_to_translate and key not in keys_to_translate:
                result_lines.append(line)
                continue

        def replacer(match):
            original = match.group(0)
            quote = original[0]
            stripped = original[1:-1]

            if not stripped.strip():
                return original

            translated = GoogleTranslator(source=source_lang, target=tgt_lang).translate(stripped)

            if quote == "'":
                translated = translated.replace("'", "\\'")
            else:
                translated = translated.replace('"', '\\"')

            return f"{quote}{translated}{quote}"

        translated_line = re.sub(r"(\".*?\"|'.*?')", replacer, line)
        result_lines.append(translated_line)
    return result_lines