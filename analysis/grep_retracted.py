import re
from pathlib import Path

files = ['paper_resource.typ', 'KAGGLE_WRITEUP_RESOURCE.md', 'README.md', 'paper.typ', 'KAGGLE_WRITEUP.md']
keywords = ['simulate', 'simulation', 'synthetic', '_retracted']

found = False
for fn in files:
    p = Path(fn)
    if p.exists():
        text = p.read_text(encoding='utf-8')
        for kw in keywords:
            matches = [m.start() for m in re.finditer(kw, text, re.IGNORECASE)]
            if matches:
                found = True
                print(f'{fn}: found keyword "{kw}" at {len(matches)} places')
                for idx in matches[:5]:
                    snippet = text[max(0, idx-40):min(len(text), idx+40)].replace('\n', ' ')
                    print(f'   ...{snippet}...')

if not found:
    print('Clean! No references to simulation or synthetic data found in papers or writeups.')
