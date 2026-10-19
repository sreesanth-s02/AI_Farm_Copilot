
from pathlib import Path
from zipfile import ZipFile
import shutil

BASE = Path(__file__).resolve().parents[1] / "data" / "plantvillage"
ZIP_PATH = BASE / "data.zip"
SPLIT_DIR = BASE / "splits"
OUTPUT_DIR = BASE / "extracted"

SPLITS = ("train", "test")

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with ZipFile(ZIP_PATH) as archive:
        archive_names = set(archive.namelist())

        for split_name in SPLITS:
            split_file = SPLIT_DIR / f"color_{split_name}.txt"
            rows = [
                line.strip()
                for line in split_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            extracted = 0

            for index, archive_path in enumerate(rows, start=1):
                if archive_path not in archive_names:
                    raise FileNotFoundError(
                        f"Image missing from archive: {archive_path}"
                    )

                relative_path = Path(*archive_path.split("/")[2:])
                destination = OUTPUT_DIR / split_name / relative_path

                if not destination.exists():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(archive_path) as source:
                        with destination.open("wb") as target:
                            shutil.copyfileobj(source, target)

                extracted += 1

                if index % 2000 == 0 or index == len(rows):
                    print(
                        f"{split_name}: {index}/{len(rows)} processed",
                        flush=True,
                    )

            print(
                f"{split_name}: completed {extracted} images",
                flush=True,
            )

    print(f"\nDataset extraction complete: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
