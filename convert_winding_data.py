#!/usr/bin/env python3
import argparse
import csv
import json
import random
from pathlib import Path
from typing import Dict, List

from PIL import Image, UnidentifiedImageError
import pillow_heif

pillow_heif.register_heif_opener()


def load_settings(input_dir: Path) -> Dict[str, dict]:

    csv_path = input_dir / "setting.csv"
    json_path = input_dir / "setting.json"

    settings: Dict[str, dict] = {}

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

    raise FileNotFoundError("setting.csv / setting.json が input ディレクトリ内に見つかりません。")



def find_image_files(folder: Path) -> List[Path]:

    exts = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".bmp", ".tif", ".tiff"}
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts]
    return sorted(files)


def convert_and_save_image(src_path: Path, dst_path: Path):

    try:
        with Image.open(src_path) as img:
            img = img.convert("RGB")
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(dst_path, format="JPEG")
    except UnidentifiedImageError as e:
        raise RuntimeError(f"画像を読み込めませんでした: {src_path}") from e


def build_folder_states(
    input_dir: Path,
    settings: Dict[str, dict],
    label_name_to_id: Dict[str, int],
    rng: random.Random,
):

    folder_states = []

    for no, info in settings.items():
        folder_path = input_dir / no
        if not folder_path.is_dir():

            continue

        images = find_image_files(folder_path)
        if len(images) < 3:

            continue

        rng.shuffle(images)

        result_name = str(info.get("result", "")).lower()
        if result_name not in label_name_to_id:

            continue

        state = {
            "folder_no": no,
            "path": folder_path,
            "label_name": result_name,
            "label_id": label_name_to_id[result_name],
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


def choose_label_name(label_names: List[str], probs: List[float], rng: random.Random) -> str:

    r = rng.random()
    cumulative = 0.0
    for name, p in zip(label_names, probs):
        cumulative += p
        if r <= cumulative:
            return name
    # 丸め誤差対策
    return label_names[-1]


def parse_data_rate(arg_value: str, num_labels: int) -> List[float]:

    parts = [p.strip() for p in arg_value.split(",") if p.strip()]
    if len(parts) != num_labels:
        raise ValueError(
            f"--data_rate の要素数({len(parts)})がラベル数({num_labels})と一致しません。"
        )

    values = []
    for p in parts:
        try:
            v = float(p)
        except ValueError:
            raise ValueError(f"--data_rate の値が数値ではありません: {p}")
        if v < 0:
            raise ValueError("--data_rate の値は 0 以上である必要があります。")
        values.append(v)

    total = sum(values)
    if total <= 0:
        raise ValueError("--data_rate の合計は 0 より大きい必要があります。")


    return [v / total for v in values]


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
    parser.add_argument(
        "--data_rate",
        type=str,
        default=None,
        help=(
            "ラベルごとのデータ比率をカンマ区切りで指定 (例: '0.8,0.2' や '0.3,0.3,0.4')。"
            "ラベルの順番は setting 内の result のユニーク値をソートした順に対応します。"
        ),
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


    label_names = sorted({info["result"] for info in settings.values() if info.get("result")})
    if not label_names:
        raise RuntimeError("setting から result が取得できませんでした。")

    label_name_to_id = {name: idx for idx, name in enumerate(label_names)}

    if args.data_rate is not None:
        label_probs = parse_data_rate(args.data_rate, len(label_names))
    else:

        label_probs = [1.0 / len(label_names)] * len(label_names)

    print("Detected labels (order for data_rate): " + ", ".join(label_names))
    print("Using data_rate (normalized): " + ", ".join(f"{p:.3f}" for p in label_probs))

    folder_states = build_folder_states(input_dir, settings, label_name_to_id, rng)

    label_to_folders: Dict[str, List[dict]] = {name: [] for name in label_names}
    for st in folder_states:
        label_to_folders[st["label_name"]].append(st)

    for name in label_names:
        if not label_to_folders[name]:
            raise RuntimeError(
                f"ラベル '{name}' に対応する有効なフォルダがありません。setting とフォルダ構成を確認してください。"
            )


    label_to_folder_index: Dict[str, int] = {name: 0 for name in label_names}

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

        sample_id = 1
        suffixes = ["a", "b", "c"]

        for _ in range(sample_count):

            label_name = choose_label_name(label_names, label_probs, rng)
            label_id = label_name_to_id[label_name]


            folders_for_label = label_to_folders[label_name]
            idx = label_to_folder_index[label_name]
            folder_state = folders_for_label[idx % len(folders_for_label)]
            label_to_folder_index[label_name] = (idx + 1) % len(folders_for_label)

            triplet = get_next_triplet_from_folder(folder_state, rng)

            for idx_img, src_path in enumerate(triplet):
                suffix = suffixes[idx_img]
                new_name = f"{sample_id}_{suffix}.JPG"
                dst_path = images_out_dir / new_name

                convert_and_save_image(src_path, dst_path)
                ref_writer.writerow([new_name, src_path.name])

            labels_writer.writerow([sample_id, label_id])

            sample_id += 1


if __name__ == "__main__":
    main()