from __future__ import annotations

import argparse
import random
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml


IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


@dataclass(frozen=True)
class PrepStats:
    images_copied: int
    labels_written: int
    images_missing_label: int
    images_with_no_pothole_after_filter: int
    boxes_kept: int
    boxes_dropped: int


def load_names(data_yaml: Path) -> list[str]:
    obj = yaml.safe_load(data_yaml.read_text(encoding="utf-8", errors="ignore"))
    names = obj.get("names")
    if not isinstance(names, list) or not all(isinstance(x, str) for x in names):
        raise ValueError(f"Invalid 'names' in {data_yaml}")
    return names


def infer_pothole_class_ids(names: list[str]) -> set[int]:
    # Keep any class whose name suggests pothole (and "bache" is often used for pothole in Hindi).
    keep: set[int] = set()
    for i, n in enumerate(names):
        s = n.strip().lower()
        if "pothole" in s or s in {"bache"}:
            keep.add(i)
    return keep


def list_images(images_dir: Path) -> list[Path]:
    out: list[Path] = []
    for ext in IMG_EXTS:
        out.extend(images_dir.glob(f"*{ext}"))
    return sorted(out)


def filter_label_to_pothole(
    label_path: Path,
    keep_class_ids: set[int],
    *,
    out_class_id: int = 0,
) -> tuple[list[str], int, int]:
    """
    Returns (new_lines, kept_boxes, dropped_boxes).
    new_lines are YOLO lines with class remapped to out_class_id.
    """
    if not label_path.exists():
        return ([], 0, 0)

    raw = label_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    kept: list[str] = []
    kept_n = dropped_n = 0

    for line in raw:
        parts = line.strip().split()
        if len(parts) != 5:
            continue
        try:
            cls = int(float(parts[0]))
            x, y, w, h = map(float, parts[1:])
        except Exception:
            continue

        if cls in keep_class_ids:
            kept.append(f"{out_class_id} {x:.8f} {y:.8f} {w:.8f} {h:.8f}")
            kept_n += 1
        else:
            dropped_n += 1

    return kept, kept_n, dropped_n


def copy_and_prepare_split(
    *,
    src_images: Path,
    src_labels: Path,
    dst_images: Path,
    dst_labels: Path,
    keep_class_ids: set[int],
) -> PrepStats:
    dst_images.mkdir(parents=True, exist_ok=True)
    dst_labels.mkdir(parents=True, exist_ok=True)

    images = list_images(src_images)
    images_copied = labels_written = missing_lbl = empty_after = 0
    boxes_kept = boxes_dropped = 0

    for img in images:
        lbl = src_labels / f"{img.stem}.txt"
        new_lines, k, d = filter_label_to_pothole(lbl, keep_class_ids)
        boxes_kept += k
        boxes_dropped += d

        # Copy image
        shutil.copy2(img, dst_images / img.name)
        images_copied += 1

        # Write label (can be empty -> treated as background)
        if not lbl.exists():
            missing_lbl += 1
            (dst_labels / f"{img.stem}.txt").write_text("", encoding="utf-8")
        else:
            if not new_lines:
                empty_after += 1
            (dst_labels / f"{img.stem}.txt").write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
        labels_written += 1

    return PrepStats(
        images_copied=images_copied,
        labels_written=labels_written,
        images_missing_label=missing_lbl,
        images_with_no_pothole_after_filter=empty_after,
        boxes_kept=boxes_kept,
        boxes_dropped=boxes_dropped,
    )


def move_subset_for_val(
    *,
    train_images: Path,
    train_labels: Path,
    val_images: Path,
    val_labels: Path,
    val_fraction: float,
    seed: int,
) -> tuple[int, int]:
    rng = random.Random(seed)
    imgs = list_images(train_images)
    rng.shuffle(imgs)
    n_val = max(1, int(round(len(imgs) * val_fraction)))

    val_images.mkdir(parents=True, exist_ok=True)
    val_labels.mkdir(parents=True, exist_ok=True)

    moved = 0
    for img in imgs[:n_val]:
        lbl = train_labels / f"{img.stem}.txt"
        shutil.move(str(img), str(val_images / img.name))
        if lbl.exists():
            shutil.move(str(lbl), str(val_labels / lbl.name))
        else:
            # should not happen; create empty label
            (val_labels / f"{img.stem}.txt").write_text("", encoding="utf-8")
        moved += 1
    return moved, len(imgs) - moved


def write_dataset_yaml(out_yaml: Path, dataset_root: Path) -> None:
    # Use forward slashes; Ultralytics accepts these on Windows.
    root = dataset_root.resolve().as_posix()
    obj = {
        "path": root,
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": 1,
        "names": ["pothole"],
    }
    out_yaml.write_text(yaml.safe_dump(obj, sort_keys=False), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare Roboflow multi-class dataset into single-class pothole-only YOLO dataset.")
    ap.add_argument(
        "--src",
        type=Path,
        default=Path(r"C:\Users\AMAN SINGH\pothole_dataset\New pothole detection.v1i.yolov8"),
        help="Roboflow YOLOv8 export folder containing train/ valid/ test/ and data.yaml",
    )
    ap.add_argument(
        "--dst",
        type=Path,
        default=Path(r"C:\Users\AMAN SINGH\pothole_dataset\roboflow_pothole_clean"),
        help="Output cleaned dataset folder (will be created).",
    )
    ap.add_argument("--val-fraction", type=float, default=0.1, help="Create val split by moving this fraction from train.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    src = args.src
    dst = args.dst

    names = load_names(src / "data.yaml")
    keep_ids = infer_pothole_class_ids(names)
    if not keep_ids:
        raise ValueError("Could not infer pothole classes from names; please edit infer_pothole_class_ids().")

    print("Keeping Roboflow class IDs as pothole:", sorted(keep_ids), "from names:", [names[i] for i in sorted(keep_ids)])

    # Clean + copy train and test. Roboflow 'valid' is missing labels in your export, so we ignore it.
    train_stats = copy_and_prepare_split(
        src_images=src / "train" / "images",
        src_labels=src / "train" / "labels",
        dst_images=dst / "train" / "images",
        dst_labels=dst / "train" / "labels",
        keep_class_ids=keep_ids,
    )
    test_stats = copy_and_prepare_split(
        src_images=src / "test" / "images",
        src_labels=src / "test" / "labels",
        dst_images=dst / "test" / "images",
        dst_labels=dst / "test" / "labels",
        keep_class_ids=keep_ids,
    )

    moved, remaining = move_subset_for_val(
        train_images=dst / "train" / "images",
        train_labels=dst / "train" / "labels",
        val_images=dst / "val" / "images",
        val_labels=dst / "val" / "labels",
        val_fraction=args.val_fraction,
        seed=args.seed,
    )

    write_dataset_yaml(dst / "data_pothole.yaml", dst)

    print("\nDone.")
    print(f"- Output dataset: {dst}")
    print(f"- Dataset YAML:   {dst / 'data_pothole.yaml'}")
    print("\nTrain copy stats:", train_stats)
    print("Test copy stats: ", test_stats)
    print(f"Val split: moved {moved} images to val, remaining in train {remaining}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

