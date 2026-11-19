"""Build a fixed, fresh general-opening EPD. Python 3 and chess 1.11.2."""
import argparse
from collections import Counter
import csv
from hashlib import sha256
from io import StringIO
from pathlib import Path
import re
import subprocess
from urllib.request import urlopen
from zipfile import ZipFile

import chess


OPEN_COMMIT = '3ba6b20d31b2e6125cb0e6a2e792f400717d9d39'
OLD_COMMIT = '37751b08db745aa02babfa74056dd1168b9da803'
OLD_SHA = '7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
HISTORY = '7d6cc0914e80bb2df836c8ed94c1c4d26b8777ef'
FEN = re.compile(rb'(?<![A-Za-z0-9/])(?:[prnbqkPRNBQK1-8]+/){7}[prnbqkPRNBQK1-8]+ [wb] (?:[KQkq]+|-) (?:-|[a-h][36])(?=\s|$)')


def fetch(cache, filename, url):
    p = cache / filename
    if not p.exists():
        with urlopen(url, timeout=90) as response:
            p.write_bytes(response.read())
    return p


def key(fen):
    # Ignore en passant and both clocks when excluding older positions.
    return b' '.join(fen.split()[:3])


def named_lines(cache):
    roots = {}
    entries = 0
    for family in 'abcde':
        p = fetch(cache, family+'.tsv', f'https://raw.githubusercontent.com/lichess-org/chess-openings/{OPEN_COMMIT}/{family}.tsv')
        data = p.read_bytes()
        print(f'source {family}.tsv sha256 {sha256(data).hexdigest()}')
        for row in csv.DictReader(StringIO(data.decode()), delimiter='\t'):
            tokens = [w for w in row['pgn'].split() if not re.fullmatch(r'\d+\.+', w)]
            if len(tokens) < 16:
                continue
            board = chess.Board()
            for san in tokens[:16]:
                board.push_san(san)
            if board.is_game_over(claim_draw=True) or board.is_check():
                continue
            entries += 1
            epd = board.epd(en_passant='legal').encode('ascii')
            roots.setdefault(key(epd), (family, epd))
    print(f'nonterminal noncheck named lines reaching ply 16 {entries}; unique position keys {len(roots)}')
    return roots


def files_from_git(repo):
    raw = subprocess.check_output(['git','-C',str(repo),'ls-tree','-r',HISTORY,'forge-combo29/astra5'])
    marked = {}
    for row in raw.splitlines():
        meta, name = row.split(b'\t')
        s = name.decode()
        m = re.match(r'forge-combo29/astra5/job(\d+)/',s)
        if not m:
            continue
        j = int(m[1])
        kind = None
        if j in {*range(1,8),10} and s.endswith(('.tsv','.txt','.epd')):
            kind = 'fen_text'
        if s.endswith('/openings.tsv') and 18 <= j <= 23:
            kind = 'opening_moves'
        if s.endswith('.pgn'):
            kind = 'pgn'
        if kind:
            marked[(meta.split()[2].decode(), kind)] = s
    with subprocess.Popen(['git','-C',str(repo),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE) as proc:
        for (oid,kind),name in sorted(marked.items()):
            proc.stdin.write((oid+'\n').encode()); proc.stdin.flush()
            ident,typ,size = proc.stdout.readline().split()
            assert typ==b'blob' and ident.decode()==oid
            data = proc.stdout.read(int(size))
            assert proc.stdout.read(1)==b'\n'
            yield kind,name,data
        proc.stdin.close()


def prior(cache, repo, candidates):
    used = set()
    archive = fetch(cache,'old-uho.zip',f'https://raw.githubusercontent.com/official-stockfish/books/{OLD_COMMIT}/UHO_Lichess_4852_v1.epd.zip')
    oldhash = sha256()
    with ZipFile(archive) as z, z.open('UHO_Lichess_4852_v1.epd') as stream:
        for count,line in enumerate(stream,1):
            oldhash.update(line)
            k = key(line)
            if k in candidates:
                used.add(k)
    assert count == 2632036 and oldhash.hexdigest()==OLD_SHA
    print(f'prior UHO full source {count} lines SHA256 {OLD_SHA}; candidate intersections {len(used)}')
    moves = set()
    files = Counter()
    for kind,name,data in files_from_git(repo):
        files[kind] += 1
        if kind == 'opening_moves':
            for row in csv.DictReader(StringIO(data.decode()), delimiter='\t'):
                moves.add(row['moves'])
        for fen in FEN.findall(data):
            k = key(fen)
            if k in candidates:
                used.add(k)
    for opening in sorted(moves):
        board = chess.Board()
        for uci in opening.split():
            board.push_uci(uci)
        k = key(board.epd().encode())
        if k in candidates:
            used.add(k)
    print(f'archive {HISTORY}; distinct blobs by type {dict(sorted(files.items()))}; distinct random-game move lists {len(moves)}')
    print(f'candidate intersections across all histories {len(used)}')
    return used


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo',type=Path)
    parser.add_argument('output_dir',type=Path)
    args = parser.parse_args()
    assert chess.__version__=='1.11.2'
    args.output_dir.mkdir(parents=True,exist_ok=True)
    cache = args.output_dir/'source'
    cache.mkdir(exist_ok=True)
    roots = named_lines(cache)
    excluded = prior(cache,args.repo,roots)
    chosen = []
    for family in 'abcde':
        group = [epd for k,(f,epd) in roots.items() if f==family and k not in excluded]
        ranked = sorted(group,key=lambda p:(sha256(b'astra5-job24-240024 '+p).digest(),p))
        chosen.extend(ranked[:64])
        print(f'ECO group {family.upper()}: available {len(group)}, selected {min(64,len(group))}')
    assert len(set(map(key,chosen)))==len(chosen)>=128
    assert not set(map(key,chosen)) & excluded
    data = b'\n'.join(chosen)+b'\n'
    p = args.output_dir/'astra5-general-openings24.epd'
    if p.exists() and p.read_bytes()!=data:
        raise RuntimeError('refusing to replace a different frozen book')
    p.write_bytes(data)
    print(f'final {p.name} lines {len(chosen)} bytes {len(data)} sha256 {sha256(data).hexdigest()}')
    print('overlap of the delivered book with the examined historical source positions: 0')


if __name__=='__main__':
    main()
