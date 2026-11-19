"""Recompute opening-paired Job 28 contrasts from compact game outcomes."""
import argparse
import csv
from hashlib import sha256
import io
from math import isclose, sqrt
from pathlib import Path
from statistics import NormalDist


def read_games(path):
    return list(csv.DictReader(io.StringIO(path.read_text()), delimiter='\t'))


def indexed_outcomes(archives, roles):
    # A block qualifies only if all three of its arms finished both colors for every opening.
    ledger = {role: {} for role in roles}
    source_hashes = []
    for block in range(1,10):
        first = (block - 1) * 50 + 1
        last = min(434, block * 50)
        want_ids = set(range(2*first - 1,2*last + 1))
        data = {}
        for role in roles:
            path = archives / f'block{block:03}' / role / 'games.tsv'
            if not path.is_file():
                break
            raw = read_games(path)
            by_id = {int(row['game']): row for row in raw}
            if len(raw) != len(by_id) or not by_id.keys() <= want_ids:
                raise ValueError(f'duplicate or out-of-block game in {path}')
            if by_id.keys() != want_ids:
                break
            data[role]=(path,by_id)
        if len(data)!=3:
            continue
        for role,(path,by_id) in data.items():
            relative=f'{archives.parent.name}/matches/{path.relative_to(archives)}'
            source_hashes.append((relative,sha256(path.read_bytes()).hexdigest()))
            for k in range(first,last+1):
                total=0.0
                for j,white,black in ((2*k-1,'A','B'),(2*k,'B','A')):
                    g=by_id[j]
                    if (int(g['opening']),g['white'],g['black']) != (k,white,black):
                        raise ValueError(f'opening/color assignment failed in {path}, game {j}')
                    if g['result']=='1/2-1/2':
                        total+=.5
                    else:
                        winner={'1-0':white,'0-1':black}[g['result']]
                        total+=winner=='A'
                ledger[role][k]=total
    return ledger,source_hashes


def write_tsv(path,columns,rows):
    with path.open('w',newline='') as out:
        w=csv.writer(out,delimiter='\t',lineterminator='\n')
        w.writerow(columns)
        w.writerows(rows)


def stats(label,xy,ddof):
    # Use integer/half-integer sufficient statistics before the final floating point divisions.
    n=len(xy)
    if n<=ddof:
        raise ValueError(f'{label} sample size {n} too small')
    sumx=sum(x for x,y in xy)
    sumy=sum(y for x,y in xy)
    mean=(sumx-sumy)/n
    varx=(sum(x*x for x,y in xy)-sumx*sumx/n)/(n-ddof)
    vary=(sum(y*y for x,y in xy)-sumy*sumy/n)/(n-ddof)
    cov=(sum(x*y for x,y in xy)-sumx*sumy/n)/(n-ddof)
    vard=(sum((x-y)**2 for x,y in xy)-((sumx-sumy)**2)/n)/(n-ddof)
    if not isclose(vard,varx+vary-2*cov,rel_tol=0,abs_tol=1e-12):
        raise ValueError(f'{label} covariance identity failed')
    z=NormalDist().inv_cdf(.975)
    h=z*sqrt(vard/n)
    independent=z*sqrt((varx+vary)/n)
    return (label,n,ddof,sumx/n,sumy/n,mean,sqrt(varx),sqrt(vary),sqrt(vard),cov,
            mean-h,mean+h,2*h,mean-independent,mean+independent,2*independent,
            2*(independent-h),100*(1-h/independent) if independent else None)


def run(prior,now,out,compare_to):
    old,old_hash=indexed_outcomes(prior,('M1','M2','M3'))
    new,new_hash=indexed_outcomes(now,('M4','M5','M6'))
    strength={**old,**new}
    detail=[]
    summary=[]
    for a,b in [('M4','M1'),('M5','M6')]:
        keys=sorted(strength[a].keys() & strength[b].keys())
        xy=[]
        for k in keys:
            x,y=strength[a][k],strength[b][k]
            xy.append((x,y))
            detail.append((a+'-'+b,k,x,y,x-y))
        for ddof in (1,0):
            summary.append(stats(a+'-'+b,xy,ddof))
    header='comparison n ddof mean_left mean_right mean_difference sd_left sd_right sd_difference covariance ci_low ci_high full_paired_width separate_low separate_high full_separate_width width_reduction width_reduction_pct'.split()
    write_tsv(out/'pair-contrast-points.tsv',('comparison','opening','left_A_points','right_A_points','difference'),detail)
    write_tsv(out/'pair-contrast-statistics.tsv',header,summary)
    write_tsv(out/'pair-contrast-inputs.tsv',('path','sha256'),old_hash+new_hash)
    print('Opening units are A pair points out of 2. Independent and paired widths are full two-sided normal 95% widths.')
    print('Primary ddof=1 uses sample SD. Secondary ddof=0 shows population SD, consistent with Job 21/27 per-arm Elo.')
    for row in summary:
        print(dict(zip(header,row)))

    if compare_to:
        comp_by_key = {r['comparison']:r for r in read_games(compare_to/'comparisons.tsv')}
        prior_by_id = {int(r['opening']):r for r in read_games(compare_to/'per_opening.tsv')}
        mapping = {'n':'n','mean_difference':'mean_delta','sd_difference':'sd_delta','ci_low':'ci_low',
                   'ci_high':'ci_high','full_paired_width':'paired_width','full_separate_width':'independent_width',
                   'width_reduction':'width_reduction','width_reduction_pct':'narrowing_pct'}
        for row in summary:
            if row[2]!=1:continue
            local=dict(zip(header,row))
            known=comp_by_key[row[0]]
            for key,other_key in mapping.items():
                if not isclose(local[key],float(known[other_key]),rel_tol=0,abs_tol=1e-9):
                    raise ValueError(f'{row[0]}: {key} disagrees with primary: {local[key]} != {known[other_key]}')
        for label,k,x,y,delta in detail:
            left,right=label.split('-')
            r=prior_by_id[k]
            seen=tuple(float(r[t]) for t in (left+'_A_pair_points',right+'_A_pair_points',left+'_minus_'+right))
            if (x,y,delta)!=seen:
                raise ValueError(f'{label} {k}: points disagree with primary')
        if len(detail)!=len(prior_by_id)*2:
            raise ValueError('opening counts disagree with primary')
        print(f'PASS: primary results match for all {len(prior_by_id)} opening IDs, raw pair points, '
              'sample SD, confidence bounds, separate/paired widths and percentage reductions.')



if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('published_job27_matches',type=Path)
    p.add_argument('published_job28_matches',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--compare-to',type=Path,help='independently produced final comparison tables')
    a=p.parse_args()
    run(a.published_job27_matches,a.published_job28_matches,a.output,a.compare_to)
