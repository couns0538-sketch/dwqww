"""Independently replay Job 27 paired node-clock games, including raw protocol evidence."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import chess
from stats_seed import evaluate

BOOK_SHA='271cea0cd131935998b72aeee5e6bda336f8bea8f48bcf060088895f1765b21c'
NC_SHA='9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3'
from functools import lru_cache
@lru_cache(maxsize=10)
def binary_hash(exe): return sha256(Path(exe).read_bytes()).hexdigest()
CUTOFF = datetime(2026, 11, 19, 19, 57, 59, tzinfo=timezone.utc)
STOP = datetime(2026, 11, 19, 20, 2, 59, tzinfo=timezone.utc)
OPTIONS = (
    'Threads 1|Hash 16|OwnBook false|MateAlphaGuard true|LmrQuietBase 93|'
    'LmrQuietDivisor 205|LmrNoisyBase 13|LmrNoisyDivisor 333|LmrHistoryDivisor 5643|'
    'NullMoveBase 5|LmpBase 8|HistoryPruneMultiplier 2220|HistoryBonusQuadratic 24|'
    'HistoryBonusLinear 54|HistoryBonusMax 2212|SingularDepth 6|IirDepth 2|'
    'NonPawnCorrection true|CuckooRep true|HistRework 2|TtPruneV2 true|CorrHistV2 true'
).split('|')


def table(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def table_out(path, fields, records):
    with path.open('w', newline='') as stream:
        writer=csv.writer(stream,delimiter='\t',lineterminator='\n')
        writer.writerow(fields); writer.writerows(records)


def check(ok, detail):
    if not ok:
        raise ValueError(str(detail))


def time(s):
    return datetime.fromisoformat(s.replace('Z','+00:00'))


def rule(b):
    if b.is_checkmate():return 'checkmate'
    if b.is_stalemate():return 'stalemate'
    if b.is_insufficient_material():return 'insufficient'
    if b.can_claim_threefold_repetition():return 'threefold'
    if b.can_claim_fifty_moves():return 'fifty'
    return None


def board_end(label):
    if label in ('time','cap','checkmate','stalemate'):return label
    low=label.lower()
    if 'mate'==low:return 'checkmate'
    if 'repet' in low or 'threefold' in low:return 'threefold'
    if 'fifty' in low or '50' in low:return 'fifty'
    if 'insuff' in low or low=='material':return 'insufficient'
    raise ValueError(f'unrecognized ending {label}')


def score2(rec):
    if rec['result']=='1/2-1/2':return 1
    check(rec['result'] in ('1-0','0-1'), rec)
    return 2*int((rec['white']=='A') == (rec['result']=='1-0'))


def read_wire(path):
    packets=[]; setup={'W':[],'B':[]}; traffic={'W':[],'B':[]}
    for number,raw in enumerate(path.read_text().splitlines(),1):
        check(not re.search('unknown option|invalid value|ERROR', raw,re.I),(path,number,raw))
        m=re.match(r'^([WB])\s*([<>])\s*(.*)$',raw)
        if not m: continue
        side,sign,text=m.groups()
        if sign=='>' and text.startswith('position '):
            packets.append(dict(s=side,pos=text,go=None,soft=[],moves=[],hold=[]))
        elif sign=='>' and text.startswith('go '):
            checking=packets[-1];check(side==checking['s'] and not checking['go'],raw);checking['go']=text
        elif sign=='<' and text.startswith(('info string TmFinishIteration hold','info string softnodes nodes','bestmove ')):
            p=packets[-1];check(side==p['s'] and p['go'],raw)
            which='soft' if text.startswith('info string softnodes') else 'moves' if text.startswith('bestmove ') else 'hold'
            p[which].append(text)
        elif sign=='>' and text!='quit':
            setup[side].append(text)
        elif sign=='<' and text in ('uciok','readyok'):
            traffic[side].append(text)
    return setup,traffic,packets


def replay_game(folder, rec, stage, book):
    game=int(rec['game']);opening=int(rec['opening'])
    check(opening==(game+1)//2 and rec['white']==('A' if game%2 else 'B'),rec)
    check({rec['white'],rec['black']}=={'A','B'},rec)
    game_path=folder/f'g{game:04d}'
    data=table(game_path/'searches.tsv')
    setup,traffic,packets=read_wire(game_path/'wire.txt')
    engines=json.loads((game_path/'engines.json').read_text())
    exe=engines['W']['exe']
    check(binary_hash(exe)==NC_SHA,(game,exe,'wrong nc'))
    check(table(game_path/'result.tsv')==[rec], (game,'per-game receipt differs from stage receipts'))
    ephemeral=[]
    expected_opening=chess.STARTING_FEN if stage in ('K27','C27') else ' '.join(book[opening-1].split()[:4])+' 0 1'
    check((game_path/'opening.txt').read_text().strip()==f'{opening}\t{expected_opening}',(game,'wrong EPD receipt'))

    for side,engine in [('W',rec['white']),('B',rec['black'])]:
        nodeclock=200 if engine=='A' and stage=='C27' else 100
        profile='M'+str(opening) if stage=='K27' else ('M1' if stage=='C27' else stage)
        opts={'M1':['TmFinishIteration true'],'M2':['TmNodeShare true'],'M3':['TmFinishIteration true','TmNodeShare true']}
        params=OPTIONS+[f'NodeClock {nodeclock}']+(opts[profile] if engine=='A' else [])
        expected=['uci']+['setoption name '+p.rsplit(' ',1)[0]+' value '+p.rsplit(' ',1)[1] for p in params]+['ucinewgame','isready']
        meta=engines[side]
        check(meta['role']==engine and [' '.join(x) for x in meta['options']]==params,(game,'engine options',side))
        check(meta['exe']==exe,(game,meta['exe'],exe))
        ident=(int(meta['pid']),int(meta['start_ticks']))
        check(ident not in ephemeral,(game,'same process on both sides'));ephemeral.append(ident)
        check(setup[side]==expected,(game,side,setup[side],expected))
        check(traffic[side]==['uciok','readyok'],(game,side,traffic))
    check(len(data)==len(packets),(game,len(data),len(packets)))
    fen=expected_opening;b=chess.Board(fen)
    clocks={'W':6000,'B':6000};names={'W':rec['white'],'B':rec['black']}
    spent=Counter();count=Counter();holds=Counter();holdlines=Counter();nodes=Counter()
    applied=[];seq=[];end=rule(b);result=('0-1' if b.turn else '1-0') if end=='checkmate' else '1/2-1/2' if end else None;flag=None
    for i,(s,p) in enumerate(zip(data,packets),1):
        who='W' if b.turn else 'B';engine=names[who];other='B' if who=='W' else 'W'
        check(end is None,(game,i,'moves after finalized board',end))
        check(int(s['game'])==game and int(s['ply'])==i and s['engine']==engine,(game,i,s))
        check(s['side'].upper() in (who,{'W':'WHITE','B':'BLACK'}[who]),(game,i,s['side'],who))
        expected_pos='position fen '+fen+(' moves '+' '.join(applied) if applied else '')
        expected_go=f"go wtime {clocks['W']} btime {clocks['B']} winc 60 binc 60"
        check(p['s']==who and p['pos'].strip()==expected_pos and p['go']==expected_go,(game,i,p['pos'],expected_pos,p['go'],expected_go))
        check(len(p['soft'])==len(p['moves'])==1,(game,i,p))
        m=re.fullmatch(r'info string softnodes nodes (\d+)',p['soft'][0]);check(m,(game,i,p['soft']))
        n=int(m[1]); used=n//100; move=p['moves'][0].split()[1]
        check(s['soft_line']==p['soft'][0] and s['move_line']==p['moves'][0],(game,i,s,p))
        check((int(s['N']),int(s['used']),s['bestmove'])==(n,used,move),(game,i,s))
        check(int(s['holds'])==len(p['hold']),(game,i,s['holds'],p['hold']))
        check((int(s['clock_before']),int(s['wtime']),int(s['btime']))==(clocks[who],clocks['W'],clocks['B']),(game,i,s))
        board_move=b.parse_uci(move)
        check(board_move in b.legal_moves,(game,i,move,b.fen()))
        before=clocks[who]
        seq.append((move,n));spent[engine]+=used;count[engine]+=1;holds[engine]+=bool(p['hold']);holdlines[engine]+=len(p['hold']);nodes[engine]+=n
        if used>before:
            end='time';result='0-1' if who=='W' else '1-0'
            flag=(game,i,who,engine,n,used,before)
        else:
            clocks[who]=before-used+60
            b.push(board_move);applied.append(move)
            end=rule(b)
            if end=='checkmate':result='1-0' if who=='W' else '0-1'
            elif end:result='1/2-1/2'
            elif len(applied)==600:end='cap';result='1/2-1/2'
        check(int(s['clock_after'])==clocks[who],(game,i,s['clock_after'],clocks))
    check((board_end(rec['ending']),rec['result'],int(rec['plies']),int(rec['wclock']),int(rec['bclock']))==(end,result,len(applied),clocks['W'],clocks['B']),(game,rec,end,result,clocks))
    for side in ('W','B'):
        player=names[side]
        forfeited=flag is not None and flag[2]==side
        counted_charge=spent[player]-(flag[5] if forfeited else 0)
        applied_count=count[player]-int(forfeited)
        check(clocks[side]==6000+60*applied_count-counted_charge,(game,side,'per-game clock conservation'))
    check(not holds['B'],(stage,game,'unexpected B hold'))
    if stage=='M2' or stage=='K27' and opening==2:check(not holds['A'],(stage,game,'unexpected A hold'))
    return dict(game=game,opening=opening,white=rec['white'],score=score2(rec),result=result,ending=end,plies=len(applied),clocks=clocks,
                count=dict(count),spent=dict(spent),holds=dict(holds),holdlines=dict(holdlines),nodes=dict(nodes),flag=flag,seq=seq,
                start=rec['started_utc'],finish=rec['ended_utc'],processes=ephemeral)

