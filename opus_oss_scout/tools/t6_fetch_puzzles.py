#!/usr/bin/env python3
"""t6_fetch_puzzles.py - OSS scout T6: a seeded random sample of Lichess puzzles (CC0-1.0,
https://huggingface.co/datasets/Lichess/chess-puzzles) via the public dataset-viewer rows API, as JSONL.

usage: python -I -B t6_fetch_puzzles.py <out.jsonl> [--blocks 20] [--per-block 100] [--seed 20261106] [--total 6157341]
Each block = one request of --per-block consecutive rows at a seeded random offset. Keeps PuzzleId, FEN, Moves, Rating,
RatingDeviation, Popularity, NbPlays, Themes. Generic User-Agent; read-only on the network; refuses to overwrite.
"""
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request

API = 'https://datasets-server.huggingface.co/rows'
KEEP = ('PuzzleId', 'FEN', 'Moves', 'Rating', 'RatingDeviation', 'Popularity', 'NbPlays', 'Themes')


def fetch(offset, length):
    q = urllib.parse.urlencode({'dataset': 'Lichess/chess-puzzles', 'config': 'default', 'split': 'train',
                                'offset': offset, 'length': length})
    req = urllib.request.Request(f'{API}?{q}', headers={'User-Agent': 'oss-scout-fetch/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))


def main(argv):
    out = argv[0]
    blocks, per, seed, total = 20, 100, 20261106, 6157341
    i = 1
    while i < len(argv):
        k, v = argv[i], argv[i + 1]
        if k == '--blocks':
            blocks = int(v)
        elif k == '--per-block':
            per = int(v)
        elif k == '--seed':
            seed = int(v)
        elif k == '--total':
            total = int(v)
        i += 2
    if os.path.exists(out):
        sys.exit(f'refusing: {out} exists')
    rng = random.Random(seed)
    offsets = sorted(rng.randrange(0, total - per) for _ in range(blocks))
    n = 0
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        for off in offsets:
            for attempt in range(4):
                try:
                    d = fetch(off, per)
                    break
                except Exception as e:  # network hiccup: retry a few times
                    if attempt == 3:
                        raise
                    time.sleep(3)
            for row in d.get('rows', []):
                r = row['row']
                rec = {k: r.get(k) for k in KEEP}
                rec['offset'] = row.get('row_idx')
                f.write(json.dumps(rec) + '\n')
                n += 1
            time.sleep(0.5)
    print(f'wrote {n} puzzles from {blocks} blocks (seed {seed}) to {out}; offsets {offsets[:3]}...')


if __name__ == '__main__':
    main(sys.argv[1:])
