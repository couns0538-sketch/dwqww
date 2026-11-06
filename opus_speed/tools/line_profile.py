"""line_profile.py - aggregate a rip_sampler run of a -g exe by source line (speed hunt, own analysis script).

usage: python -I -B line_profile.py <run dir> [<top N>]
Runs addr2line -f -i -C once over every sampled address; prints the samples per innermost source line, and per
(outer function, innermost line) for the hottest functions.
"""
import collections
import json
import pathlib
import subprocess
import sys


def main():
    run = pathlib.Path(sys.argv[1])
    top = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    meta = json.loads((run / 'meta.json').read_text(encoding='utf-8'))
    counts = {}
    for line in (run / 'addresses.tsv').read_text(encoding='utf-8').splitlines()[1:]:
        v, c = line.split('\t')
        counts[int(v, 16)] = int(c)
    addrs = sorted(counts)
    # addr2line prints, per address, pairs of lines (function, file:line) for each inline frame, innermost first;
    # -a prints the address first so the frames can be split per address.
    out = subprocess.run(['C:/msys64/ucrt64/bin/addr2line.exe', '-a', '-f', '-i', '-C', '-e', meta['exe']],
                         input='\n'.join('0x%x' % a for a in addrs) + '\n', capture_output=True, text=True).stdout
    frames = {}
    cur = None
    lines = out.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith('0x'):
            cur = int(lines[i], 16)
            frames[cur] = []
            i += 1
            continue
        func = lines[i]
        loc = lines[i + 1] if i + 1 < len(lines) else '??:0'
        loc = loc.split(' (discriminator')[0]
        loc = loc.replace('\\', '/').split('/src_copy/')[-1]
        frames[cur].append((func, loc))
        i += 2
    total = sum(counts.values())
    by_line = collections.Counter()
    by_outer_line = collections.Counter()
    for a, c in counts.items():
        fr = frames.get(a) or [('?', '?')]
        inner = fr[0][1]
        outer = fr[-1][0].split('(')[0]
        by_line[inner] += c
        by_outer_line[(outer, inner)] += c
    print('samples %d' % total)
    print('-- innermost source line --')
    for loc, c in by_line.most_common(top):
        print('%6d %5.2f%%  %s' % (c, 100.0 * c / total, loc))
    print('-- outer function / innermost line --')
    for (outer, loc), c in by_outer_line.most_common(top):
        print('%6d %5.2f%%  %-40s %s' % (c, 100.0 * c / total, outer[:40], loc))


if __name__ == '__main__':
    main()
