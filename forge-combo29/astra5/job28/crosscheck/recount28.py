"""Recount Job 28 using only compact game and search tables, then check the final audit."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
from hashlib import sha256
import io
import json
from math import isclose, log10, sqrt
from pathlib import Path
from statistics import NormalDist


ARMS = ('M4', 'M5', 'M6')
BY45 = datetime.fromisoformat('2026-11-19T22:59:52+00:00')
STOP = datetime.fromisoformat('2026-11-19T23:04:52+00:00')


def require(value, evidence):
    if not value:
        raise ValueError(evidence)


def read_table(path, root, digests):
    data = path.read_bytes()
    digests.append(f'{path.relative_to(root)}\t{len(data)}\t{sha256(data).hexdigest()}')
    return list(csv.DictReader(io.StringIO(data.decode('ascii')), delimiter='\t'))


def ci(bins):
    # Each pair contributes one normalized score in {0,.25,.50,.75,1}.
    n = sum(bins)
    mean = sum(i * count for i, count in enumerate(bins)) / (4 * n)
    variance = sum(count * (i / 4 - mean)**2 for i, count in enumerate(bins)) / n
    margin = NormalDist().inv_cdf(.975) * sqrt(variance / n)
    if not 0 < mean - margin <= mean + margin < 1:
        return None
    def logistic(p):
        return 400 * log10(p / (1-p))
    elo = logistic(mean)
    width = (logistic(mean + margin) - logistic(mean - margin)) / 2
    return (elo, elo - width, elo + width)


def recount(root, audit, out, checkpoint=False):
    manifest = ['path\tbytes\tsha256']
    openings, last_utc = [], []
    games = {s: {} for s in ARMS}
    events, skipped = [], []
    counters = {s: Counter() for s in ARMS}
    for b in range(1, 10):
        lo, hi = 50*(b-1)+1, min(50*b, 434)
        wanted = set(range(2*lo-1, 2*hi+1))
        group = {}
        for s in ARMS:
            folder = root / f'block{b:03}' / s
            gf = folder/'games.tsv'
            if gf.is_file():
                rows = read_table(gf, root, manifest)
                ids = [int(g['game']) for g in rows]
                require(len(ids)==len(set(ids)) and set(ids)<=wanted, (s,b,'game IDs'))
                if set(ids)==wanted:
                    group[s] = (folder,rows)
        if len(group) < 3:
            skipped.append(b)
            continue
        require(not skipped, (b,'non-prefix common block',skipped))
        openings.extend(range(lo, hi+1))
        finishes = []
        for s,(folder,rows) in group.items():
            tally = counters[s]
            by_game = defaultdict(list)
            for x in read_table(folder/'searches.tsv',root,manifest):
                by_game[int(x['game'])].append(x)
            require(set(by_game)<=wanted, (s,b,'unmatched search/game IDs'))
            for g in rows:
                game, k = int(g['game']),int(g['opening'])
                require(game not in games[s] and k==(game+1)//2, (s,game,'numbering'))
                color = dict(W=g['white'],B=g['black'])
                require(color['W']==('A' if game%2 else 'B') and set(color.values())=={'A','B'}, (s,game,'colors'))
                score = {'1-0':int(color['W']=='A')*2,'0-1':int(color['B']=='A')*2,'1/2-1/2':1}[g['result']]
                games[s][game] = score
                clock = {'W':6000,'B':6000}
                forfeited = False
                turns = by_game[game]
                for ply,x in enumerate(turns,1):
                    side = x['side']
                    player = color[side]
                    n = int(x['N'])
                    charge = n // 100
                    before = clock[side]
                    require((int(x['ply']),x['engine'],int(x['used']),int(x['clock_before']),int(x['wtime']),int(x['btime']))==
                            (ply,player,charge,before,clock['W'],clock['B']), (s,game,ply,'charge or clock'))
                    require(x['soft_line']==f'info string softnodes nodes {n}' and x['move_line'].split()[1]==x['bestmove'], (s,game,ply,'literal lines'))
                    tally['searches',player]+=1
                    tally['used',player]+=charge
                    tally['nodes',player]+=n
                    tally['holds',player]+=int(x['holds'])>0
                    if charge >= before:
                        kind='time loss' if charge>before else 'exactly spent'
                        events.append((s,game,ply,side,player,n,charge,before,kind))
                    if charge > before:
                        require(ply==len(turns) and g['ending']=='time' and g['result']==('0-1' if side=='W' else '1-0'), (s,game,ply,'time verdict'))
                        forfeited = True
                    else:
                        clock[side] += 60 - charge
                    require(int(x['clock_after'])==clock[side], (s,game,ply,'post clock'))
                require((int(g['plies']),int(g['wclock']),int(g['bclock']),g['ending']=='time')==
                        (len(turns)-int(forfeited),clock['W'],clock['B'],forfeited), (s,game,'terminal clock or plies'))
                for side in clock:
                    tally['role_clock',color[side]]+=clock[side]
                    tally['color_clock',side]+=clock[side]
                tally['ending',g['ending']]+=1
                finishes.append(datetime.fromisoformat(g['ended_utc']))
        last_utc.append(max(finishes))
    if checkpoint:
        return f'{len(last_utc)} common blocks, {len(openings)} pairs per arm'
    require(last_utc and all(t<=STOP for t in last_utc), ('minute 50',last_utc))
    truth = json.loads(audit.read_text())
    require(truth['final'] and truth['common_opening_ids']==openings and truth['blocks_complete_by_minute45']==sum(t<=BY45 for t in last_utc), 'Final audit block/time difference')
    report = [f'Common blocks {len(last_utc)}. Common openings {len(openings)}.',
              f'Common blocks completed by minute 45: {sum(t<=BY45 for t in last_utc)}. Last played game per block (UTC):']
    report.extend(f'{i} {t.isoformat()}' for i,t in enumerate(last_utc,1))
    for s in ARMS:
        scores = games[s]
        tally = counters[s]
        n = len(scores)
        gcount = Counter(scores.values())
        wld = [gcount[k] for k in (2,0,1)]
        bins = [0]*5
        for k in openings:
            bins[scores[2*k-1]+scores[2*k]]+=1
        elo = ci(bins)
        canonical = truth['arms'][s]
        require(wld==canonical['A_WLD'] and bins==canonical['penta'], (s,wld,bins))
        if elo is None:
            require(canonical['elo_lower_upper'] is None, (s,elo))
        else:
            require(all(isclose(x,y,rel_tol=0,abs_tol=1e-9) for x,y in zip(elo,canonical['elo_lower_upper'])),(s,'CI',elo,canonical['elo_lower_upper']))
        flags=[list(event[1:-1]) for event in events if event[0]==s and event[-1]=='time loss']
        require(sorted(flags)==sorted(canonical['time_losses']), (s,flags))
        require({e:tally['ending',e] for t,e in tally if t=='ending'}==canonical['endings'],(s,'ending totals'))
        report.append(f'{s} pairs {len(openings)}; A W-L-D {wld}; bins {bins}; Elo/lo/hi {elo}; time losses {len(flags)}.')
        for player in 'AB':
            c,u,h,v,N=(tally[t,player] for t in ('searches','used','holds','role_clock','nodes'))
            p=canonical['players'][player]
            require((c,u,h,v,N)==(p['searches'],p['used_total'],p['hold_searches'],p['clock_total'],p['N_total']), (s,player,'player totals'))
            report.append(f'  {player}: searches {c}, used {u} (mean {u/c:.8f}), nodes {N}, holds {h}, final clock total {v} (mean {v/n:.8f}).')
        for side in 'WB':
            v = tally['color_clock',side]
            require(isclose(v/n,canonical['by_colour_mean_clock'][side], rel_tol=0,abs_tol=1e-9),(s,side,'color end clock'))
            report.append(f'  {side} final clocks sum {v}, mean {v/n:.8f}.')
    manifest_path=out/'input-sha256.tsv'
    manifest_path.write_text('\n'.join(manifest)+'\n')
    with (out/'flag-and-equality.tsv').open('w',newline='') as f:
        writer=csv.writer(f,delimiter='\t',lineterminator='\n')
        writer.writerow(('arm','game','ply','side','player','N','used','clock_before','event'))
        writer.writerows(events)
    report.extend((f'Exact clock exhaustion without flag: {sum(e[-1]=="exactly spent" for e in events)}.',
                   f'Input manifest SHA256 {sha256(manifest_path.read_bytes()).hexdigest()}.',
                   f'All three compact-table outcomes match final audit {sha256(audit.read_bytes()).hexdigest()}.'))
    text='\n'.join(report)+'\n'
    (out/'recount.txt').write_text(text)
    return text


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('published_matches',type=Path)
    p.add_argument('final_audit',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--checkpoint',action='store_true',help='check current complete blocks without a final audit or written outputs')
    args=p.parse_args()
    print(recount(args.published_matches,args.final_audit,args.output,args.checkpoint))
