#!/usr/bin/env python3
from __future__ import annotations

"""
Extract and run available skill demo scripts in parallel.
Saves output as v4 demo reports in docs/demo-reports/.

Usage:
    export BOHR_ACCESS_KEY="your_access_key"
    python3 tests/run_all_demos.py
"""

import os
import re
import sys
import subprocess
import tempfile
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent.parent
ZH_DIR = BASE_DIR / "zh"
OUTPUT_DIR = BASE_DIR / "docs" / "demo-reports"

ORCHESTRATION_SKILLS = [
    (f"{idx:02d}", path.parent.name)
    for idx, path in enumerate(sorted(ZH_DIR.glob("*/SKILL.md")), start=1)
]

# CLI arguments for scripts that require them
SKILL_ARGS = {
    "scholar-profiler": ["Weinan E", "Peking University"],
    "pre-review": ["https://arxiv.org/pdf/2302.14231"],
    "paper-dissector": ["https://arxiv.org/pdf/2302.14231", "quick"],
    "citation-explorer": ["10.1038/s41586-021-03819-2", "both", "1"],
    "collaborator-finder": ["电催化CO2还原", "需要in-situ表征能力", ""],
    "review-assistant": ["https://arxiv.org/pdf/2302.14231", "NeurIPS"],
    "academic-promo": ["https://arxiv.org/pdf/2302.14231"],
}

SKIP_DEMOS = {
    "bohrium-knowledge-base": "requires local input files and can mutate remote knowledge bases",
}


def extract_main_script(skill_name: str) -> str | None:
    """Extract the main Python script from SKILL.md."""
    skill_file = ZH_DIR / skill_name / "SKILL.md"
    if not skill_file.exists():
        return None

    content = skill_file.read_text(encoding="utf-8")
    blocks = re.findall(r'```python\n(.*?)```', content, re.DOTALL)

    # Strategy 1: Find a single large block with __main__ or main()
    main_block = None
    max_len = 0
    for b in blocks:
        if len(b) > max_len and (
            '__main__' in b or
            'def main(' in b or
            ('CONFIG' in b and len(b) > 2000) or
            ('def step1' in b and len(b) > 2000) or
            (skill_name.replace('-', '_') in b.lower() and len(b) > 2000)
        ):
            main_block = b
            max_len = len(b)

    # Fallback: just take the largest script block
    if not main_block:
        candidates = [b for b in blocks if len(b) > 2000]
        if candidates:
            main_block = max(candidates, key=len)

    # If the single block doesn't compile OR is too small compared to
    # concatenated version, prefer concatenation
    if main_block:
        needs_concat = False
        try:
            compile(main_block, '<test>', 'exec')
        except SyntaxError:
            needs_concat = True

        # Always try concatenation and prefer it if much larger
        concat_script = try_concat_blocks(content, blocks)
        if concat_script:
            if needs_concat:
                main_block = concat_script
            elif len(concat_script) > len(main_block) * 2:
                # Concatenated version is much larger — likely the real script
                main_block = concat_script

    # If the selected block is missing imports, prepend them from an earlier block
    if main_block and 'import ' not in main_block.split('\n')[0]:
        import_block = next((b for b in blocks if b.strip().startswith('import ') or b.strip().startswith('from ')), None)
        if import_block and import_block not in main_block:
            main_block = import_block + "\n\n" + main_block

    return main_block


def try_concat_blocks(content: str, blocks: list) -> str | None:
    """For skills with split code blocks, concatenate them into one script."""
    # Find where "完整编排" section starts
    match = re.search(r'## 完整编排', content)
    if not match:
        return None

    after_section = content[match.start():]
    section_blocks = re.findall(r'```python\n(.*?)```', after_section, re.DOTALL)

    if len(section_blocks) < 2:
        return None

    # Try progressively removing blocks from the end until we find one that
    # both compiles AND has a print/report output (not just a helper function)
    # Skip blocks that call save/persist functions (require configured backends)
    for end_idx in range(len(section_blocks), 1, -1):
        last_block = section_blocks[end_idx - 1]
        # Skip blocks that persist to external services or depend on external state
        if 'save_baseline' in last_block or 'save_to_kb' in last_block:
            continue
        if 'baseline_comparison' in last_block:
            continue
        combined = "\n\n".join(section_blocks[:end_idx])
        try:
            compile(combined, '<test>', 'exec')
            if 'print(' in last_block or 'report' in last_block:
                return combined
        except SyntaxError:
            continue

    # Fallback: just try all blocks
    combined = "\n\n".join(section_blocks)
    try:
        compile(combined, '<test>', 'exec')
        return combined
    except SyntaxError:
        pass
    return None


def fix_multiline_strings(script: str) -> str:
    """Fix common issues with multiline strings extracted from markdown."""
    # Fix unterminated string literals on lines ending with "
    # These are usually f-strings or regular strings that span multiple lines
    # in the original source but got broken by markdown extraction
    lines = script.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this line has an unterminated string
        # Pattern: line ends with opening quote without closing
        stripped = line.rstrip()
        if (stripped.endswith('("') or stripped.endswith("('") or
            stripped.endswith('(f"') or stripped.endswith("(f'") or
            (stripped.count('"') % 2 == 1 and stripped.endswith('"') and
             not stripped.endswith('"""'))):
            # Try to join with next lines until we find the closing
            combined = line
            j = i + 1
            while j < len(lines):
                combined += '\n' + lines[j]
                # Check if string is now terminated
                try:
                    compile(combined + '\npass', '<test>', 'exec')
                    break
                except SyntaxError:
                    j += 1
            fixed_lines.append(combined)
            i = j + 1
        else:
            fixed_lines.append(line)
            i += 1

    return '\n'.join(fixed_lines)


def validate_script(script: str) -> tuple[bool, str]:
    """Check if the script compiles without syntax errors."""
    try:
        compile(script, '<skill_script>', 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"


def run_skill(num: str, skill_name: str) -> tuple[str, str, bool]:
    """Run a single skill demo and return (skill_name, output, success)."""
    script = extract_main_script(skill_name)
    if not script:
        return (skill_name, f"ERROR: Could not extract script from {skill_name}/SKILL.md", False)

    # Validate and attempt fix
    valid, err = validate_script(script)
    if not valid:
        # Try to fix common multiline string issues
        script = fix_multiline_strings(script)
        valid, err = validate_script(script)
        if not valid:
            return (skill_name, f"ERROR: Script has syntax error: {err}", False)

    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script)
        tmp_path = f.name

    try:
        env = os.environ.copy()
        ak = env.get("BOHR_ACCESS_KEY") or env.get("ACCESS_KEY", "")
        env["BOHR_ACCESS_KEY"] = ak
        env["ACCESS_KEY"] = ak

        # Build command with skill-specific arguments
        cmd = [sys.executable, tmp_path]
        if skill_name in SKILL_ARGS:
            cmd.extend([a for a in SKILL_ARGS[skill_name] if a])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout per skill
            env=env,
            cwd=str(BASE_DIR),
        )

        output = result.stdout
        if result.returncode != 0:
            output += f"\n\nSTDERR:\n{result.stderr}"
            return (skill_name, output, False)

        return (skill_name, output, True)

    except subprocess.TimeoutExpired:
        return (skill_name, "ERROR: Script timed out after 300 seconds", False)
    except Exception as e:
        return (skill_name, f"ERROR: {e}", False)
    finally:
        os.unlink(tmp_path)


def main():
    ak = os.environ.get("BOHR_ACCESS_KEY") or os.environ.get("ACCESS_KEY", "")
    if not ak:
        print("ERROR: BOHR_ACCESS_KEY (or ACCESS_KEY) not set")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    demo_skills = [
        (num, skill_name)
        for num, skill_name in ORCHESTRATION_SKILLS
        if skill_name not in SKIP_DEMOS and extract_main_script(skill_name)
    ]
    skipped = len(ORCHESTRATION_SKILLS) - len(demo_skills)
    if not demo_skills:
        print("No runnable demo scripts found.")
        return

    print(f"Running {len(demo_skills)} demo scripts in parallel...")
    if skipped:
        print(f"Skipping {skipped} skills without standalone demo scripts.")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"BOHR_ACCESS_KEY: {ak[:8]}...{ak[-4:]}")
    print("=" * 60)

    # Run all skills in parallel (max 6 concurrent to avoid API rate limits)
    futures = {}
    with ProcessPoolExecutor(max_workers=6) as executor:
        for num, skill_name in demo_skills:
            future = executor.submit(run_skill, num, skill_name)
            futures[future] = (num, skill_name)

        completed = 0
        failed = 0
        for future in as_completed(futures):
            num, skill_name = futures[future]
            completed += 1

            try:
                name, output, success = future.result()
            except Exception as e:
                name = skill_name
                output = f"ERROR: Future failed: {e}"
                success = False

            status = "✅" if success else "❌"
            print(f"  [{completed}/{len(demo_skills)}] {status} {num}-{name}")

            # Save output
            out_file = OUTPUT_DIR / f"{num}-{name}-v4.md"
            out_file.write_text(output, encoding="utf-8")

            if not success:
                failed += 1

    print("=" * 60)
    print(f"Done: {len(demo_skills) - failed} succeeded, {failed} failed, {skipped} skipped")
    if failed:
        print("\nFailed skills:")
        for num, skill_name in demo_skills:
            f = OUTPUT_DIR / f"{num}-{skill_name}-v4.md"
            if f.exists():
                content = f.read_text()[:200]
                if "ERROR" in content or "STDERR" in content:
                    # Show first line of error
                    first_err = [l for l in content.split('\n') if 'ERROR' in l or 'Error' in l or 'STDERR' in l]
                    err_msg = first_err[0][:80] if first_err else "unknown error"
                    print(f"  - {num}-{skill_name}: {err_msg}")


if __name__ == "__main__":
    main()
