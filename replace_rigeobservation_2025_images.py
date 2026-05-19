from pathlib import Path
from tqdm import tqdm
import shutil

SOURCE_DIR = Path(r"F:\Publish\Sixs_api\ApkImages")
OPTIMIZED_DIR = Path(r"G:\Sixs_api\ApkImages_Optimized_NewV1")

# ONLY THIS FOLDER WILL BE PROCESSED
TARGET_RELATIVE_FOLDER = Path(
    r"RigeObservation_SOI_Image\2026"
)

replaced_count = 0
skipped_count = 0
failed = []

target_optimized_folder = (
    OPTIMIZED_DIR / TARGET_RELATIVE_FOLDER
)

optimized_files = list(
    target_optimized_folder.rglob("*")
)

for opt_file in tqdm(optimized_files):

    try:

        if not opt_file.is_file():
            continue

        rel = opt_file.relative_to(OPTIMIZED_DIR)

        original_file = SOURCE_DIR / rel

        # Original file must exist
        if not original_file.exists():
            skipped_count += 1
            continue

        opt_size = opt_file.stat().st_size
        original_size = original_file.stat().st_size

        # Replace only if optimized file is smaller
        if opt_size < original_size:

            shutil.move(
                str(opt_file),
                str(original_file)
            )

            replaced_count += 1

        else:
            skipped_count += 1

    except Exception as e:
        failed.append(f"{opt_file} | {e}")

# ============================================
# RESULT
# ============================================

print("\n========== RESULT ==========")

print(f"Replaced Files : {replaced_count}")
print(f"Skipped Files  : {skipped_count}")
print(f"Failed Files   : {len(failed)}")

# ============================================
# FAILED LOG
# ============================================

if failed:

    log_file = (
        OPTIMIZED_DIR / "replace_failed_log.txt"
    )

    log_file.write_text(
        "\n".join(failed),
        encoding="utf-8"
    )

    print(f"\nFailed log saved:")
    print(log_file)

print("\nDone.")
