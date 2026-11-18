#!/usr/bin/env python3
"""Record Astra5's comparable guard matches from a pinned Git tree."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess


CELLS = (
    (8, 'M1', 2000, 7313, 2000, (675, 654, 671)),
    (9, 'M1b', 2000, 7323, 2000, (691, 694, 615)),
    (8, 'M2', 20000, 7314, 800, (239, 221, 340)),
    (9, 'M2b', 20000, 7324, 800, (245, 230, 325)),
    (11, 'M2c', 20000, 7333, 800, (232, 220, 348)),
    (11, 'M2d', 20000, 7334, 800, (213, 224, 363)),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('commit')
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--exclusions', type=Path)
    args = parser.parse_args()

    def read(path):
        return subprocess.check_output(['git', '-C', str(args.repo), 'show', f'{args.commit}:{path}'])

    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    source = manifest['source']['sha256']
    reports = {job: read(f'forge-combo29/REPORT_astra5_job{job}.md') for job in (8, 9, 11)}
    common_engine = 'ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e'
    net_manifest = read('forge-combo29/astra5/job7/step0/r15d.sha256.txt')
    net = re.search(rb'(?m)^([0-9a-f]{64})  src/nnue_weights\.inc$', net_manifest)[1].decode()
    rows = []
    keys_seen = set()
    for job, cell, nodes, seed, games, wld in CELLS:
        cut_source = f'forge-combo29/astra5/job{job}/{cell}'
        assert f'[{cell}](astra5/job{job}/{cell}.pgn)'.encode() in reports[job]
        assert '–'.join(map(str, wld)).encode() in reports[job]
        meta, elo, pgn = (read(f'{cut_source}{suffix}') for suffix in ('.meta', '/elo.txt', '.pgn'))
        details = meta.decode()
        assert f'A nodes {nodes}, B nodes {nodes}; seed {seed}; target games {games}' in details
        assert f'engine SHA256 {common_engine}' in details and f'book SHA256 {source}' in details
        command = next(line for line in details.splitlines() if line.startswith('command '))
        for option in ('-repeat', 'option.NullMateGuard=2', 'option.NullMateGuard=0', 'option.Threads=1',
                       'option.Hash=16', 'option.HistRework=2', 'option.HistoryPruneMultiplier=2220',
                       'option.MateAlphaGuard=true', '-concurrency 4', '-maxmoves 300'):
            assert option in command, option
        record = elo.decode()
        assert f'Match {cell}; complete\nPairs {games//2}/{games//2}; games in these complete pairs {games}' in record
        penta = list(map(int, re.search(r'(?m)^Pentanomial \[.*\] (.*)$', record)[1].split()))
        center, width = map(float, re.search(r'Logistic Elo (.*?); fastchess 95% halfwidth (.*)', record).groups())
        display = re.search(r'(?m)^Reported Elo \[95%\] (.*)$', record)[1]
        fens = re.findall(rb'(?m)^\[FEN "([^"]+)"\]\r?$', pgn)
        keys = [sha256(b' '.join(fen.split()[:4])).hexdigest() for fen in fens]
        assert len(fens) == games and len(set(keys)) == games//2
        keys_seen.update(keys)
        target = 'M5' if nodes == 2000 else 'M6'
        overlap = set(keys).intersection(manifest['cells'][target]['fen_keys_sha256'])
        rows.append(dict(job=job, match=cell, nodes=nodes, seed=seed, games=games, wld=wld, penta=penta,
                         elo=center, halfwidth=width, printed_elo=display, opening_overlap=len(overlap),
                         pgn_sha256=sha256(pgn).hexdigest(), meta_sha256=sha256(meta).hexdigest(),
                         elo_sha256=sha256(elo).hexdigest(), source=cut_source))
    exclusion_text = ''.join(f'{key}\n' for key in sorted(keys_seen))
    if args.exclusions:
        args.exclusions.write_text(exclusion_text)
    report_hashes = {f'forge-combo29/REPORT_astra5_job{job}.md': sha256(report).hexdigest()
                     for job, report in reports.items()}
    print(json.dumps(dict(astra5_commit=args.commit, engine_sha256=common_engine,
                          embedded_net_sha256=net, book_sha256=source,
                          sol_manifest_sha256=sha256(manifest_bytes).hexdigest(), report_hashes=report_hashes,
                          distinct_exclusions=len(keys_seen),
                          exclusion_sha256=sha256(exclusion_text.encode()).hexdigest(), rows=rows), indent=2))


if __name__ == '__main__':
    main()
