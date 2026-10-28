"""Print full manifest entries by tag (read-only on the scratch copy of forge_gates.json).

Usage: python -I -B show_entries.py <forge_gates.json copy> <tag> [<tag> ...]
"""
import json
import sys


def main():
    raw = open(sys.argv[1], 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    man = json.loads(raw.decode('utf-8'))
    want = set(sys.argv[2:])
    for g in man['gates']:
        if g.get('tag') in want:
            print(json.dumps(g, indent=1, ensure_ascii=True))
    print('lock:', json.dumps(man.get('lock'), ensure_ascii=True)[:600])
    print('comment:', json.dumps(man.get('comment'), ensure_ascii=True)[:1500])


if __name__ == '__main__':
    main()
