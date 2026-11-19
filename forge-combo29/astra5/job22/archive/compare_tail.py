"""Verify persistent process receipts and replay the file comparisons from archived inputs."""
import argparse
import csv
from hashlib import sha256
from itertools import zip_longest
from pathlib import Path

BUILDS = ('r15d', 'kF')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def read_canonical(directory):
    entries = rows(directory / 'records-manifest.tsv')
    require(entries and entries[-1]['kind'] == 'whole', f'missing manifest total in {directory}')
    chunks = []
    for meta in entries[:-1]:
        require(meta['kind'] == 'part', f'invalid manifest member in {directory}')
        chunk = (directory / meta['file']).read_bytes()
        require((len(chunk), chunk.count(b'\n'), sha256(chunk).hexdigest())
                == (int(meta['bytes']), int(meta['rows']), meta['sha256']), f'part mismatch in {directory}')
        chunks.append(chunk)
    data = b''.join(chunks)
    whole = entries[-1]
    require((len(data), data.count(b'\n'), sha256(data).hexdigest()) ==
            (int(whole['bytes']), int(whole['rows']), whole['sha256']), f'whole mismatch in {directory}')
    return data


def difference(left, right):
    for rownum, (a, b) in enumerate(zip_longest(left.splitlines(), right.splitlines()), 1):
        if a != b:
            return rownum, a.decode() if a is not None else 'EOF', b.decode() if b is not None else 'EOF'
    return None


def game_chunks(data, receipts):
    start = 0
    result = {}
    for row in receipts:
        end = int(row['record_bytes'])
        game = int(row['book_line'])
        require(start <= end <= len(data), f'bad game end for {game}')
        result[game] = data[start:end]
        start = end
    require(start == len(data), 'last receipt does not cover complete stream')
    return result


def check(results, archive, output):
    barriers = rows(results/'L1-barriers.tsv')
    evidence = []
    details = ['Independent comparison of the normalized four-column archive and process observations.']
    streams = {}
    game_data = {}
    lifetimes = set()
    for build in BUILDS:
        for stage in ('L1', 'L0'):
            arm = f'{stage}-{build}'
            folder = archive/arm
            require('mode final\n' in (folder/'archive.txt').read_text(), f'{arm} lacks final archive')
            data = read_canonical(folder)
            games = rows(folder/'games.tsv')
            rss = rows(folder/'rss-all.tsv')
            raw = (folder/'rss-source.txt').read_text().splitlines()
            require(len(games) == len(rss) == len(raw), f'{arm} has missing RSS or receipt')
            identity = {(r['pid'], r['start_ticks']) for r in rss}
            require(len(identity) == 1 and not identity & lifetimes, f'{arm} process uniqueness failed')
            lifetimes.update(identity)
            pid, ticks = next(iter(identity))
            run = (results/arm/'run.log').read_text()
            require(f'P1_Both pid {pid} ' in run and f'engine_start_ticks {ticks}\n' in run, f'{arm} runner identity failed')
            require(run.count('NNUE v3 active:') >= 1 and 'checksum 30ab43b4ba5db5f3' in run, f'{arm} missing active net checksum')
            checkpoints = {1, 1000, 2000, 3000, 4000, len(games)}
            milestones = []
            for i, (row, obs, line) in enumerate(zip(games, rss, raw), 1):
                game = row['book_line']
                require(row['p1_pid'] == row['p2_pid'] == obs['pid'] and obs['game'] == game and int(obs['completed']) == i, f'{arm} RSS/receipt mismatch at {game}')
                prefix = f"{i} {game} {pid} {obs['observed_utc']} VmRSS:"
                require(line.startswith(prefix) and line[len(prefix):].split()==[obs['vmrss_kb'],'kB'], f'{arm} raw /proc value differs at {game}')
                require(obs['observed_utc'] <= row['end_utc'], f'{arm} RSS observed after receipt')
                if stage == 'L1':
                    b = barriers[i-1]
                    require(int(b['ordinal']) == i and obs['game'] == b['game'] and
                            (pid, obs['vmrss_kb']) == (b[f'{build}_pid'], b[f'{build}_vmrss_kb']) and
                            b['released_utc'] <= obs['observed_utc'] <= row['end_utc'] <= b['both_done_utc'], f'{arm} L1 coordinator differs for {game}')
                if i in checkpoints:
                    milestones.append(obs)
                    evidence.append([stage, build, i, game, pid, ticks, obs['vmrss_kb'], obs['observed_utc']])
            require(milestones == rows(folder/'rss.tsv'), f'{arm} wrong milestone selection')
            if stage == 'L1':
                require(len(games)==len(barriers), f'{arm} L1 coordinator receipt count differs')
            streams[arm] = data
            game_data[arm] = game_chunks(data, games)
            details.append(f"{arm} games {len(games)} after-game VmRSS observations {len(rss)} engine_pid {pid} start_ticks {ticks} "
                           f"first_kB {rss[0]['vmrss_kb']} last_kB {rss[-1]['vmrss_kb']}")
    left, right = (streams[f'L1-{b}'] for b in BUILDS)
    ga, gb = (game_data[f'L1-{b}'] for b in BUILDS)
    require(list(ga)==list(gb), 'L1 games differ across builds')
    ids = list(ga)
    require(ids == list(range(700001,700001+len(ids))), 'nonconsecutive L1 book lines')
    mismatch = [i for i in ids if ga[i] != gb[i]]
    first = difference(left, right)
    require(bool(first)==bool(mismatch), 'per-game and whole-file differences disagree')
    details.append(f"L1 shared game range {ids[0]}..{ids[-1]} both arms {len(ids)} games "
                   f"and {len(mismatch)} differing games; reading {'DIFFERS' if first else 'IDENTICAL'}.")
    if first:
        n, a, b = first
        details.extend([f'first differing row {n}', f'r15d {a}', f'kF {b}'])
        game = mismatch[0]
        for build in BUILDS:
            arm = f'L1-{build}'
            opening = next(line.split('\t', 1)[1] for line in (results/arm/'openings.tsv').read_text().splitlines() if line.startswith(f'{game}\t'))
            prior = []
            for x,y in zip(ga[game].splitlines(),gb[game].splitlines()):
                if x != y:
                    break
                prior.append(x.decode().split()[2])
            details.append(f'{build} moves to difference: {opening} {" ".join(prior)}')
    for build in BUILDS:
        arm = f'L0-{build}'
        cut = b''.join(game_data[f'L1-{build}'][g] for g in ids[-10:])
        require(list(game_data[arm])==ids[-10:], f'{arm} fresh game bounds differ')
        require(cut == (results/arm/'from-L1.txt').read_bytes(), f'{arm} driver suffix disagrees with archived last ten')
        fresh = streams[arm]
        first = difference(cut, fresh)
        details.append(f"{arm} freshly replayed {ids[-10]}..{ids[-1]}; L1 suffix bytes {len(cut)} SHA256 {sha256(cut).hexdigest()} "
                       f"fresh bytes {len(fresh)} SHA256 {sha256(fresh).hexdigest()} reading {'CARRIES' if first else 'SAME'}.")
        if first:
            details.extend([f'first differing suffix row {first[0]}', f'L1 {first[1]}', f'L0 {first[2]}'])
    output.mkdir(parents=True,exist_ok=True)
    (output/'suffix-memory-check.txt').write_text('\n'.join(details)+'\n')
    with (output/'memory-milestones.tsv').open('w',newline='') as f:
        write=csv.writer(f,delimiter='\t',lineterminator='\n')
        write.writerow(['stage','build','completed','game','pid','start_ticks','vmrss_kb','observed_utc'])
        write.writerows(evidence)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,default=Path('/workspace/work/j22archive/export'))
    parser.add_argument('--results',type=Path,default=Path('/workspace/work/j22match/results'))
    parser.add_argument('--out',type=Path,default=Path('/workspace/work/j22archive/crosscheck'))
    args=parser.parse_args()
    check(args.results,args.archive,args.out)
