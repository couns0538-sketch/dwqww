#!/usr/bin/env python3
"""merge_licences.py - rebuild the "checked by this job" table of LICENCES.md from the workers' notes.

usage: python -I -B merge_licences.py [--no-recheck]
Collects every (repo, commit) row from notes/T*/licences.md, re-runs tools/licence_at.py --row at that exact commit
(so an old row with a wrong guess is corrected; --no-recheck keeps the workers' rows), and rewrites the block between
"<!-- merged:start -->" and "<!-- merged:end -->" in LICENCES.md. Repos of the 30-Oct table that no worker read are
listed as "not read by this job".
"""
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ROW = re.compile(r'^\|\s*([\w.-]+/[\w.-]+)\s*\|\s*([0-9a-f]{7,40})\s*\|(.*)$')
OCT30 = {
    'Witek902/Caissa': 'MIT', 'Alex2262/AltairChessEngine': 'MIT', 'Adam-Kulju/Patricia': 'MIT', 'jw1912/bullet': 'MIT',
    'jdart1/Fathom': 'verify', 'official-stockfish/Stockfish': 'GPL-3.0', 'jhonnold/berserk': 'GPL-3.0',
    'gab8192/Obsidian': 'GPL-3.0', 'Yoshie2000/PlentyChess': 'GPL-3.0', 'Ciekce/Stormphrax': 'GPL-3.0',
    'PGG106/Alexandria': 'GPL-3.0', 'Luecx/Koivisto': 'GPL-3.0', 'AndyGrant/Ethereal': 'GPL-3.0',
    'KierenP/Halogen': 'GPL-3.0', 'Matthies/RubiChess': 'GPL-3.0', 'official-stockfish/fishtest': 'GPL-3.0',
    'official-stockfish/nnue-pytorch': 'GPL-3.0', 'cosmobobak/viridithas': 'AGPL-3.0-only since v21',
    'codedeliveryservice/Reckless': 'AGPL', 'aronpetko/integral': 'no LICENSE file',
}


def use_of(lic):
    l = lic.upper()
    if l.startswith(('MIT', 'BSD', 'APACHE', 'UNLICENSE')):
        return 'copy with notice'
    if l.startswith('CC0'):
        return 'free use (public-domain dedication)'
    if 'GPL' in l:
        return 'ideas only'
    if 'NO LICENCE' in l or 'ABSENT' in l:
        return 'ideas only (no licence)'
    return 'check the text'


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    recheck = '--no-recheck' not in sys.argv
    seen = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'notes', 'T*', 'licences.md'))):
        track = os.path.basename(os.path.dirname(f))
        for line in open(f, encoding='utf-8', errors='replace'):
            m = ROW.match(line.strip())
            if m:
                key = (m.group(1), m.group(2)[:10])
                seen.setdefault(key, {'tracks': set(), 'row': line.strip()})['tracks'].add(track)
    out = ['| repo | commit read | date | file | licence | first line | GitHub API | tracks | use |',
           '|---|---|---|---|---|---|---|---|---|']
    cache_path = 'F:/odr/cache/licence_rows.json'
    try:
        cache = json.load(open(cache_path, encoding='utf-8'))
    except (OSError, ValueError):
        cache = {}
    tool_mtime = str(os.path.getmtime(os.path.join(HERE, 'licence_at.py')))
    for (repo, sha), v in sorted(seen.items()):
        row = v['row']
        if recheck:
            ck = f'{repo}@{sha}'
            hit = cache.get(ck)
            if hit and hit.get('tool') == tool_mtime:
                row = hit['row']
            else:
                r = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'licence_at.py'), repo, sha, '--row'],
                                   capture_output=True, text=True, encoding='utf-8')
                if r.returncode == 0 and r.stdout.strip().startswith('|'):
                    row = r.stdout.strip().splitlines()[0]
                    cache[ck] = {'row': row, 'tool': tool_mtime}
        cells = [c.strip() for c in row.strip('|').split('|')]
        while len(cells) < 7:
            cells.append('')
        lic = cells[4]
        out.append('| ' + ' | '.join(cells[:7] + [', '.join(sorted(v['tracks'])), use_of(lic)]) + ' |')
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path + '.part', 'w', encoding='utf-8', newline='\n') as f:
        json.dump(cache, f)
    os.replace(cache_path + '.part', cache_path)
    read = {k[0] for k in seen}
    out.append('')
    out.append('30-Oct table repos not read by this job (no check needed unless a card cites them): ' +
               ', '.join(f'{r} ({l})' for r, l in OCT30.items() if r not in read) + '.')
    path = os.path.join(ROOT, 'LICENCES.md')
    text = open(path, encoding='utf-8').read()
    block = '<!-- merged:start -->\n' + '\n'.join(out) + '\n<!-- merged:end -->'
    if '<!-- merged:start -->' in text:
        text = re.sub(r'<!-- merged:start -->.*?<!-- merged:end -->', lambda _: block, text, flags=re.S)
    else:
        text = text.rstrip('\n') + '\n\n## Checked by this job (tools/merge_licences.py)\n' + block + '\n'
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print(f'{len(seen)} (repo, commit) rows merged from {len(set(t for v in seen.values() for t in v["tracks"]))} tracks')


if __name__ == '__main__':
    main()
