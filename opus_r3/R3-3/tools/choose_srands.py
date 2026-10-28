"""Pick one srand per R3-3 entry from the deterministic candidates (make_cands.py).

A candidate is rejected if
  - it appears literally (digit-bounded) in any scanned file or git blob (candidate_hits of every scan), or
  - it is in the merged used-value set (srand/seed context values of every scan), or
  - it equals a manifest srand or openings_start of the live manifest copy.
Openings starts: 390001 + 3000 * (n - 1) for R3-n (the PC adds 3000 per gate; the live manifest max is 366001,
so 369001..387001 stay free for automatic confirm gates the runner may append before these entries are installed).

Usage: python -I -B choose_srands.py <cands_map.json> <manifest copy> <out.json> <scan1.json> [<scan2.json> ...]
"""
import json
import sys


def load_manifest(p):
    raw = open(p, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    return json.loads(raw.decode('utf-8'))


def main():
    cmap = json.load(open(sys.argv[1]))
    man = load_manifest(sys.argv[2])
    used = set()
    hits = {}
    files = 0
    for p in sys.argv[4:]:
        d = json.load(open(p, encoding='utf-8'))
        files += d['files_scanned']
        used |= {int(v) for v in d['context'].keys()}
        for v, paths in d['candidate_hits'].items():
            hits.setdefault(int(v), []).extend(paths)
    man_srands = {int(g['srand']) for g in man['gates'] if g.get('srand') is not None}
    man_starts = {int(g['openings_start']) for g in man['gates'] if g.get('openings_start')}
    max_start = max(man_starts)
    chosen = {}
    rejected = {}
    for eid, cands in cmap.items():
        for k, v in enumerate(cands):
            why = []
            if v in hits:
                why.append('literal hit: ' + '; '.join(hits[v][:3]))
            if v in used:
                why.append('in used set')
            if v in man_srands or v in man_starts:
                why.append('in manifest')
            if v in chosen.values():
                why.append('already chosen')
            if why:
                rejected.setdefault(eid, []).append([k, v, why])
                continue
            chosen[eid] = v
            break
        else:
            raise SystemExit(f'no clean candidate for {eid}')
    starts = {}
    for eid in chosen:
        if eid.startswith('R3-') and eid[3:].isdigit():
            n = int(eid[3:])
            s = 390001 + 3000 * (n - 1)
            assert s not in man_starts and s > max_start + 3000 * 7
            starts[eid] = s
    out = {'chosen_srand': chosen, 'openings_start': starts, 'rejected': rejected,
           'n_used_values_checked': len(used), 'n_files_and_blobs_scanned': files,
           'manifest_srands': len(man_srands), 'manifest_max_openings_start': max_start,
           'rule': 'first SHA-256 candidate (k = 0..3) absent from every scanned file/blob and from the used set'}
    with open(sys.argv[3], 'w', newline='\n') as fh:
        json.dump(out, fh, indent=1)
    for eid, v in chosen.items():
        print(eid, v, starts.get(eid, '-'), 'rejected before: %d' % len(rejected.get(eid, [])))


if __name__ == '__main__':
    main()
