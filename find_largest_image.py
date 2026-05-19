from pathlib import Path
from PIL import Image, ImageFile
from tqdm import tqdm
from datetime import datetime

ImageFile.LOAD_TRUNCATED_IMAGES = True

SOURCE_DIR = Path(r"F:\Publish")

IMAGE_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff"
}

# Target Date
TARGET_DATE = "15-05-2026"

largest_size = 0
largest_file = None
largest_width = 0
largest_height = 0

failed = []

for file in tqdm(list(SOURCE_DIR.rglob("*"))):

    if not file.is_file():
        continue

    if file.suffix.lower() not in IMAGE_EXTS:
        continue

    try:

        # File modified date
        modified_time = datetime.fromtimestamp(
            file.stat().st_mtime
        ).strftime("%d-%m-%Y")

        # Skip other dates
        if modified_time != TARGET_DATE:
            continue

        file_size = file.stat().st_size

        if file_size > largest_size:

            with Image.open(file) as img:

                width, height = img.size

                largest_size = file_size
                largest_file = file
                largest_width = width
                largest_height = height

    except Exception as e:
        failed.append(f"{file} | {e}")

print("\n========== RESULT ==========")

if largest_file:

    print(f"File      : {largest_file}")
    print(f"Size MB   : {largest_size / (1024 * 1024):.2f} MB")
    print(f"Width     : {largest_width}")
    print(f"Height    : {largest_height}")

else:
    print("No file found for given date.")

print("\n========== FAILED ==========")
print(f"Failed Count: {len(failed)}")
