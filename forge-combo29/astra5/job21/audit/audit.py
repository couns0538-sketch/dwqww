"""Reconcile Fastchess clocks, game endings and only complete pre-cutoff opening pairs."""
import argparse
import csv
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import re
from stats_seed import evaluate

STARTPOS="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TAGS=re.compile(r'^\[(\w+) "((?:[^"\\]|\\.)*)"\]$')
FINISHED=re.compile(r'^Finished game (\d+) \((.+?) vs (.+?)\): (\S+) \{(.*)\}$',re.M)
STARTED=re.compile(r'^Started game (\d+) of (\d+) \((.+?) vs (.+?)\)$',re.M)
DRAW_RULE={'Draw by insufficient mating material','Draw by 3-fold repetition','Draw by fifty moves rule','Draw by stalemate'}
RESULTS={'1-0','0-1','1/2-1/2'}
CAUSES=('mate','draw_rule','limit_300','time_A_loss','time_B_loss','other')

def read(path,permit_truncation):
    txt=path.read_text()
    records=re.split(r'(?=^\[Event )',txt,flags=re.M)
    games=[];partials=[]
    for ii,rec in enumerate(records):
        if not rec.strip():continue
        tags={};body=[]
        for s in rec.splitlines():
            m=TAGS.fullmatch(s.strip())
            if m:tags[m[1]]=m[2]
            elif s.strip():body.append(s.strip())
        txt=' '.join(body)
        comments=re.findall(r'\{([^}]*)\}',txt)
        clean=re.sub(r'\{[^}]*\}', ' ',txt)
        clean=re.sub(r'(?<![A-Za-z0-9])\d+\.{1,3}', ' ',clean).split()
        if not clean or clean[-1] not in RESULTS:
            if not permit_truncation or ii!=len(records)-1:raise ValueError('unscored PGN before last record '+str(tags))
            partials.append((tags.get('Round','?'),tags.get('White','?'),tags.get('Black','?')))
            continue
        score=clean.pop()
        assert tags['Result']==score and int(tags['PlyCount'])==len(clean),(tags,len(clean),score)
        assert tags['White']!=tags['Black']
        end=datetime.strptime(tags['GameEndTime'],'%Y-%m-%dT%H:%M:%S %z').astimezone(timezone.utc)
        games.append(dict(tags=tags,fen=tags.get('FEN',STARTPOS),moves=clean,last_comment=comments[-1] if comments else '',end=end))
    return games,partials

def clock_reason(result,reason,white,black,engine_a):
    m=re.fullmatch(r'(White|Black) loses on time \(\d+ms overrun\)',reason)
    if m:
        assert result==('0-1' if m[1]=='White' else '1-0'),(result,reason,white,black)
        loser=white if m[1]=='White' else black
        return 'time_A_loss' if loser==engine_a else 'time_B_loss'
    if reason in ('White mates','Black mates'):
        assert result==('1-0' if reason=='White mates' else '0-1')
        return 'mate'
    if reason in DRAW_RULE:
        assert result=='1/2-1/2'
        return 'draw_rule'
    if reason=='Draw by adjudication':
        assert result=='1/2-1/2'
        return 'limit_300'
    return 'other'

def mark(result,white,black,a):
    assert a in (white,black) and result in RESULTS
    if result=='1/2-1/2':return 'D'
    return 'W' if (result=='1-0')==(white==a) else 'L'

def spans(nums):
    out=[];lo=None;hi=None
    for n in sorted(set(nums)):
        if lo is None or n!=hi+1:
            if lo is not None:out.append(str(lo) if lo==hi else f'{lo}–{hi}')
            lo=hi=n
        else:hi=n
    if lo is not None:out.append(str(lo) if lo==hi else f'{lo}–{hi}')
    return ', '.join(out) if out else 'none'

def dump_tsv(path,fields,rows):
    with path.open('w') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(fields);w.writerows(rows)

def run(args):
    pgn=args.pgn;raw=args.match_out.read_text();meta=args.meta.read_text()
    cutoff=datetime.fromisoformat(args.deadline.replace('Z','+00:00'))
    interrupted='status incomplete' in meta
    games,partial=read(pgn,interrupted)
    starts={int(i):(w,b) for i,planned,w,b in STARTED.findall(raw)}
    parsed_finish=FINISHED.findall(raw);finished={int(i):(w,b,r,reason) for i,w,b,r,reason in parsed_finish}
    assert len(finished)==len(parsed_finish),'duplicate runner finished record'
    finished_real={i:r for i,r in finished.items() if r[2] in RESULTS}
    unmapped=[]
    by_gid={}; by_round=defaultdict(list); details=[]; causes_all=Counter();causes_eligible=Counter()
    raw_causes=Counter(clock_reason(r[2],r[3],r[0],r[1],args.engine_a) for r in finished_real.values())
    for g in games:
        t=g['tags'];rnd=int(t['Round']);w,b,r=t['White'],t['Black'],t['Result']
        gids=[i for i in (2*rnd-1,2*rnd) if (finished.get(i,())[:2] or starts.get(i,()))==(w,b)]
        if not gids:
            unmapped.append((rnd,w,b));continue
        assert len(gids)==1
        i=gids[0];assert i not in by_gid
        g['gid']=i;by_gid[i]=g;g['mark']=mark(r,w,b,args.engine_a)
        if i not in finished_real:
            g['cause']='unconfirmed';g['reason']='missing scored Finished game line'
            continue
        rw,rb,rr,reason=finished_real[i];assert (w,b,r)==(rw,rb,rr),(i,t,finished_real[i])
        cause=clock_reason(r,reason,w,b,args.engine_a)
        if cause.startswith('time_'):
            assert t['Termination']=='time forfeit',(i,t,reason)
            if g['moves']:assert g['last_comment'].endswith(reason),(i,g['last_comment'],reason)
        else:
            assert t['Termination']!='time forfeit',(i,reason,t)
            assert g['last_comment'].endswith(reason),(i,g['last_comment'],reason)
        if cause=='limit_300': assert t['Termination']=='adjudication' and int(t['PlyCount'])>=599
        g['cause']=cause;g['reason']=reason
        causes_all[cause]+=1
        if g['end']<cutoff:by_round[rnd].append(g);causes_eligible[cause]+=1
    paired=[];singletons=[];pair_detail=[];scored=set();same=0;vals=[];unit={'L':0,'D':1,'W':2}
    for rnd,games2 in sorted(by_round.items()):
        assert len(games2)<=2
        if len(games2)!=2:
            singletons.append(rnd);continue
        a,b=sorted(games2,key=lambda x:x['gid'])
        assert a['gid']==2*rnd-1 and b['gid']==2*rnd,(rnd,a['gid'],b['gid'])
        assert a['fen']==b['fen'] and (a['tags']['White'],a['tags']['Black'])==(b['tags']['Black'],b['tags']['White'])
        pts=(unit[a['mark']]+unit[b['mark']])/2.0
        eq=a['moves']==b['moves'];same+=eq;vals.append(pts/2)
        scored.update([a['gid'],b['gid']]);paired.extend([a,b])
        pair_detail.append([rnd,a['gid'],a['mark'],b['gid'],b['mark'],pts,'yes','yes' if eq else 'no'])
    why={i:'retained' if i in scored else 'missing runner result' if i not in finished_real else 'end timestamp at/after cutoff' if g['end']>=cutoff else 'no eligible color reverse' for i,g in by_gid.items()}
    for i,g in sorted(by_gid.items()):
        t=g['tags'];details.append([i,t['Round'],t['White'],t['Black'],t['Result'],g['mark'],g['end'].isoformat(),g['cause'],g['reason'],why[i]])
    complete=(not interrupted and len(paired)==args.want and len(games)==args.want and len(finished_real)==args.want and not partial and not unmapped)
    if not complete and not interrupted and len(games)<args.want: interrupted=True
    counts=Counter(g['mark'] for g in paired);ends=Counter(g['cause'] for g in paired);names=Counter(g['reason'] for g in paired);bins=[vals.count(i/4) for i in range(5)]
    assert sum(ends.values())==sum(counts.values())==2*sum(bins)
    summary_matches=re.findall(r'^Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+),',raw,re.M)
    penta_matches=re.findall(r'^Ptnml\(0-2\): \[([\d, ]+)\]',raw,re.M)
    final_score=tuple(map(int,summary_matches[-1])) if summary_matches else None
    final_bins=[int(x) for x in penta_matches[-1].split(',')] if penta_matches else None
    if complete:
        assert final_score==(args.want,counts['W'],counts['L'],counts['D']) and final_bins==bins,(final_score,final_bins,bins)
        assert set(by_gid)==set(finished_real)==set(starts)==set(range(1,args.want+1))
    args.out.mkdir(parents=True,exist_ok=True)
    dump_tsv(args.out/'pairs.tsv',['round','first_game','A_result_first','second_game','A_result_second','A_points','opening_equal','move_list_equal'],pair_detail)
    dump_tsv(args.out/'games.tsv',['game_id','round','white','black','result','A_result','utc_end','cause','runner_reason','status'],details)
    for title,vals_ in [('raw PGN',causes_all),('eligible PGN',causes_eligible),('complete pairs',ends),('scored runner',raw_causes)]: assert min([v for v in vals_.values()]+[0])>=0
    report=[f'status {"complete" if complete else "incomplete"}',f'requested games {args.want}',f'PGN games {len(games)}',f'fastchess finished game records {len(finished_real)}',f'complete opening pairs {len(pair_detail)}',f'scored games {len(paired)}',f'PGN rounds excluded (lone games) {singletons}',f'A W-L-D {counts["W"]} {counts["L"]} {counts["D"]}','pentanomial '+' '.join(map(str,bins)),
      'all paired opening FENs equal True',f'identical move lists {same}/{len(pair_detail)}','endings '+' '.join(f'{k}={ends[k]}' for k in CAUSES),*[f'reason {k} = {v}' for k,v in sorted(names.items())]]
    if vals:
        e,lo,hi=evaluate(vals);report+= [f'paired Elo {e:+.8f} [{lo:+.8f}, {hi:+.8f}]']
    covered=set(by_gid); scored_out=set(finished_real)
    coverage=[f'Deadline {args.deadline}. Only pairs with both PGN results and agreeing scored runner lines and both GameEndTime timestamps strictly before this UTC deadline are retained.',
        f'PGN complete records {len(games)}. All runner Started-game IDs ({len(starts)}): {spans(starts)}.',
        f'Runner Finished-game IDs with scored result ({len(scored_out)}): {spans(scored_out)}.',
        f'Runner Finished-game IDs that were interrupted/unscored: {spans(set(finished)-scored_out)}.',
        f'PGN mapped game IDs ({len(covered)}): {spans(covered)}. Unmapped PGN records {unmapped}. Trailing partial PGN record {partial}.',
        f'Scored runner IDs without a PGN: {spans(scored_out-covered)}. PGN IDs without agreeing scored runner line: {spans(covered-scored_out)}.',
        f'Games started with no scored runner finish: {spans(set(starts)-scored_out)}. Never started: {spans(set(range(1,args.want+1))-set(starts))}.',
        f'Raw PGN game IDs excluded from pair totals: {spans(covered-scored)}. Single-eligible-game rounds: {spans(singletons)}. PGN games at/after cutoff: {spans(i for i,g in by_gid.items() if g["end"]>=cutoff)}.',
        f'Complete pre-cutoff opening pairs {len(pair_detail)}. Scored game IDs ({len(scored)}): {spans(scored)}.',
        f'All scored runner records time losses A/B {raw_causes["time_A_loss"]}/{raw_causes["time_B_loss"]}; all mapped PGNs {causes_all["time_A_loss"]}/{causes_all["time_B_loss"]}; retained games {ends["time_A_loss"]}/{ends["time_B_loss"]}.',
        f'Last runner footer games/W/L/D: {final_score}; penta {final_bins}; retained-pair W/L/D ({counts["W"]}, {counts["L"]}, {counts["D"]}) and penta {bins}.']
    if by_gid:coverage.append(f'Latest recorded completed PGN GameEndTime in UTC: {max(g["end"] for g in by_gid.values()).isoformat()}.')
    for s in meta.splitlines():
        if 'SIG' in s or 'status ' in s or 'fastchess launch' in s or ' start' in s or ' end' in s:coverage.append('meta '+s)
    (args.out/'pgn-audit.txt').write_text('\n'.join(report)+'\n')
    (args.out/'coverage.txt').write_text('\n'.join(coverage)+'\n')
    print('\n'.join(report+coverage))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pgn',type=Path,required=True);p.add_argument('--match-out',type=Path,required=True);p.add_argument('--meta',type=Path,required=True)
    p.add_argument('--want',type=int,required=True);p.add_argument('--engine-a',required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--deadline',default='2026-11-19T02:22:00Z')
    run(p.parse_args())
