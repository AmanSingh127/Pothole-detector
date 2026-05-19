from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path


IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


@dataclass(frozen=True)
class SplitStats:
    total_images: int
    positives: int
    negatives: int
    sampled_negatives: int


def _is_positive_label(label_path: Path) -> bool:
    # In this dataset, background images have empty .txt files (present but blank).
    try:
        return bool(label_path.read_text(encoding="utf-8", errors="ignore").strip())
    except FileNotFoundError:
        return False


def _collect_images(images_dir: Path) -> list[Path]:
    images: list[Path] = []
    for ext in IMG_EXTS:
        images.extend(images_dir.glob(f"*{ext}"))
    return sorted(images)


def _to_ultralytics_path(p: Path) -> str:
    # Ultralytics is fine with forward slashes on Windows.
    return p.resolve().as_posix()


def build_balanced_list(
    images_dir: Path,
    labels_dir: Path,
    *,
    neg_per_pos: float,
    seed: int,
) -> tuple[list[Path], SplitStats]:
    rng = random.Random(seed)

    images = _collect_images(images_dir)
    positives: list[Path] = []
    negatives: list[Path] = []

    for img in images:
        lbl = labels_dir / f"{img.stem}.txt"
        if _is_positive_label(lbl):
            positives.append(img)
        else:
            negatives.append(img)

    # Keep all positives, sample a controlled number of negatives.
    max_negs = int(round(len(positives) * neg_per_pos))
    sampled_negs = negatives if max_negs >= len(negatives) else rng.sample(negatives, k=max_negs)

    combined = positives + sampled_negs
    rng.shuffle(combined)

    stats = SplitStats(
        total_images=len(images),
        positives=len(positives),
        negatives=len(negatives),
        sampled_negatives=len(sampled_negs),
    )
    return combined, stats


def write_list(file_path: Path, image_paths: list[Path]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("\n".join(_to_ultralytics_path(p) for p in image_paths) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Create balanced Ultralytics/YOLO image lists by downsampling background-only images.\n"
            "Positives = images whose corresponding label .txt is non-empty."
        )
    )
    ap.add_argument(
        "--base",
        type=Path,
        default=Path(r"C:\Users\AMAN SINGH\pothole_dataset\RDD2022_india\india"),
        help="Base directory containing train/ and val/ folders.",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path(r"C:\Users\AMAN SINGH\pothole_dataset\balanced_splits"),
        help="Output directory for train.txt and val.txt.",
    )
    ap.add_argument(
        "--neg-per-pos",
        type=float,
        default=2.0,
        help="How many negative (no-pothole) images to keep per positive image.",
    )
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    base: Path = args.base
    out_dir: Path = args.out_dir

    train_list, train_stats = build_balanced_list(
        base / "train" / "images",
        base / "train" / "labels",
        neg_per_pos=args.neg_per_pos,
        seed=args.seed,
    )
    val_list, val_stats = build_balanced_list(
        base / "val" / "images",
        base / "val" / "labels",
        neg_per_pos=args.neg_per_pos,
        seed=args.seed + 1,
    )

    write_list(out_dir / "train.txt", train_list)
    write_list(out_dir / "val.txt", val_list)

    print("Wrote balanced lists:")
    print(f"- train: {out_dir / 'train.txt'}")
    print(f"  total={train_stats.total_images} pos={train_stats.positives} "
          f"neg={train_stats.negatives} sampled_neg={train_stats.sampled_negatives} "
          f"final={len(train_list)} (neg_per_pos={args.neg_per_pos})")
    print(f"- val:   {out_dir / 'val.txt'}")
    print(f"  total={val_stats.total_images} pos={val_stats.positives} "
          f"neg={val_stats.negatives} sampled_neg={val_stats.sampled_negatives} "
          f"final={len(val_list)} (neg_per_pos={args.neg_per_pos})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

