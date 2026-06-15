#!/usr/bin/env /usr/bin/python3
"""批量将图片上下对半裁开，保存为 *_上 和 *_下 两张图。"""
from pathlib import Path
import argparse
from PIL import Image


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def iter_images(input_path: Path):
    """遍历输入路径中的图片文件。"""
    if input_path.is_file():
        if input_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield input_path
        return

    for path in sorted(input_path.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def split_image(path: Path, output_dir: Path, overwrite: bool):
    """将单张图片上下对半裁开并保存。"""
    top_path = output_dir / f"{path.stem}_上{path.suffix}"
    bottom_path = output_dir / f"{path.stem}_下{path.suffix}"

    for target_path in (top_path, bottom_path):
        if target_path.exists() and not overwrite:
            raise FileExistsError(f"输出文件已存在：{target_path}，如需覆盖请加 --overwrite")

    with Image.open(path) as img:
        width, height = img.size
        half_height = height // 2

        top = img.crop((0, 0, width, half_height))
        top.save(top_path)

        bottom = img.crop((0, half_height, width, height))
        bottom.save(bottom_path)

    return top_path, bottom_path, width, height


def main():
    parser = argparse.ArgumentParser(description="批量将图片上下对半裁开，保存为 *_上 和 *_下 两张图")
    parser.add_argument("input", help="图片文件或图片文件夹路径")
    parser.add_argument("-o", "--output-dir", default="split_output", help="输出文件夹，默认 split_output")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已存在的输出文件")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = list(iter_images(input_path))
    if not image_paths:
        raise SystemExit("没有找到可处理的图片文件")

    for path in image_paths:
        top_path, bottom_path, w, h = split_image(path, output_dir, args.overwrite)
        print(f"{path.name} ({w}×{h}) → {top_path.name}, {bottom_path.name}")


if __name__ == "__main__":
    main()
