import re
import subprocess
from typing import Optional


def find_changed_keys(input_file: str, previous_head: str, current_head: str, pattern: str = r'["\']?(\w+)["\']?\s*:\s*["\']([^"\']+)["\']')  -> Optional[set]:
    """Extract changed keys from git diff between two commits

    Args:
        input_file: Path to the source i18n file to check
        previous_head: Previous git commit hash
        current_head: Current git commit hash
        pattern: Regex pattern to match key-value pairs

    Returns:
        Set of changed keys, or None if no changes detected

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
        print(f"✓ No changes detected in '{input_file}'. Skipping translation.")
        return None

    changed_keys = set()
    for line in diff_result.stdout.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            match = re.search(pattern, line[1:])
            if match:
                changed_keys.add(match.group(1))

    if changed_keys:
        print(f"✓ Detected changes in {len(changed_keys)} key(s): {', '.join(sorted(changed_keys))}")
        return changed_keys
    else:
        print(f"✓ Changes detected but no translatable keys modified.")
        return None
