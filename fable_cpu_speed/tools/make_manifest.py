# make_manifest.py - DONE.md and MANIFEST.tsv without circular hashes (Python standard library only).
#   payload      = every file under fable_cpu_speed/ except DONE.md and MANIFEST.tsv
#   DONE.md      = DONE_head.md (the hand-written verdicts) + the payload list with MD5; it does not list itself
#                  and does not list MANIFEST.tsv
#   MANIFEST.tsv = payload + DONE.md with bytes, MD5 and SHA256; it does not list itself
#   python -I -B make_manifest.py write    (writes both files)
#   python -I -B make_manifest.py verify   (recomputes every hash from the files and compares; exit 0 only if equal)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402

ROOT = U.REPO + r'\fable_cpu_speed'
EXCLUDE = ('DONE.md', 'MANIFEST.tsv')


def payload():
    out = []
    for d, _dirs, files in os.walk(ROOT):
        for f in files:
            rel = os.path.relpath(os.path.join(d, f), ROOT).replace('\\', '/')
            if rel not in EXCLUDE:
                out.append(rel)
    return sorted(out)


def done_text():
    head = open(os.path.join(ROOT, 'DONE_head.md'), 'r', encoding='utf-8').read().rstrip('\n')
    lines = [head, '', '## Payload files with MD5', '',
             'Every file under `fable_cpu_speed/` except `DONE.md` itself and `MANIFEST.tsv` (explicit exclusions, so that no hash depends on itself). `MANIFEST.tsv` lists the same files plus `DONE.md`, with MD5 and SHA256, and excludes itself.',
             '', '| File | MD5 |', '|---|---|']
    for rel in payload():
        lines.append('| `%s` | `%s` |' % (rel, U.hashes(os.path.join(ROOT, rel))[0]))
    return '\n'.join(lines) + '\n'


def manifest_text():
    lines = ['# path\tbytes\tmd5\tsha256   (payload files and DONE.md; this file excludes itself)']
    for rel in payload() + ['DONE.md']:
        p = os.path.join(ROOT, rel)
        md5, sha = U.hashes(p)
        lines.append('%s\t%d\t%s\t%s' % (rel, os.path.getsize(p), md5, sha))
    return '\n'.join(lines) + '\n'


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    U.require_lane()
    dp, mp = os.path.join(ROOT, 'DONE.md'), os.path.join(ROOT, 'MANIFEST.tsv')
    if mode == 'write':
        with open(dp, 'w', encoding='utf-8', newline='\n') as f:
            f.write(done_text())
        with open(mp, 'w', encoding='utf-8', newline='\n') as f:
            f.write(manifest_text())
        print('wrote DONE.md (%d payload files) and MANIFEST.tsv' % len(payload()))
    ok_d = open(dp, 'r', encoding='utf-8', newline='').read() == done_text()
    ok_m = open(mp, 'r', encoding='utf-8', newline='').read() == manifest_text()
    print('verify: DONE.md payload list %s; MANIFEST.tsv %s; payload files %d' % (
        'matches the files' if ok_d else 'DOES NOT MATCH', 'matches the files' if ok_m else 'DOES NOT MATCH', len(payload())))
    print('MANIFEST.tsv md5 %s sha256 %s' % U.hashes(mp))
    print('STATUS.md md5 %s' % U.hashes(os.path.join(ROOT, 'STATUS.md'))[0])
    return 0 if (ok_d and ok_m) else 1


if __name__ == '__main__':
    sys.exit(main())
