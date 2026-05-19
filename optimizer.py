from pathlib import Path
from PIL import Image, ImageOps, ImageFile
import shutil

ImageFile.LOAD_TRUNCATED_IMAGES = True

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

MAX_SIZE_MB = 1
INITIAL_QUALITY = 85
MIN_QUALITY = 45
MAX_WIDTH = 1920

def run_optimization(source_dir_str, output_dir_str, progress_callback=None, log_callback=None, check_cancel_callback=None, images_only=False):
    SOURCE_DIR = Path(source_dir_str)
    OUTPUT_DIR = Path(output_dir_str)

    if log_callback: log_callback(f"Source: {SOURCE_DIR}")
    if log_callback: log_callback(f"Output: {OUTPUT_DIR}")

    missing_files = []
    failed = []

    # ============================================
    # FIND MISSING FILES
    # ============================================
    if log_callback: log_callback("Scanning for files to process...")

    for src_file in SOURCE_DIR.rglob("*"):
        if not src_file.is_file():
            continue

        if images_only and src_file.suffix.lower() not in IMAGE_EXTS:
            continue

        rel = src_file.relative_to(SOURCE_DIR)
        dst = OUTPUT_DIR / rel

        if not dst.exists():
            missing_files.append(src_file)

    total_files = len(missing_files)
    if log_callback: log_callback(f"Files found to process: {total_files}")

    if total_files == 0:
        if log_callback: log_callback("No new files to optimize.")
        return

    # ============================================
    # PROCESS FILES
    # ============================================
    for i, src_file in enumerate(missing_files):
        if check_cancel_callback and check_cancel_callback():
            if log_callback: log_callback("Optimization cancelled by user.")
            break

        if progress_callback:
            progress_callback(i, total_files)

        rel = src_file.relative_to(SOURCE_DIR)
        dst = OUTPUT_DIR / rel

        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            ext = src_file.suffix.lower()
            size_mb = src_file.stat().st_size / (1024 * 1024)

            # ------------------------------------
            # COPY VIDEOS / NON IMAGES
            # ------------------------------------
            if ext not in IMAGE_EXTS:
                shutil.copy2(src_file, dst)
                continue

            # ------------------------------------
            # SMALL IMAGE => DIRECT COPY
            # ------------------------------------
            if size_mb <= MAX_SIZE_MB:
                shutil.copy2(src_file, dst)
                continue

            # ------------------------------------
            # IMAGE OPTIMIZATION
            # ------------------------------------
            with Image.open(src_file) as img:
                img = ImageOps.exif_transpose(img)

                # Convert unsupported modes
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Resize large images
                if img.width > MAX_WIDTH:
                    ratio = MAX_WIDTH / img.width
                    new_height = int(img.height * ratio)

                    img = img.resize(
                        (MAX_WIDTH, new_height),
                        Image.LANCZOS
                    )

                quality = INITIAL_QUALITY

                while quality >= MIN_QUALITY:
                    img.save(
                        dst,
                        format="JPEG" if ext in [".jpg", ".jpeg"] else None,
                        quality=quality,
                        optimize=True,
                        progressive=True
                    )

                    final_size_mb = dst.stat().st_size / (1024 * 1024)

                    if final_size_mb <= MAX_SIZE_MB:
                        break

                    quality -= 5

        except Exception as e:
            failed.append(f"{src_file} | {e}")
            try:
                shutil.copy2(src_file, dst)
            except Exception as copy_error:
                failed.append(f"{src_file} | copy failed: {copy_error}")

    if progress_callback:
        progress_callback(total_files, total_files)

    # ============================================
    # FAILED LOG
    # ============================================
    if failed:
        log_file = OUTPUT_DIR / "missing_failed_log.txt"
        log_file.write_text("\n".join(failed), encoding="utf-8")
        if log_callback: log_callback(f"Failed log saved: {log_file}")

    if log_callback: log_callback("Done. Missing files optimized/copied.")

if __name__ == "__main__":
    # Fallback to simple console execution if run directly
    import sys
    
    # You can change these default paths if needed
    source = r"F:\Publish\Sixs_api\ApkImages"
    output = r"G:\Sixs_api\ApkImages_Optimized_NewV1"
    
    print("Starting optimization...")
    from tqdm import tqdm
    pbar = None
    
    def on_progress(current, total):
        global pbar
        if pbar is None:
            pbar = tqdm(total=total)
        pbar.update(current - pbar.n)
        if current == total:
            pbar.close()

    run_optimization(source, output, progress_callback=on_progress, log_callback=print)
