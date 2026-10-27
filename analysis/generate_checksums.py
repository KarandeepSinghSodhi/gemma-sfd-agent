"""
analysis/generate_checksums.py: Computes SHA-256 checksums and file sizes for all files
in dataset_resource/ and writes dataset_resource/checksums.sha256.
"""

import hashlib
from pathlib import Path

ROOT = Path(r"d:\AI Research\gemma_paper")
DATASET_DIR = ROOT / "dataset_resource"

def main():
    lines = []
    print("Computing SHA-256 checksums for dataset_resource...")
    
    files = sorted([f for f in DATASET_DIR.rglob("*") if f.is_file() and f.name != "checksums.sha256"])
    
    for f in files:
        rel = f.relative_to(DATASET_DIR).as_posix()
        h = hashlib.sha256()
        with open(f, "rb") as fh:
            while chunk := fh.read(65536):
                h.update(chunk)
        digest = h.hexdigest()
        size_bytes = f.stat().st_size
        lines.append(f"{digest}  {rel}  ({size_bytes:,} bytes)")
        
    out_file = DATASET_DIR / "checksums.sha256"
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Checksums computed for {len(files)} files and saved to {out_file}")

if __name__ == "__main__":
    main()
