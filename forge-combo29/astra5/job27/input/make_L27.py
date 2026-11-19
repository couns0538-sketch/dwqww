"""Construct Job 27's canonical opening list and document every excluded source line."""
import argparse
from pathlib import Path
import hashlib
import subprocess

REPOSITORY = 'https://github.com/couns0538-sketch/dwqww.git'
REF = 'for-fable-and-opus/deepseek5-work'
REVISION = '731fc808e3e0770805cb67654dea498d3bcdb6c6'
FILE = 'forge-combo29/tests_deepseek5_job10/set_O.epd'
O_DIGEST = '02d59eaf2515a4e11aecb78c5736db193812516f42ab8a6aa0b2411332186300'
BOOK_DIGEST = '889e8db12ee327cae68b29ada3458a2fb957cf8f5563d29a7fd13d850ff3f638'


def read_position(raw):
    parts = raw.split()
    if len(parts) < 4:
        raise ValueError(f'Invalid opening record {raw!r}')
    return ' '.join(parts[:4])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path, help='shallow checkout containing the named deepseek5 revision')
    parser.add_argument('book', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    args.evidence.mkdir(parents=True, exist_ok=True)
    def git(*argv):
        return subprocess.check_output(['git', '-C', args.checkout, *argv])
    source = git('show', f'{REVISION}:{FILE}')
    book = args.book.read_bytes()
    assert hashlib.sha256(source).hexdigest() == O_DIGEST
    assert hashlib.sha256(book).hexdigest() == BOOK_DIGEST
    o_lines, book_lines = [d.decode('ascii').splitlines() for d in (source, book)]
    assert (len(o_lines), len(book_lines)) == (200, 234)
    result = []
    first = {}
    excluded = []
    for label, records in [('O', o_lines), ('book', book_lines)]:
        for lineno, raw in enumerate(records, 1):
            key = read_position(raw)
            if label == 'book' and key in first:
                first_source, first_line, index = first[key]
                excluded.append((lineno, first_source, first_line, index, key))
                continue
            result.append(key + ' 0 1')
            first.setdefault(key, (label, lineno, len(result)))
    output = ('\n'.join(result) + '\n').encode('ascii')
    args.output.write_bytes(output)
    digest = hashlib.sha256(output).hexdigest()
    with (args.evidence / 'omitted.tsv').open('w', encoding='ascii') as f:
        print('book_line\tfirst_source\tfirst_source_line\tL27_line\tfirst_four_fields', file=f)
        for row in excluded:
            print(*row, sep='\t', file=f)
    with (args.evidence / 'openings-provenance.txt').open('w', encoding='ascii') as f:
        print(f'Set O repository {REPOSITORY}\nRef refs/heads/{REF}\nSource commit {REVISION}\nPath {FILE}\nBlob '+git('rev-parse',f'{REVISION}:{FILE}').decode().strip(),file=f)
        print(f'Source retrieval: git fetch --no-tags --depth=1 --filter=blob:none origin {REF}; git show {REVISION}:{FILE}',file=f)
        print(f'Set O: {len(o_lines)} lines; SHA-256 {O_DIGEST}',file=f)
        print(f'Job 24 {args.book.name}: {len(book_lines)} lines; SHA-256 {BOOK_DIGEST}',file=f)
        print(f'All {len(o_lines)} O lines are retained in order; {len(book_lines)-len(excluded)} book lines follow in original order. A book line is omitted when its first four fields equal an earlier included line.',file=f)
        print('Excluded book source line numbers (1-based): '+(', '.join(str(r[0]) for r in excluded) or 'none'),file=f)
        print(f'L27: {len(result)} lines; SHA-256 {digest}',file=f)
        print('Each output line and game FEN uses the first four fields plus " 0 1"; file ends in LF. Detailed matches are in omitted.tsv.',file=f)


if __name__ == '__main__':
    main()
