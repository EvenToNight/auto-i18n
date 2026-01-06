import re
from typing import Dict, Set, Tuple, Optional, List
from tree_sitter import Language, Parser, Node
from tree_sitter_typescript import language_typescript


KEY_VALUE_PATTERN = re.compile(
    r'["\']?([\w.-]+)["\']?\s*:\s*["\']([^"\']+)["\']'
)

OBJECT_START_PATTERN = re.compile(
    r'["\']?([\w.-]+)["\']?\s*:\s*\{'
)

# Initialize tree-sitter parser
TS_LANGUAGE = Language(language_typescript())
parser = Parser(TS_LANGUAGE)


def get_node_text(node: Node, source: bytes) -> str:
    """Extract text from a tree-sitter node"""
    return source[node.start_byte:node.end_byte].decode('utf-8')


def extract_string_value(node: Node, source: bytes) -> str:
    """Extract the actual string value without quotes"""
    text = get_node_text(node, source)
    # Remove surrounding quotes
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    return text


def find_comment_for_node(node: Node, source: bytes) -> Optional[str]:
    """Find [ignorei18n] comment associated with a node"""
    # Check next sibling for inline comment
    next_sibling = node.next_sibling
    while next_sibling and next_sibling.type == ',':
        next_sibling = next_sibling.next_sibling

    if next_sibling and next_sibling.type == 'comment':
        comment_text = get_node_text(next_sibling, source)
        if '[ignorei18n]' in comment_text:
            return '[ignorei18n]'

    return None


def parse_object_recursive(node: Node, source: bytes, path: List[str] = None) -> Dict[str, dict]:
    """Recursively parse object and extract translation keys with tree-sitter"""
    if path is None:
        path = []

    result = {}

    for child in node.named_children:
        if child.type == 'pair':
            # Extract key
            key_node = child.child_by_field_name('key')
            value_node = child.child_by_field_name('value')

            if not key_node or not value_node:
                continue

            key_text = get_node_text(key_node, source)
            # Remove quotes from key if present
            if (key_text.startswith('"') and key_text.endswith('"')) or \
               (key_text.startswith("'") and key_text.endswith("'")):
                key_text = key_text[1:-1]

            current_path = path + [key_text]
            full_key = '.'.join(current_path)

            # Check if value is a string
            if value_node.type == 'string':
                string_value = extract_string_value(value_node, source)
                quote_char = get_node_text(value_node, source)[0]
                comment = find_comment_for_node(child, source)

                result[full_key] = {
                    'value': string_value,
                    'quote': quote_char,
                    'comment': comment
                }

            # Check if value is an object (nested translations)
            elif value_node.type == 'object':
                nested = parse_object_recursive(value_node, source, current_path)
                result.update(nested)

    return result


def parse_ts_file(content: str) -> Dict[str, dict]:
    """Parse TypeScript/JavaScript file and extract all translation keys"""
    source_bytes = content.encode('utf-8')
    tree = parser.parse(source_bytes)
    root = tree.root_node

    result = {}

    # Find the exported object
    for node in root.named_children:
        if node.type == 'export_statement':
            # Look for default export or variable export
            for child in node.named_children:
                if child.type == 'object':
                    result.update(parse_object_recursive(child, source_bytes))
                elif child.type == 'lexical_declaration':
                    # Handle: export const translations = { ... }
                    for decl in child.named_children:
                        if decl.type == 'variable_declarator':
                            value = decl.child_by_field_name('value')
                            if value and value.type == 'object':
                                result.update(parse_object_recursive(value, source_bytes))
        elif node.type == 'lexical_declaration':
            # Handle non-exported const translations = { ... }
            for decl in node.named_children:
                if decl.type == 'variable_declarator':
                    value = decl.child_by_field_name('value')
                    if value and value.type == 'object':
                        result.update(parse_object_recursive(value, source_bytes))

    return result


def normalize_object_syntax(content: str) -> str:
    """
    Normalize JS object syntax into one-key-per-line format.
    Supports multiline values, apostrophes, unicode and ignore comments.
    """
    content = re.sub(r'\{\s*', '{\n', content)
    content = re.sub(r'\s*\}', '\n}', content)

    # Normalize key-value pairs onto single lines, removing commas
    def replace_kv(match):
        key = match.group(1)
        quote = match.group(2)
        value = match.group(3)
        comment = match.group(4) if match.group(4) else ''
        if comment:
            return f'{key}: {quote}{value}{quote} {comment}\n'
        else:
            return f'{key}: {quote}{value}{quote}\n'

    content = re.sub(
        r'(\w+)\s*:\s*(["\'])(.*?)\2\s*,?\s*(//\s*\[ignorei18n\].*)?',
        replace_kv,
        content,
        flags=re.DOTALL
    )
    content = re.sub(r'\n{2,}', '\n', content)
    return content.strip()

def build_key_paths(content: str) -> Dict[str, dict]:
    """
    Build full dot-separated paths for all translation keys using tree-sitter.
    """
    return parse_ts_file(content)

def restore_file(content: str, key_paths: Dict[str, dict]) -> str:
    """
    Build js/ts file with translations from original content using tree-sitter.
    Preserves structure and replaces values with translations.
    """
    source_bytes = content.encode('utf-8')
    tree = parser.parse(source_bytes)

    # Collect all replacements (position, old_value, new_value)
    replacements = []

    def collect_replacements(node: Node, path: List[str] = None):
        if path is None:
            path = []

        for child in node.named_children:
            if child.type == 'pair':
                key_node = child.child_by_field_name('key')
                value_node = child.child_by_field_name('value')

                if not key_node or not value_node:
                    continue

                key_text = get_node_text(key_node, source_bytes)
                if (key_text.startswith('"') and key_text.endswith('"')) or \
                   (key_text.startswith("'") and key_text.endswith("'")):
                    key_text = key_text[1:-1]

                current_path = path + [key_text]
                full_key = '.'.join(current_path)

                if value_node.type == 'string' and full_key in key_paths:
                    # Get the new value from key_paths
                    new_value = key_paths[full_key]['value']
                    quote_char = key_paths[full_key].get('quote', "'")

                    # Create replacement
                    replacements.append((
                        value_node.start_byte,
                        value_node.end_byte,
                        f"{quote_char}{new_value}{quote_char}"
                    ))

                elif value_node.type == 'object':
                    collect_replacements(value_node, current_path)

    # Find the exported object and collect replacements
    root = tree.root_node
    for node in root.named_children:
        if node.type == 'export_statement':
            for child in node.named_children:
                if child.type == 'object':
                    collect_replacements(child)
                elif child.type == 'lexical_declaration':
                    for decl in child.named_children:
                        if decl.type == 'variable_declarator':
                            value = decl.child_by_field_name('value')
                            if value and value.type == 'object':
                                collect_replacements(value)
        elif node.type == 'lexical_declaration':
            for decl in node.named_children:
                if decl.type == 'variable_declarator':
                    value = decl.child_by_field_name('value')
                    if value and value.type == 'object':
                        collect_replacements(value)

    # Apply replacements from end to start to maintain positions
    result = content
    for start, end, new_text in sorted(replacements, reverse=True, key=lambda x: x[0]):
        result = result[:start] + new_text + result[end:]

    return result