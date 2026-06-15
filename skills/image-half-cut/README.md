# Image Half Cut / 上下对半裁图

Batch split images into top and bottom halves. Each image is split at the exact vertical midpoint and saved as two separate files with `_上` (upper) and `_下` (lower) suffixes.

## Requirements

- Python 3.7+
- [Pillow](https://python-pillow.org/) (`pip install Pillow`)

## Usage

```bash
# Process a single image
python3 split_images_half.py image.png -o output/

# Process all images in a folder
python3 split_images_half.py /path/to/images/ -o output/

# Overwrite existing output files
python3 split_images_half.py /path/to/images/ -o output/ --overwrite
```

## Output

For each input image, two files are created:

- `original_上.png` — top half
- `original_下.png` — bottom half

Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tif`, `.tiff`

## How it works

Uses Pillow's `Image.crop()` with absolute pixel coordinates. Each image is read individually, so images of different sizes in the same folder are handled correctly:

- Top half: `crop((0, 0, width, height // 2))`
- Bottom half: `crop((0, height // 2, width, height))`

## Example

```
$ python3 split_images_half.py ./photos -o ./split

maxi dress.png (1024×1536) → maxi dress_上.png, maxi dress_下.png
pants.png (1024×1536) → pants_上.png, pants_下.png
```

## License

MIT
