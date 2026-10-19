
from pathlib import Path
from zipfile import ZipFile

BASE = Path(__file__).resolve().parents[1] / "data" / "plantvillage"
ZIP_PATH = BASE / "data.zip"
SPLIT_DIR = BASE / "splits"
OUTPUT_DIR = BASE / "extracted"

with ZipFile(ZIP_PATH) as archive:
    archive_names = set(archive.namelist())

    for split in ("train", "test"):
        rows = [
            line.strip()
            for line in (SPLIT_DIR / f"color_{split}.txt")
            .read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        missing = []

        for archive_path in rows:
            relative = Path(*archive_path.split("/")[2:])
            extracted_path = OUTPUT_DIR / split / relative

            if not extracted_path.is_file():
                missing.append((archive_path, archive_path in archive_names))

        print(f"\n{split.upper()}")
        print(f"Official images: {len(rows)}")
        print(f"Missing extracted files: {len(missing)}")

        for path, exists_in_zip in missing[:10]:
            print(f"Missing: {path} | Exists in ZIP: {exists_in_zip}")
