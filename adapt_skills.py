#!/usr/bin/env python3
"""Adapt browser-harness domain-skills to camoufox-harness Playwright API."""
import re
from pathlib import Path

DOMAIN_SKILLS = Path("domain-skills")

# Replacements: browser-harness → camoufox-harness
REPLACEMENTS = [
    # Async wrappers
    (r'\bgoto\(', 'await goto('),
    (r'\bwait_for_load\(', 'await wait_for_load('),
    (r'\bwait\(', 'await wait('),
    (r'\bscreenshot\(', 'await screenshot('),
    (r'\bjs\(', 'await js('),
    (r'\bclick\(', 'await click('),
    (r'\btype_text\(', 'await type_text('),
    (r'\bpress_key\(', 'await press_key('),
    (r'\bnew_tab\(', 'await new_tab('),
    (r'\bswitch_tab\(', 'await switch_tab('),
    (r'\bclose_tab\(', 'await close_tab('),
    (r'\blist_tabs\(', 'await list_tabs('),
    (r'\bpage_info\(', 'await page_info('),
    (r'\bget_html\(', 'await get_html('),
    (r'\bget_text\(', 'await get_text('),
    (r'\bget_cookies\(', 'await get_cookies('),
    (r'\bset_cookies\(', 'await set_cookies('),
    (r'\bsave_profile\(', 'await save_profile('),
    (r'\bload_profile\(', 'await load_profile('),
    (r'\biframe_target\(', 'await iframe_target('),
    (r'\bhuman_click\(', 'await human_click('),
    (r'\bhuman_type\(', 'await human_type('),
    (r'\bstealth_mode\(', 'await stealth_mode('),

    # CDP removal (comment out with TODO)
    (r'(\s+)cdp\("([^"]+)"([^)]*)\)', r'\1# cdp("\2"\3  # TODO: Adapt to Playwright'),

    # http_get → js fetch (simple cases)
    (r'http_get\(([^)]+)\)', r'''await js('fetch(" + r"\1" + r").then(r=>r.text())'''),

    # Remove CDP-specific patterns
    (r'#.*cdp.*', '# TODO: CDP code removed - needs Playwright adaptation'),

    # Fix async function definitions in examples
    (r'def test_\w+\((.*?)\):', r'async def test_\1(self):'),
    (r'\bfor\s+(\w+)\s+in\s+(.*?):', r'async for \1 in \2:'),
]

def adapt_file(file_path: Path):
    """Adapt a single file."""
    content = file_path.read_text()
    original = content

    # Apply replacements
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)

    # Add header note if file was modified
    if content != original:
        header = """> **Adapted from browser-harness to camoufox-harness (Playwright API)**
>
> Original browser-harness code used CDP/sync calls. This has been adapted to use Playwright async API.
>
> If you find issues, check `helpers.py` for available functions.

"""
        # Insert after first heading
        first_heading = re.search(r'^#\s+', content, re.MULTILINE)
        if first_heading and "Adapted from browser-harness" not in content:
            pos = first_heading.end()
            content = content[:pos] + "\n" + header + "\n" + content[pos:]

        file_path.write_text(content)
        return True
    return False

def main():
    """Adapt all domain-skills."""
    files_to_adapt = []

    # Find all .md files
    for md_file in DOMAIN_SKILLS.rglob("*.md"):
        # Check if needs adaptation
        content = md_file.read_text()
        if re.search(r'cdp\(|http_get\|goto\(|wait_for_load\(', content):
            files_to_adapt.append(md_file)

    print(f"Found {len(files_to_adapt)} files to adapt")

    adapted = 0
    for md_file in files_to_adapt:
        if adapt_file(md_file):
            adapted += 1
            print(f"✅ Adapted: {md_file}")
        else:
            print(f"⏭️  Skipped: {md_file}")

    print(f"\nAdapted {adapted}/{len(files_to_adapt)} files")

if __name__ == "__main__":
    main()
