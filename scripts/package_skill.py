#!/usr/bin/env python3
"""Package the Palace skill into a distributable .skill (ZIP) file.

Usage:
    python3 scripts/package_skill.py [output-directory]

Examples:
    python3 scripts/package_skill.py           # outputs to ./dist/
    python3 scripts/package_skill.py ./release  # outputs to ./release/
"""

import re
import sys
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "palace"
EXCLUDE = {".DS_Store", "__pycache__", "*.pyc", "node_modules", "evals"}


def validate(skill_path: Path) -> tuple[bool, str]:
    """Validate SKILL.md frontmatter."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    # Simple key-value parse (avoid yaml dependency)
    fm = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"')

    allowed = {
        "name", "description", "license",
        "allowed-tools", "metadata", "compatibility",
    }
    unexpected = set(fm.keys()) - allowed
    if unexpected:
        return False, f"Unexpected keys: {', '.join(sorted(unexpected))}"

    if "name" not in fm:
        return False, "Missing 'name'"
    if "description" not in fm:
        return False, "Missing 'description'"

    name = fm["name"]
    if not re.match(r"^[a-z0-9-]+$", name):
        return False, f"Name '{name}' must be kebab-case"
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return False, f"Name '{name}' has invalid hyphens"
    if len(name) > 64:
        return False, f"Name too long ({len(name)} > 64)"

    desc = fm["description"]
    if "<" in desc or ">" in desc:
        return False, "Description cannot contain angle brackets"
    if len(desc) > 1024:
        return False, f"Description too long ({len(desc)} > 1024)"

    return True, "Valid"


def should_exclude(name: str) -> bool:
    return name in EXCLUDE or name.endswith(".pyc")


def package(skill_path: Path, output_dir: Path) -> Path | None:
    valid, msg = validate(skill_path)
    if not valid:
        print(f"  Validation failed: {msg}")
        return None
    print("  Validation passed")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{skill_path.name}.skill"

    with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(skill_path.rglob("*")):
            if not file_path.is_file():
                continue
            if any(should_exclude(p) for p in file_path.relative_to(skill_path).parts):
                continue
            arcname = file_path.relative_to(skill_path.parent)
            zf.write(file_path, arcname)
            print(f"  + {arcname}")

    print(f"\n  Packaged: {out_file} ({out_file.stat().st_size} bytes)")
    return out_file


def main():
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dist")
    print("Packaging Palace skill...")
    print(f"  Source:  {SKILL_DIR}")
    print(f"  Output:  {output_dir.resolve()}\n")

    result = package(SKILL_DIR, output_dir)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
