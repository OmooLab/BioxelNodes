"""
Create a zip archive of the src/bioxelnodes package with a top-level folder
named `bioxelnodes/`. Excludes specified temporary/cache files and folders.
Does not modify any files in the project.

Usage:
    python build_package.py <platform_name> [output_zip_path]

Example:
    python build_package.py windows-x64
"""
from pathlib import Path
import sys
import zipfile
import fnmatch
from datetime import datetime

platforms = {
    "windows-x64": "windows-x64",
    "linux-x64": "linux-x64",
    "macos-arm64": "macos-arm64",
    "macos-x64": "macos-x64",
}

# patterns to exclude (filename matching)
EXCLUDE_FILENAME_PATTERNS = [
    "*.blend1",
    "blendcache_*",
    "*.cats.txt~",
    "*.pyc",
    "*.pyo",
    "*$py.class",
]

# directory names to exclude entirely
EXCLUDE_DIR_NAMES = {
    "__pycache__",
}

def should_exclude(path: Path) -> bool:
    name = path.name
    # exclude directories by name anywhere in the path
    if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
        return True
    # only apply filename patterns to files
    if path.is_file():
        for pat in EXCLUDE_FILENAME_PATTERNS:
            if fnmatch.fnmatch(name, pat):
                return True
    return False

def build_package(platform_name: str, out_zip: Path):
    src_root = Path("src") / "bioxelnodes"
    if not src_root.exists():
        raise SystemExit(f"Source folder not found: {src_root.resolve()}")

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in src_root.rglob("*"):
            if p.is_dir():
                continue
            if should_exclude(p):
                continue
            # arcname should place files under top-level 'bioxelnodes/...'
            rel = p.relative_to(src_root)
            arcname = Path("bioxelnodes") / rel
            zf.write(p, arcname.as_posix())
            total += 1
    print(f"Packaged {total} files into {out_zip}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python build_package.py <platform_name> [output_zip_path]")
        print("Available platforms:", ", ".join(platforms.keys()))
        sys.exit(1)

    platform_key = sys.argv[1]
    if platform_key not in platforms:
        print("Unknown platform:", platform_key)
        print("Available platforms:", ", ".join(platforms.keys()))
        sys.exit(1)

    tag = platforms[platform_key]
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    default_name = f"bioxelnodes-{tag}-{timestamp}.zip"
    out_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path(default_name)

    build_package(platform_key, out_path)

if __name__ == "__main__":
    main()