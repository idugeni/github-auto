#!/usr/bin/env python3
"""
Auto-update documentation based on current codebase state.

Run: python scripts/update_docs.py
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def count_lines(path: Path) -> int:
    """Count lines in a file."""
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except Exception:
        return 0


def scan_python_modules() -> dict[str, dict]:
    """Scan Python source modules."""
    modules = {}
    src = ROOT / "src"
    for module_dir in sorted(src.iterdir()):
        if module_dir.is_dir() and not module_dir.name.startswith("_"):
            files = list(module_dir.glob("*.py"))
            files = [f for f in files if f.name != "__init__.py"]
            total_lines = sum(count_lines(f) for f in files)
            modules[module_dir.name] = {
                "files": len(files),
                "total_lines": total_lines,
                "avg_lines": total_lines // max(len(files), 1),
                "max_file": max(files, key=count_lines).name if files else None,
                "max_lines": max((count_lines(f) for f in files), default=0),
            }
    return modules


def scan_frontend_features() -> dict[str, dict]:
    """Scan frontend feature pages."""
    features = {}
    features_dir = ROOT / "frontend" / "src" / "features"
    if features_dir.exists():
        for feature_dir in sorted(features_dir.iterdir()):
            if feature_dir.is_dir():
                page = feature_dir / "page.tsx"
                if page.exists():
                    features[feature_dir.name] = {
                        "lines": count_lines(page),
                    }
    return features


def scan_components() -> dict[str, dict]:
    """Scan UI components."""
    components = {}
    ui_dir = ROOT / "frontend" / "src" / "components" / "ui"
    if ui_dir.exists():
        for f in sorted(ui_dir.glob("*.tsx")):
            components[f.stem] = {"lines": count_lines(f)}
    return components


def scan_all_files() -> dict[str, int]:
    """Scan all source files and count LOC."""
    counts = {}
    extensions = ("*.py", "*.tsx", "*.ts", "*.rs", "*.css")
    for ext in extensions:
        for f in ROOT.rglob(ext):
            if "node_modules" in f.parts or "target" in f.parts or "dist" in f.parts:
                continue
            rel = f.relative_to(ROOT)
            counts[str(rel)] = count_lines(f)
    return counts


def generate_module_table(modules: dict) -> str:
    """Generate Python module table."""
    lines = ["| Module | Files | Total LOC | Avg LOC | Max File | Max LOC |"]
    lines.append("|--------|-------|-----------|---------|----------|---------|")
    for name, info in modules.items():
        lines.append(
            f"| `{name}` | {info['files']} | {info['total_lines']} | "
            f"{info['avg_lines']} | `{info['max_file']}` | {info['max_lines']} |"
        )
    return "\n".join(lines)


def generate_feature_table(features: dict) -> str:
    """Generate frontend feature table."""
    lines = ["| Feature | LOC |"]
    lines.append("|---------|-----|")
    for name, info in features.items():
        lines.append(f"| `{name}` | {info['lines']} |")
    return "\n".join(lines)


def update_section(content: str, marker: str, new_section: str) -> str:
    """Replace or append a section in markdown."""
    if marker in content:
        start = content.index(marker)
        next_heading = content.find("\n## ", start + len(marker))
        if next_heading == -1:
            return content[:start] + new_section.strip()
        else:
            return content[:start] + new_section.strip() + content[next_heading:]
    else:
        return content.rstrip() + "\n" + new_section


def update_claude_md(modules: dict, features: dict) -> None:
    """Update CLAUDE.md with current codebase stats."""
    path = ROOT / "CLAUDE.md"
    content = path.read_text(encoding="utf-8")

    total_python_lines = sum(m["total_lines"] for m in modules.values())
    total_python_files = sum(m["files"] for m in modules.values())
    total_frontend_lines = sum(f["lines"] for f in features.values())

    stats_section = f"""
## Codebase Stats (Auto-generated)

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

| Category | Files | Total LOC |
|----------|-------|-----------|
| Python backend | {total_python_files} | {total_python_lines} |
| Frontend pages | {len(features)} | {total_frontend_lines} |

### Python Modules

{generate_module_table(modules)}

### Frontend Features

{generate_feature_table(features)}
"""

    content = update_section(content, "## Codebase Stats (Auto-generated)", stats_section)
    path.write_text(content, encoding="utf-8")
    print("  Updated CLAUDE.md")


def update_agents_md(modules: dict, features: dict) -> None:
    """Update AGENTS.md with current codebase stats."""
    path = ROOT / "AGENTS.md"
    content = path.read_text(encoding="utf-8")

    total_python_lines = sum(m["total_lines"] for m in modules.values())
    largest_module = max(modules, key=lambda k: modules[k]["total_lines"]) if modules else "none"
    largest_lines = max((m["total_lines"] for m in modules.values()), default=0)
    largest_feature = max(features, key=lambda k: features[k]["lines"]) if features else "none"
    largest_feature_lines = max((f["lines"] for f in features.values()), default=0)

    stats_section = f"""
## Current Codebase Stats (Auto-generated)

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

- **Python LOC:** {total_python_lines}
- **Modules:** {len(modules)}
- **Frontend features:** {len(features)}
- **Largest Python module:** `{largest_module}` ({largest_lines} LOC)
- **Largest frontend page:** `{largest_feature}` ({largest_feature_lines} LOC)

### Module Health

| Module | Status | LOC |
|--------|--------|-----|
"""
    for name, info in modules.items():
        status = "[OK]" if info["max_lines"] <= 300 else "[WARN]" if info["max_lines"] <= 400 else "[OVER]"
        stats_section += f"| `{name}` | {status} | {info['total_lines']} |\n"

    content = update_section(content, "## Current Codebase Stats (Auto-generated)", stats_section)
    path.write_text(content, encoding="utf-8")
    print("  Updated AGENTS.md")


def update_readme_stats(modules: dict, features: dict) -> None:
    """Update README.md stats section."""
    path = ROOT / "README.md"
    content = path.read_text(encoding="utf-8")

    total_python = sum(m["total_lines"] for m in modules.values())
    total_frontend = sum(f["lines"] for f in features.values())
    total_files = sum(m["files"] for m in modules.values()) + len(features)

    stats_section = f"""
## Codebase Stats

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

| Category | Files | Total LOC |
|----------|-------|-----------|
| Python backend | {sum(m['files'] for m in modules.values())} | {total_python} |
| Frontend features | {len(features)} | {total_frontend} |
| **Total** | **{total_files}** | **{total_python + total_frontend}** |
"""

    content = update_section(content, "## Codebase Stats", stats_section)
    path.write_text(content, encoding="utf-8")
    print("  Updated README.md")


def update_changelog_stats(modules: dict, features: dict) -> None:
    """Update CHANGELOG.md with current stats."""
    path = ROOT / "CHANGELOG.md"
    if not path.exists():
        return

    content = path.read_text(encoding="utf-8")

    total_python = sum(m["total_lines"] for m in modules.values())
    total_frontend = sum(f["lines"] for f in features.values())

    # Update the Unreleased section with current stats
    if "### Current Stats" not in content:
        stats_section = f"""
### Current Stats

- **Python LOC:** {total_python}
- **Frontend LOC:** {total_frontend}
- **Modules:** {len(modules)}
- **Features:** {len(features)}
"""
        content = update_section(content, "## [Unreleased]", stats_section)
        path.write_text(content, encoding="utf-8")
        print("  Updated CHANGELOG.md")


def main():
    print("Scanning codebase...")
    modules = scan_python_modules()
    features = scan_frontend_features()
    components = scan_components()

    print(f"  {len(modules)} Python modules")
    print(f"  {len(features)} frontend features")
    print(f"  {len(components)} UI components")

    print("\nUpdating documentation...")
    update_claude_md(modules, features)
    update_agents_md(modules, features)
    update_readme_stats(modules, features)
    update_changelog_stats(modules, features)

    print("\nDone!")


if __name__ == "__main__":
    main()
