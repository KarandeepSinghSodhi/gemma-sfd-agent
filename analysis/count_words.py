import re
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "KAGGLE_WRITEUP_RESOURCE.md"
text = p.read_text(encoding="utf-8")

# Raw word count
raw_words = len(re.findall(r"\b\w+\b", text))

# Markdown stripped count (excluding table lines and image tags)
lines = []
for line in text.splitlines():
    l = line.strip()
    if l.startswith("|") and l.endswith("|"):
        continue # table row
    if l.startswith("![") and l.endswith(")"):
        continue # image markdown
    if l.startswith("```"):
        continue # code fence
    lines.append(line)

cleaned_text = "\n".join(lines)
cleaned_words = len(re.findall(r"\b\w+\b", cleaned_text))

print(f"Total raw words: {raw_words}")
print(f"Cleaned words (prose): {cleaned_words}")
