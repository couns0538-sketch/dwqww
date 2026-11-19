"""Replay original wire and compact evidence to independently verify every counted engine search."""
from collections import Counter,defaultdict
from pathlib import Path
import json,re
from common29 import *

GO_LINE=re.compile(r'info string softnodes nodes (\d+)$')
NAMES=("searches","n_total","spent_total","depth_total","depth_reported","hardcap","no_score")

def wire_packets(path):
    setup={s:[] for s in ('W','B')}; handshake={s:[] for s in setup};quits=[];packets=[];pending=None
    for line in path.read_text().splitlines():
        check(not re.search(r'unknown option|invalid value|ERROR',line,re.I),(path,line))
        if not re.match(r'^[WB] [<>] ',line):continue
        side,arrow,text=line.split(' ',2)
        if arrow=='>':
            if text.startswith('position '):
                check(pending is None,(path,'incomplete search'));pending={'color':side,'pos':text,'go':None,'soft':[],'info':[]}
            elif text.startswith('go '):
                check(pending and pending['color']==side and pending['go'] is None,(path,text));pending['go']=text
            elif text=='quit':quits.append(side)
            else:setup[side].append(text)
        elif text in ('uciok','readyok'):handshake[side].append(text)
        elif pending is not None:
            check(side==pending['color'] and pending['go'],(path,text))
            if text.startswith('info string softnodes nodes'):pending['soft'].append(text)
            elif text.startswith('info ') and not text.startswith('info string '):pending['info'].append(text)
            elif text.startswith('bestmove '):
                pending['move']=text;packets.append(pending);pending=None
    expected=['uci']+['setoption name '+key+' value '+val for key,val in (o.rsplit(' ',1) for o in OPTIONS)]+['ucinewgame','isready']
    check(all(setup[x]==expected and handshake[x]==['uciok','readyok'] for x in setup),(path,'startup',setup))
    check(quits==['W','B'] and pending is None,(path,'shutdown',quits))
    return packets

def maybe_none(s):return None if s in ('','NA','-') else s

def replay(rec,rows,fen,raw,thresholds=THRESHOLDS):
    arm=rec['match'];i=int(rec['game']);opening=int(rec['opening'])
    check(i in (2*opening-1,2*opening) and rec['white']==('A' if i%2 else 'B') and set([rec['white'],rec['black']])=={'A','B'},(arm,i,rec))
    board=chess.Board(fen);history=[];ending,result=rule(board,0)
    if raw:
        packets=wire_packets(raw/'wire.txt')
        check(len(packets)==len(rows),(raw,len(packets),len(rows)))
        check(table(raw/'searches.tsv')==rows and table(raw/'result.tsv')==[rec],(raw,'compact mismatch'))
        check((raw/'opening.txt').read_text().strip()==f'{opening}\t{fen}',(raw,'wrong opening'))
    metrics={k:Counter() for k in ('A','B')};bands=defaultdict(Counter);first={k:{} for k in metrics}
    for j,r in enumerate(rows,1):
        color='W' if board.turn else 'B';side=rec['white'] if board.turn else rec['black'];go=command(arm,opening,side)
        check(ending is None and (r['match'],int(r['game']),int(r['ply']),r['side'],r['color'],r['go'])==(arm,i,j,side,color,go),(arm,i,j,r))
        n=int(r['n']);kind,limit=go.split()[1:];lim=int(limit)
        depth=maybe_none(r['depth']);score=maybe_none(r['score']);info_nodes=maybe_none(r['info_nodes']);soft_n=maybe_none(r['soft_n'])
        soft=maybe_none(r['soft_line']);info=maybe_none(r['info_line']);move_line=r['move_line']
        d=data_info(info) if info else {}
        check(score==d.get('score') and (int(depth) if depth is not None else None)==d.get('depth'),(arm,i,j,'last scored info',r))
        m=GO_LINE.fullmatch(soft) if soft else None
        check((int(m[1]) if m else None)==(int(soft_n) if soft_n else None),(arm,i,j,'soft footer'))
        if kind=='softnodes':check(m and n==int(m[1]),(arm,i,j,'soft reported n',r))
        else:check(n==int(info_nodes or 0) and n<=lim,(arm,i,j,'nodes recorded',r))
        if raw:
            q=packets[j-1];pos='position fen '+fen+(' moves '+' '.join(history) if history else '')
            check((q['color'],q['pos'],q['go'],q['move'])==(color,pos,go,move_line),(raw,j,'commands/bestmove'))
            check(q['soft']==([soft] if soft else []),(raw,j,'footer',q['soft'],soft))
            found=None;lastnodes=None
            for l in q['info']:
                inf=data_info(l)
                if 'score' in inf:found=l
                if 'depth' in inf and 'nodes' in inf:lastnodes=inf['nodes']
            check(found==info and lastnodes==(int(info_nodes) if info_nodes is not None else None),(raw,j,'last info selection',found,info,lastnodes,info_nodes))
        val=r['bestmove'];check(move_line.split()[:2]==['bestmove',val],(arm,i,j,move_line));mv=board.parse_uci(val)
        check(mv in board.legal_moves,(arm,i,j,'illegal',val))
        tok=metrics[side];tok['searches']+=1;tok['n_total']+=n;tok['spent_total']+=n if kind=='softnodes' else lim
        if depth is not None:tok['depth_total']+=int(depth);tok['depth_reported']+=1
        if score is None:tok['no_score']+=1
        else:
            typ,sv=score.split();sv=int(sv)
            for e in thresholds:
                if e not in first[side] and (typ=='mate' and sv>0 or typ=='cp' and sv>=e):first[side][e]=j
        if kind=='softnodes' and n>=4*lim:tok['hardcap']+=1
        if kind=='softnodes' and lim==2000:
            group='1-40' if j<=40 else '41-80' if j<=80 else '81+'
            for key in ('all',group):bands[key]['searches']+=1;bands[key]['n_total']+=n
        history.append(val);board.push(mv);ending,result=rule(board,len(history))
    check((ending,result,len(history))==(rec['ending'],rec['result'],int(rec['plies'])),(arm,i,'board replay',ending,result,len(history),rec))
    return dict(game=i,opening=opening,white=rec['white'],score=scored(result,rec['white']),result=result,ending=ending,plies=len(history),
                players={k:dict(v) for k,v in metrics.items()},bands={k:dict(v) for k,v in bands.items()},first={k:dict(v) for k,v in first.items()},
                start=rec['started_utc'],finish=rec['ended_utc'])

def stage(path,book,live=None):
    ar=json.loads((path/'receipt.json').read_text());arm=ar['stage'];b=ar['block']
    for name,meta in ar['files'].items():
        data=(path/name).read_bytes();check((len(data),sha(data))==(meta['bytes'],meta['sha256']),(path,name,'manifest'))
    rgs=table(path/'games.tsv');source=defaultdict(list)
    for r in table(path/'searches.tsv'):source[int(r['game'])].append(r)
    opens={int(r['opening']):r['fen'] for r in table(path/'openings.tsv')}
    check(all(fen==book[k-1] for k,fen in opens.items()),(path,'L27 mismatch'))
    profiles=json.loads((path/'option-profiles.json').read_text());gos=table(path/'engines.tsv')
    pids=defaultdict(list)
    for e in gos:
        i=int(e['game']);c=e['color'];role='A' if (i%2==1)==(c=='W') else 'B'
        check(role==e['role'] and proc_options(profiles[e['option_profile']])==OPTIONS,(path,e,'options'))
        pids[i].append([int(e['pid']),int(e['start_ticks'])])
    wire={int(x['game']):x for x in table(path/'wire-sha256.tsv')};games=[];ids=set()
    for rec in rgs:
        i=int(rec['game']);k=int(rec['opening']);check(i not in ids and rec['match']==arm,(path,rec));ids.add(i)
        raw=live/f'g{i:04d}' if live else None
        if raw:
            h=wire[i];data=(raw/'wire.txt').read_bytes();check((len(data),sha(data))==(int(h['bytes']),h['sha256']),(raw,'wire digest'))
            ep=json.loads((raw/'engines.json').read_text())
            check(all(proc_options(y['options'])==OPTIONS for y in ep.values()),(raw,'options'))
            check(pids[i]==[[ep[c]['pid'],int(ep[c]['start_ticks'])] for c in ('W','B')],(raw,'side PIDs'))
        g=replay(rec,source[i],opens[k],raw);check(len(pids[i])==2,(path,i,'fresh processes'));g['processes']=pids[i];games.append(g)
    check(ids==set(ar['finished_game_ids']) and sum(g['plies'] for g in games)==ar['searches']==ar['plies'],(path,'result totals'))
    check(sum(len(rows) for rows in source.values())==ar['searches'],(path,'search total'))
    return dict(block=b,match=arm,complete=ar['complete'],started=ar['started_games'],finished=len(games),games=games,
                unstarted=ar['not_started_game_ids'],unfinished=ar['unfinished_game_ids'],unfinished_searches=ar['unfinished_searches'])
