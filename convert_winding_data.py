#!/usr/bin/env python3
import argparse
import csv
import json
import random
from pathlib import Path

from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()


def load_settings(input_dir: Path):

    csv_path = input_dir / "setting.csv"
    json_path = input_dir / "setting.csv"

    settings = {}

    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                no = str(row.get("no", "")).strip()
                if not no:
                    continue
                result = str(row.get("result", "")).strip().lower()
                settings[no] = {
                    "angle": row.get("angle"),
                    "distance": row.get("distance"),
                    "speed": row.get("speed"),
                    "result": result,
                }
        return settings

    if json_path.exists():
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)


        if isinstance(data, list):
            for row in data:
                no = str(row.get("no", "")).strip()
                if not no:
                    continue
                result = str(row.get("result", "")).strip().lower()
                settings[no] = {
                    "angle": row.get("angle"),
                    "distance": row.get("distance"),
                    "speed": row.get("speed"),
                    "result": result,
                }
        elif isinstance(data, dict):

            for no, row in data.items():
                no = str(no).strip()
                result = str(row.get("result", "")).strip().lower()
                settings[no] = {
                    "angle": row.get("angle"),
                    "distance": row.get("distance"),
                    "speed": row.get("speed"),
                    "result": result,
                }
        return settings

    raise FileNotFoundError("setting.csv / setting.csv が input ディレクトリ内に見つかりません。")


def result_to_label(result: str) -> int:

    if result.lower() == "ok":
        return 1
    return 0


def find_image_files(folder: Path):

    exts = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".bmp", ".tif", ".tiff"}
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts]
    return sorted(files)


def convert_and_save_image(src_path: Path, dst_path: Path):

    with Image.open(src_path) as img:

        img = img.convert("RGB")
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(dst_path, format="JPEG")


def build_folder_states(input_dir: Path, settings: dict, rng: random.Random):

    folder_states = []

    for no, info in settings.items():
        folder_path = input_dir / no
        if not folder_path.is_dir():

            continue

        images = find_image_files(folder_path)
        if len(images) < 3:

            continue

        rng.shuffle(images)

        state = {
            "folder_no": no,
            "path": folder_path,
            "label": result_to_label(info.get("result", "")),
            "images": images,
            "index": 0,
        }
        folder_states.append(state)

    if not folder_states:
        raise RuntimeError("有効なフォルダ(画像が3枚以上あるフォルダ)が見つかりませんでした。")


    rng.shuffle(folder_states)
    return folder_states


def get_next_triplet_from_folder(state, rng: random.Random):

    images = state["images"]
    idx = state["index"]
    n = len(images)

    if n < 3:
        raise RuntimeError(f"Folder {state['folder_no']} has less than 3 images.")


    if idx + 3 <= n:
        triplet = images[idx:idx + 3]
        state["index"] = idx + 3
        return triplet


    rng.shuffle(images)
    state["images"] = images
    state["index"] = 3
    return images[0:3]


def main():
    parser = argparse.ArgumentParser(
        description="巻線工程データを学習データ形式に変換するスクリプト"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="入力となる winding_data ディレクトリのパス (例: ./data/raw_winding_data)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="出力先ディレクトリのパス (例: ./data/winding_data)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        required=True,
        help="作成するサンプル数 (0以上の整数)。サンプル1つにつき画像3枚を使用。",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="乱数シード (0以上の整数)",
    )

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    images_out_dir = output_dir / "images"
    sample_count = max(0, args.sample)
    seed = max(0, args.seed)

    rng = random.Random(seed)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"input ディレクトリが存在しません: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    images_out_dir.mkdir(parents=True, exist_ok=True)


    settings = load_settings(input_dir)


    folder_states = build_folder_states(input_dir, settings, rng)


    labels_path = output_dir / "labels.csv"
    reference_path = output_dir / "reference.csv"

    with labels_path.open("w", encoding="utf-8", newline="") as lf, \
            reference_path.open("w", encoding="utf-8", newline="") as rf:

        labels_writer = csv.writer(lf)
        ref_writer = csv.writer(rf)

        labels_writer.writerow(["sample_id", "label"])
        ref_writer.writerow(["name", "origin"])

        if sample_count == 0:

            return

        num_folders = len(folder_states)

        sample_id = 1

        for i in range(sample_count):

            state = folder_states[i % num_folders]

            triplet = get_next_triplet_from_folder(state, rng)


            suffixes = ["a", "b", "c"]
            label = state["label"]

            for idx_img, src_path in enumerate(triplet):
                suffix = suffixes[idx_img]
                new_name = f"{sample_id}_{suffix}.JPG"
                dst_path = images_out_dir / new_name


                convert_and_save_image(src_path, dst_path)


                ref_writer.writerow([new_name, src_path.name])


            labels_writer.writerow([sample_id, label])

            sample_id += 1


if __name__ == "__main__":
    main()
