import re
from typing import Dict, Set, Tuple


KEY_VALUE_PATTERN = re.compile(
    r'["\']?([\w.-]+)["\']?\s*:\s*["\']([^"\']+)["\']'
)

OBJECT_START_PATTERN = re.compile(
    r'["\']?([\w.-]+)["\']?\s*:\s*\{'
)


def normalize_object_syntax(content: str) -> str:
    """
    Normalize JS object syntax into one-key-per-line format.
    Supports multiline values, apostrophes, unicode and ignore comments.
    """
    content = re.sub(r'\{\s*', '{\n', content)
    content = re.sub(r'\s*\}', '\n}', content)
    content = re.sub(
        r'(\w+)\s*:\s*(["\'])(.*?)\2\s*,?\s*(//\s*\[ignorei18n\].*)?',
        r'\1: \2\3\2 \4\n',
        content,
        flags=re.DOTALL
    )
    content = re.sub(r',', '', content)
    content = re.sub(r'\n{2,}', '\n', content)
    return content.strip()

def build_key_paths(content: str) -> Dict[str, str]:
    """
    Build full dot-separated paths for all translation keys.
    """

    content = normalize_object_syntax(content)
    lines = content.splitlines()

    key_paths: Dict[str, str] = {}
    path_stack: list[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith('export '):
            continue

        obj_match = OBJECT_START_PATTERN.match(stripped)
        if obj_match:
            path_stack.append(obj_match.group(1))
            continue

        if stripped.startswith('}'):
            if path_stack:
                path_stack.pop()
            continue

        kv_match = KEY_VALUE_PATTERN.match(stripped)
        if kv_match:
            key = kv_match.group(1)
            full_path = '.'.join(path_stack + [key])
            
            comment = None
            line_without_comment = stripped
            comment_match = re.search(r'//\s*(\[.*?\])', stripped)
            if comment_match:
                comment = comment_match.group(1)
                line_without_comment = stripped[:comment_match.start()].rstrip()
            key_paths[full_path] = {
                'value': line_without_comment,
                'comment': comment
            }
    return key_paths

def restore_file(content: str, key_paths: Dict[str, str]) -> Dict[str, str]:
    """
    Build js/ts file with translations from original content.
    """

    content = normalize_object_syntax(content)
    lines = content.splitlines()

    path_stack: list[str] = []

    output_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith('export '):
            output_lines.append(line)
            continue

        obj_match = OBJECT_START_PATTERN.match(stripped)
        if obj_match:
            path_stack.append(obj_match.group(1))
            output_lines.append(line)
            continue

        if stripped.startswith('}'):
            if path_stack:
                path_stack.pop()
            output_lines.append(line)
            continue

        kv_match = KEY_VALUE_PATTERN.match(stripped)
        if kv_match:
            key = kv_match.group(1)
            full_path = '.'.join(path_stack + [key])
            comment = key_paths[full_path]["comment"]
            output_lines.append(
                key_paths[full_path]["value"]+", " + (f"//{comment}" if comment else "")
            )
    return '\n'.join(output_lines)