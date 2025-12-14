import os
from pathlib import Path
from PIL import Image


def format_mb(num_bytes: int) -> str:
    return f"{num_bytes / (1024 * 1024):.2f}MB"


# Tuned for typical full-width backgrounds + card images on a Bootstrap site.
# We keep filenames and extensions the same (overwrite in-place) but back up originals.
DEFAULT_MAX_EDGE = 1920
MAX_EDGE_OVERRIDES = {
    # Very large hero backgrounds
    "background1.jpg": 1920,
    "background2.jpg": 1920,
    "background3.jpg": 1920,
    "background4.jpg": 1920,

    # Section/slider images: still large but don't need 5k+ px
    "about.jpg": 1600,
    "about2.jpg": 1600,
    "about3.jpg": 1600,
    "about4.jpg": 1600,

    # Course cards: displayed small; keep some sharpness for retina
    "course-1.jpg": 1400,
    "course-2.jpg": 1400,
    "course-3.jpg": 1400,
    "course9.jpg": 1400,
    "Ramzan.jpg": 1400,
    "Aqedah.jpg": 1400,

    # Others
    "Taruf.jpg": 1600,
    "Usool-Hadees.jpg": 1400,
    "Doraarab.jpg": 1400,
}

# JPEG output settings
JPEG_QUALITY = 78


def optimize_jpeg(src_path: Path, backup_root: Path) -> tuple[int, int]:
    """Return (before_bytes, after_bytes)."""
    before_bytes = src_path.stat().st_size

    rel = src_path.relative_to(src_path.parents[2]) if len(src_path.parents) >= 2 else src_path.name
    backup_path = backup_root / rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        backup_path.write_bytes(src_path.read_bytes())

    with Image.open(src_path) as im:
        im = im.convert("RGB")
        max_edge = MAX_EDGE_OVERRIDES.get(src_path.name, DEFAULT_MAX_EDGE)
        w, h = im.size
        scale = min(1.0, max_edge / max(w, h))
        if scale < 1.0:
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
            im = im.resize(new_size, Image.Resampling.LANCZOS)

        tmp_path = src_path.with_suffix(src_path.suffix + ".tmp")
        im.save(
            tmp_path,
            format="JPEG",
            quality=JPEG_QUALITY,
            optimize=True,
            progressive=True,
        )

    os.replace(tmp_path, src_path)
    after_bytes = src_path.stat().st_size
    return before_bytes, after_bytes


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    img_dir = repo_root / "assets" / "img"
    if not img_dir.exists():
        print(f"ERROR: image directory not found: {img_dir}")
        return 2

    backup_root = repo_root / "assets" / "img" / "_originals"

    jpgs = sorted([p for p in img_dir.rglob("*.jpg") if "_originals" not in p.parts])
    if not jpgs:
        print("No .jpg images found to optimize.")
        return 0

    total_before = 0
    total_after = 0
    changed = 0

    print(f"Optimizing {len(jpgs)} JPG(s) under {img_dir}...")

    for p in jpgs:
        try:
            before, after = optimize_jpeg(p, backup_root)
        except Exception as e:
            print(f"SKIP {p.relative_to(repo_root)}: {e}")
            continue

        total_before += before
        total_after += after
        if after != before:
            changed += 1
        print(f"OK   {p.relative_to(repo_root)}  {format_mb(before)} -> {format_mb(after)}")

    savings = total_before - total_after
    pct = (savings / total_before * 100) if total_before else 0
    print("\nSummary")
    print(f"- Changed: {changed}/{len(jpgs)}")
    print(f"- Total:   {format_mb(total_before)} -> {format_mb(total_after)}")
    print(f"- Saved:   {format_mb(savings)} ({pct:.1f}%)")
    print(f"- Backup:  {backup_root.relative_to(repo_root)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
