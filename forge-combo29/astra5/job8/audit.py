"""Audit paired Fastchess PGNs against the complete match output."""
import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
import re

STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TAG = re.compile(r'^\[(\w+) "((?:[^"\\]|\\.)*)"\]$')
RESULTS = ('1-0', '0-1', '1/2-1/2')
DRAWS = {'Draw by 3-fold repetition','Draw by fifty moves rule','Draw by insufficient mating material','Draw by stalemate'}
FINISHED = re.compile(r'^Finished game (\d+) \((.+?) vs (.+?)\): (\S+) \{(.*)\}$', re.M)

def read_pgn(p):
    games=[]
    def finish(tags,lines):
        text=' '.join(lines)
        if not text:
            return
        comments=re.findall(r'\{([^}]*)\}',text)
        clean=re.sub(r'\{[^}]*\}', ' ',text)
        assert not any(s in clean for s in ('{','}','(',')')),'Unexpected nested comments or RAV'
        body=re.sub(r'(?<![A-Za-z0-9])\d+\.{1,3}', ' ',clean).split()
        if not body or body[-1] not in RESULTS:
            raise ValueError(f'Incomplete/unscored PGN at round {tags.get("Round")}')
        result=body.pop()
        assert result == tags['Result']
        assert len(body)==int(tags['PlyCount']),(tags['Round'],len(body),tags['PlyCount'])
        games.append(dict(tags=tags,fen=tags.get('FEN',STARTPOS),moves=body,last_comment=comments[-1] if comments else ''))
    tags={};lines=[]
    with p.open() as src:
        for raw in src:
            line=raw.strip(); m=TAG.fullmatch(line)
            if m:
                if lines:
                    finish(tags,lines); tags={}; lines=[]
                tags[m[1]]=m[2]
            elif line:
                lines.append(line)
    if tags or lines: finish(tags,lines)
    return games

def reason_group(reason):
    if reason in ('White mates','Black mates'): return 'mate'
    if reason in DRAWS: return 'draw_rule'
    if reason=='Draw by adjudication': return 'limit_300'
    return 'other'

def audit(args):
    pgn_games=read_pgn(args.pgn)
    text=args.match_out.read_text()
    fast={}
    for game_id,white,black,result,reason in FINISHED.findall(text):
        assert int(game_id) not in fast, game_id
        fast[int(game_id)]=white,black,result,reason
    # Round is this Fastchess version's 1-based pairing id, shared between color reversals.
    by_round=defaultdict(list)
    for g in pgn_games: by_round[int(g['tags']['Round'])].append(g)
    values=[]; marks=Counter(); reasons=Counter(); reason_names=Counter()
    first_bad=None; paired=0; orphan=[]; detail=[]; errors=[]; seen_ids=set()
    for rid, pair in sorted(by_round.items()):
        if len(pair)!=2:
            assert len(pair)==1,(rid,len(pair))
            orphan.append(rid); continue
        paired+=1; marks_pair=[]; per_game=[]
        assert pair[0]['tags']['White']==pair[1]['tags']['Black'] and pair[1]['tags']['White']==pair[0]['tags']['Black'],rid
        for g in pair:
            t=g['tags'];white=t['White'];black=t['Black'];result=t['Result']
            assert args.engine_a in (white,black)
            candidate_won=(result=='1-0' and white==args.engine_a) or (result=='0-1' and black==args.engine_a)
            mark='D' if result=='1/2-1/2' else ('W' if candidate_won else 'L')
            marks_pair.append(mark); marks[mark]+=1
            candidates=[gid for gid in (2*rid-1,2*rid) if gid in fast and fast[gid][:3]==(white,black,result)]
            assert len(candidates)==1,(rid,t['White'],result,candidates)
            gid=candidates[0]; assert gid not in seen_ids; seen_ids.add(gid)
            reason=fast[gid][3]
            assert g['last_comment'].endswith(reason),(gid,g['last_comment'],reason)
            cls=reason_group(reason)
            if cls=='limit_300':
                assert t['Termination']=='adjudication' and t['Result']=='1/2-1/2' and int(t['PlyCount'])>=599,(gid,t)
            reasons[cls]+=1;reason_names[reason]+=1
            per_game.append((gid,mark))
        units=sum({'W':2,'D':1,'L':0}[q] for q in marks_pair)
        values.append(units)
        equal_moves=pair[0]['moves']==pair[1]['moves']
        equal_fens=pair[0]['fen']==pair[1]['fen']
        if not equal_fens: errors.append(f'Opening FEN differs in round {rid}.')
        if args.k8 and first_bad is None and (not equal_moves or not equal_fens or units!=2):
            first_bad=(rid,pair,units)
        per_game.sort()
        detail.append([rid,per_game[0][0],per_game[0][1],per_game[1][0],per_game[1][1],units/2,'yes' if equal_fens else 'no','yes' if equal_moves else 'no'])
    bins=[values.count(i) for i in range(5)]
    stats=tuple(marks[m] for m in 'WLD')
    expected=args.want
    status='complete' if len(pgn_games)==expected and 2*paired==expected and len(fast)==expected else 'incomplete'
    if status=='complete':
        assert sorted(by_round)==list(range(1,1+expected//2))
        assert seen_ids==set(range(1,expected+1))
        assert not orphan
        suites=re.findall(r'^Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+),',text,re.M)
        pentas=re.findall(r'^Ptnml\(0-2\): \[([\d, ]+)\]',text,re.M)
        assert suites and pentas,(bool(suites),bool(pentas))
        assert tuple(map(int,suites[-1]))==(expected,*stats),(suites[-1],stats)
        assert [int(n) for n in pentas[-1].split(',')]==bins,(pentas[-1],bins)
    args.out.mkdir(exist_ok=True,parents=True)
    with (args.out/'pairs.tsv').open('w') as out:
        table=csv.writer(out,delimiter='\t',lineterminator='\n');table.writerow(['round','first_game','A_result_first','second_game','A_result_second','A_points','opening_equal','move_list_equal']);table.writerows(detail)
    lines=[f'status {status}',f'requested games {expected}',f'PGN games {len(pgn_games)}',f'fastchess finished game records {len(fast)}',
           f'complete opening pairs {paired}',f'scored games {2*paired}',f'PGN rounds excluded (lone games) {orphan}',f'A W-L-D {" ".join(map(str,stats))}',
           'pentanomial '+ ' '.join(map(str,bins)),f'all paired opening FENs equal {not errors}',f'identical move lists {sum(r[-1]=="yes" for r in detail)}/{paired}',
           'endings '+' '.join(f'{k}={reasons[k]}' for k in ('mate','draw_rule','limit_300','other')),*[f'reason {k} = {v}' for k,v in sorted(reason_names.items())]]
    if args.k8:
        lines.append(f'K8 exact gate {"PASS" if first_bad is None and status=="complete" and not errors else "FAIL"}')
        if first_bad:
            rid,pair,units=first_bad;lines.append(f'first discrepancy round {rid} A pair points {units/2:g}')
            for idx,g in enumerate(pair,1):
                t=g['tags'];lines.extend([f'game {idx} {t["White"]} vs {t["Black"]} {t["Result"]} opening FEN {g["fen"]}', 'moves '+' '.join(g['moves'])])
    lines.extend(errors[:5])
    result='\n'.join(lines)+'\n'
    (args.out/'pgn-audit.txt').write_text(result)
    print(result,end='')
    return 1 if errors or args.k8 and first_bad is not None else 0

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pgn',type=Path);parser.add_argument('match_out',type=Path)
    parser.add_argument('--engine-a',required=True);parser.add_argument('--want',type=int,required=True)
    parser.add_argument('--k8',action='store_true');parser.add_argument('--out',type=Path,required=True)
    raise SystemExit(audit(parser.parse_args()))
