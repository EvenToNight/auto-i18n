import re
import subprocess
from typing import Optional
from utils.parsing_utils import build_key_paths

def find_changed_keys(input_file: str, previous_head: str, current_head: str)  -> Optional[set]:
    """Extract changed keys with full paths from git diff between two commits

    Args:
        input_file: Path to the source i18n file to check
        previous_head: Previous git commit hash
        current_head: Current git commit hash
        pattern: Regex pattern to match key-value pairs

    Returns:
        Set of changed full key paths, or None if no changes detected

    Raises:
        subprocess.CalledProcessError: If git command fails
        FileNotFoundError: If git is not installed
    """
    print(f"Checking for changes in '{input_file}' between {previous_head[:7]}...{current_head[:7]}")

    diff_result = subprocess.run(
        ["git", "diff", previous_head, current_head, input_file],
        capture_output=True,
        text=True,
        check=True
    )

    if not diff_result.stdout.strip():
        print(f"✓ No changes detected in '{input_file}'.")
        return None
    
    old_file_key_paths = build_key_paths(subprocess.run(
        ["git", "show", f"{previous_head}:{input_file}"],
        capture_output=True,
        text=True,
        check=True
    ).stdout)

    new_file_key_paths = build_key_paths(subprocess.run(
        ["git", "show", f"{current_head}:{input_file}"],
        capture_output=True,
        text=True,
        check=True
    ).stdout)

    changed_keys = set()
    for key, line_info in new_file_key_paths.items():
        old_line_info = old_file_key_paths.get(key)
        if not old_line_info or old_line_info["value"] != line_info["value"]:
            changed_keys.add(key)

    if changed_keys:
        print(f"✓ Detected changes in {len(changed_keys)} key(s): {', '.join(sorted(changed_keys))}")
        return changed_keys
    else:
        print(f"✓ Changes detected but no translatable keys modified.")
        return None
