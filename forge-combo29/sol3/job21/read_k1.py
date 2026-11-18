#!/usr/bin/env python3
"""Read the Job 20 S2 raw UCI evidence for the independent Job 21 K1 gate."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys


HARD_CAP = 8000
BESTMOVE = re.compile(r'bestmove ([a-h][1-8][a-h][1-8][qrbn]?|0000)(?: ponder [a-h][1-8][a-h][1-8][qrbn]?)?$')
FINAL = re.compile(r'info string softnodes nodes ([0-9]+)$')
SHADOW = re.compile(r'info string shadow evals ([0-9]+) differ ([0-9]+)$')
REFUSAL = re.compile(r'unknown option|invalid value|invalid FEN|\bERROR\b',re.I)


def digest(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file,'sha256').hexdigest()


def parse_info(number, line):
    tokens=line.split()
    nodes,elapsed=(tokens.index(key) for key in ('nodes','time'))
    return {'line_number':number,'depth':int(tokens[2]),'nodes':int(tokens[nodes+1]),
            'time_ms':int(tokens[elapsed+1]),'text':line}


def parse_stdout(path):
    ready=0
    game=0
    in_game=0
    opened=False
    active=None
    depth_infos=[]
    final=None
    shadow=None
    results=[]
    with path.open(encoding='ascii') as file:
        for number,raw in enumerate(file,1):
            line=raw.rstrip('\n')
            if REFUSAL.search(line):
                raise ValueError(f'stdout line {number}: {line}')
            if line=='uciok':
                if opened:
                    raise ValueError(f'duplicate uciok at line {number}')
                opened=True
            elif line.startswith('info string NNUE v3 active:'):
                if not opened or ready or active or 'hidden 768' not in line or 'checksum 30ab43b4ba5db5f3' not in line:
                    raise ValueError(f'invalid active net at line {number}')
                active=line
            elif line=='readyok':
                if depth_infos or final or shadow or not active or (game and not in_game):
                    raise ValueError(f'misplaced game/setup barrier at line {number}')
                ready+=1
                if ready>1:
                    game+=1
                    in_game=0
            elif line.startswith('info depth '):
                if not game or final or shadow:
                    raise ValueError(f'depth summary outside an open search at line {number}')
                depth_infos.append(parse_info(number,line))
            elif (count:=FINAL.fullmatch(line)) is not None:
                if not depth_infos or final or shadow:
                    raise ValueError(f'misplaced or duplicate final node count at line {number}')
                final=(number,int(count[1]),line)
            elif (counter:=SHADOW.fullmatch(line)) is not None:
                if not final or shadow:
                    raise ValueError(f'misplaced or duplicate shadow summary at line {number}')
                shadow=(int(counter[1]),int(counter[2]))
            elif line.startswith('bestmove '):
                match=BESTMOVE.fullmatch(line)
                if match is None or not depth_infos or not final or shadow is None:
                    raise ValueError(f'incomplete search at line {number}')
                results.append({'search':len(results)+1,'game':game,'ply':in_game,'last_info':depth_infos[-1],
                                'last_three_info':depth_infos[-3:],'final_nodes':final[1],
                                'final_line':final[0],'final_text':final[2],'bestmove':match[1],
                                'bestmove_line':number,'bestmove_text':line,
                                'shadow_evals':shadow[0],'shadow_differ':shadow[1]})
                in_game+=1
                depth_infos.clear()
                final=shadow=None
    if depth_infos or final or shadow or not active or not in_game:
        raise ValueError('unterminated or empty last game')
    return results, {'games':game,'readyok':ready,'net_active':active}


def check_commands(cmd, rows, fens):
    lines=cmd.read_text(encoding='ascii').splitlines()
    first=lines.index('ucinewgame')
    if lines[0]!='uci' or lines[first-1]!='isready' or lines[-1]!='quit':
        raise ValueError('missing UCI setup or quit in command transcript')
    for option in ('setoption name Threads value 1','setoption name Hash value 16','setoption name NNUEArch value true'):
        if option not in lines[:first]:
            raise ValueError(f'missing setting {option!r}')
    it=iter(enumerate(lines[first:-1],first+1))
    root=None
    previous=[]
    for row in rows:
        number,line=next(it)
        if row['ply']==0:
            if line!='ucinewgame' or next(it)[1]!='isready':
                raise ValueError(f'missing commanded game reset at line {number}')
            number,line=next(it)
            root=None
            previous=[]
        tokens=line.split()
        if tokens[:2]!=['position','fen'] or len(tokens)<9 or tokens[8]!='moves':
            raise ValueError(f'missing FEN history at command line {number}')
        fen=' '.join(tokens[2:8]); moves=tokens[9:]
        if root is None:
            root=fen
        if root!=fen or previous!=moves or len(moves)!=row['ply']:
            raise ValueError(f'root or played move history disagrees at command line {number}')
        if fens is not None and fen!=fens[19+row['game']]:
            raise ValueError(f'game does not start at required Job 19 fixture row {20+row["game"]}')
        go,command=next(it)
        if command!='go softnodes 2000':
            raise ValueError(f'wrong budget at command line {go}')
        row.update({'fixture_position':20+row['game'],'root_fen':root,
                    'position_command_line':number,'go_command_line':go})
        previous=[*previous,row['bestmove']]
    if next(it,None) is not None:
        raise ValueError('trailing unconsumed game commands')


def write_rows(output,rows):
    labels=('search','game','ply','fixture_position','root_fen','position_command_line','go_command_line',
            'bestmove','bestmove_line','final_nodes','final_line','last_depth','last_nodes','last_time_ms',
            'last_info_line','previous_nodes','prior_nodes','unreported_nodes','shadow_evals','shadow_differ')
    with output.open('x',encoding='ascii',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=labels,delimiter='\t',lineterminator='\n')
        writer.writeheader()
        for row in rows:
            last=row['last_info']
            rec={k:row[k] for k in labels if k in row}
            rec.update({'last_depth':last['depth'],'last_nodes':last['nodes'],'last_time_ms':last['time_ms'],
                        'last_info_line':last['line_number'],
                        'unreported_nodes':row['final_nodes']-last['nodes']})
            for column,offset in [('previous_nodes',2),('prior_nodes',3)]:
                if len(row['last_three_info'])>=offset:
                    rec[column]=row['last_three_info'][-offset]['nodes']
            writer.writerow(rec)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stdout',type=Path)
    parser.add_argument('--commands',type=Path)
    parser.add_argument('--fixture',type=Path,help='Job 19 W1 FENs, optional exact start-order check')
    parser.add_argument('--rows',type=Path,help='optional independent TSV with the last three info node counts')
    args=parser.parse_args()
    if args.fixture is not None and args.commands is None:
        parser.error('--fixture requires --commands')
    rows,meta=parse_stdout(args.stdout)
    fens=args.fixture.read_text().splitlines() if args.fixture is not None else None
    if args.commands is not None:
        check_commands(args.commands,rows,fens)
    if args.rows is not None:
        write_rows(args.rows,rows)
    affected=[r for r in rows if r['final_nodes']>r['last_info']['nodes']]
    under=[r for r in affected if r['final_nodes']<HARD_CAP]
    above=[r for r in rows if r['final_nodes']>HARD_CAP]
    backwards=[r for r in rows if r['final_nodes']<r['last_info']['nodes']]
    unflagged=[r for r in rows if r['final_nodes']>=HARD_CAP and r['final_nodes']==r['last_info']['nodes']]
    final=sum(r['final_nodes'] for r in rows)
    info=sum(r['last_info']['nodes'] for r in rows)
    gate=(len(rows),final,info,len(affected))==(933,3920946,3028475,131) and not under and not backwards
    result={'raw_stdout':str(args.stdout),'stdout_sha256':digest(args.stdout),**meta,
            'commands_sha256':digest(args.commands) if args.commands is not None else None,
            'fixture_sha256':digest(args.fixture) if args.fixture is not None else None,
            'searches':len(rows),'final_softnodes_sum':final,'last_info_nodes_sum':info,
            'excess_searches':len(affected),'unreported_nodes':final-info,
            'unreported_node_share':(final-info)/final,
            'minimum_final_count_with_excess':min((r['final_nodes'] for r in affected),default=None),
            'excess_below_cap':len(under),'final_above_cap':len(above),'final_below_last_info':len(backwards),
            'cap_without_excess':len(unflagged),
            'first_excess':affected[0] if affected else None,
            'first_final_above_cap':above[0] if above else None,
            'first_excess_below_cap':under[0] if under else None,
            'first_backwards':backwards[0] if backwards else None,
            'shadow_evals':sum(r['shadow_evals'] for r in rows),'shadow_differ':sum(r['shadow_differ'] for r in rows),
            'known_answer_pass':gate}
    print(json.dumps(result,indent=2))
    return int(not gate)


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (IndexError,KeyError,StopIteration,OSError,ValueError) as error:
        print(f'K1 archive readback failed: {error}',file=sys.stderr)
        raise SystemExit(1) from error
