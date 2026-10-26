import json
from pathlib import Path

ROOT = Path(r"d:\AI Research\gemma_paper")
writeup_path = ROOT / "KAGGLE_WRITEUP.md"
writeup = writeup_path.read_text(encoding="utf-8")

# Split writeup into major logical sections by '---'
parts = [p.strip() for p in writeup.split("\n---\n") if p.strip()]

cells = []
for p in parts:
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in p.splitlines()]
    })

# Add Appendix code cell verifying submission_sfd.zip and agent_sfd files
code_appendix = """# ==============================================================================
# Appendix: Architecture Verification & SHA-256 Provenance Check
# ==============================================================================
import hashlib
from pathlib import Path

print("State-Filtered Deliberation (SFD) Verification:")
print("- Pre-evaluation commit: af0937d4109f956d7d11aa560809bcb4f6bab471 (2026-10-25 21:23:27 UTC)")
print("- Competition submission archive: submission_sfd.zip")
print("- Expected SHA-256: c4857f8d163fe7d64d74b22370ee26ad8f6e23af50678edc4414fb2f2d928124")

zip_path = Path("submission_sfd.zip")
if zip_path.exists():
    h = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"Calculated archive SHA-256: {h}")
    print(f"Exact match: {h == 'c4857f8d163fe7d64d74b22370ee26ad8f6e23af50678edc4414fb2f2d928124'}")
else:
    print("Run inside repo root to verify local file hashes.")
"""

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [line + "\n" for line in code_appendix.splitlines()]
})

nb = {
    "cells": cells,
    "metadata": {
        "language_info": {"name": "python"},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

kernel_dir = ROOT / "kaggle_kernel"
nb_out = kernel_dir / "sfd_developer_agent.ipynb"
nb_out.write_text(json.dumps(nb, indent=1), encoding="utf-8")

# Update kernel-metadata.json for clean fast CPU execution
meta = {
    "id": "karandeepsinghsodhi/sfd-state-filtered-deliberation-agent-gemma-4",
    "title": "SFD: State-Filtered Deliberation Agent (Gemma 4)",
    "code_file": "sfd_developer_agent.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": False,
    "enable_gpu": False,
    "enable_tpu": False,
    "enable_internet": False,
    "keywords": [
        "research-paper",
        "software-engineering",
        "agents",
        "gemma"
    ],
    "dataset_sources": [],
    "kernel_sources": [],
    "competition_sources": [
        "gemma-4-developer-agent"
    ],
    "model_sources": []
}
(kernel_dir / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
print(f"Successfully generated {nb_out} with {len(cells)} cells and updated {kernel_dir / 'kernel-metadata.json'}")
