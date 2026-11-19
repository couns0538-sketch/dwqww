"""Concatenate every played edge's durable games in ascending edge, game and ply order."""
import csv
import subprocess
from selfplay import ROOT, RESULTS, HEADER, NA_HEADER, sha, utc
from compare_stage import compare

def aggregate(edges):
    for stage in edges:
        if not (RESULTS/f'{stage}-cmp.txt').is_file(): raise ValueError(f'edge missing {stage}')
    for build in ('r15d','kF'):
        dest=RESULTS/f'E-{build}'
        dest.mkdir()
        total_records=total_nodes=total_na=total_games=0
        last_game=0
        with (dest/'records.txt').open('xb') as records, (dest/'games.tsv').open('x') as games, (dest/'openings.tsv').open('x') as op, (dest/'no-info.tsv').open('x') as na, (dest/'run.log').open('x') as log, (dest/'sources.tsv').open('x') as sources:
            gw=csv.DictWriter(games,fieldnames=HEADER,delimiter='\t',lineterminator='\n')
            gw.writeheader()
            na.write('\t'.join(NA_HEADER)+'\n')
            op.write('game\tmoves\n')
            print('edge\tgames\trecords\tna_records\tsum_nodes\trecords_sha256',file=sources)
            print('aggregate_build',build,'construction_utc',utc(),file=log)
            for stage in edges:
                arm=RESULTS/f'{stage}-{build}'
                lines=(arm/'run.log').read_text().splitlines()
                if lines[-1]!='status COMPLETE': raise ValueError(f'incomplete {arm}')
                with (arm/'games.tsv').open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
                if len(rows)!=5: raise ValueError(f'expected 5 games in {arm}')
                data=(arm/'records.txt').read_bytes()
                offset=records.tell()
                for row in rows:
                    gid=int(row['book_line'])
                    if gid<=last_game: raise ValueError('nonmonotone edge/game order')
                    last_game=gid
                    row['record_bytes']=str(offset+int(row['record_bytes']))
                    gw.writerow(row)
                if int(rows[-1]['record_bytes'])!=offset+len(data): raise ValueError(f'bad edge end offset {arm}')
                records.write(data)
                for name,target in [('openings.tsv',op),('no-info.tsv',na)]:
                    with (arm/name).open() as f:
                        next(f)
                        target.writelines(f)
                counts=[sum(int(row[k]) for row in rows) for k in ('plies','na','nodes')]
                total_games+=len(rows)
                total_records+=counts[0]
                total_na+=counts[1]
                total_nodes+=counts[2]
                print(stage,len(rows),*counts,sha(arm/'records.txt'),sep='\t',file=sources)
                for line in lines:
                    if 'NNUE v3 loaded' in line or 'NNUE v3 active' in line:
                        print(stage,line,file=log)
            records.flush()
            print('aggregate_order numeric edge, game, ply',file=log)
            print('played_edges',len(edges),file=log)
            print('games',total_games,file=log)
            print('records',total_records,file=log)
            print('na_records',total_na,file=log)
            print('sum_nodes',total_nodes,file=log)
            print('records_sha256',sha(dest/'records.txt'),file=log)
            print('status COMPLETE',file=log)
    return compare('E')
