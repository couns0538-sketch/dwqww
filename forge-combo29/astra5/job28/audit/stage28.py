"""Independent wire, clocks, chess replay and compact-file readback for one arm of one block."""
import argparse
from collections import defaultdict
import csv
from hashlib import sha256
import io
import json
from pathlib import Path

from replay28 import BOOK_SHA, check, replay_game, table, table_out, time


def digest(raw):
    return sha256(raw).hexdigest()


def read_compact(arm, name):
    path=arm/name
    if path.is_file():
        return path.read_bytes()
    parts=table(path.with_name(path.name+'.parts.tsv'))
    data=b''.join((arm/p['filename']).read_bytes() for p in parts if p['kind']=='part')
    whole=next(p for p in parts if p['kind']=='whole')
    check((len(data),digest(data))==(int(whole['bytes']),whole['sha256']),(arm,name,'split archive mismatch'))
    return data


def tab_from(raw):
    return list(csv.DictReader(io.StringIO(raw.decode()),delimiter='\t'))


def verify(live, arm, book, target):
    meta=json.loads((arm/'receipt.json').read_text())
    block,profile,lo,hi=meta['block'],meta['stage'],meta['opening_first'],meta['opening_last']
    check(live.name==arm.name==profile and lo==50*(block-1)+1 and hi==min(50*block,len(book)),(block,profile,lo,hi))
    for name,desc in meta['files'].items():
        raw=(arm/name).read_bytes();check((len(raw),digest(raw))==(desc['bytes'],desc['sha256']),(arm,name,'manifest SHA or length'))
    compact_games=tab_from(read_compact(arm,'games.tsv'));compact_search=defaultdict(list)
    for row in tab_from(read_compact(arm,'searches.tsv')):compact_search[int(row['game'])].append(row)
    compact_openings={int(r['opening']):r['fen'] for r in tab_from(read_compact(arm,'openings.tsv'))}
    compact_process={(int(r['game']),r['color']):r for r in tab_from(read_compact(arm,'engines.tsv'))}
    wire_hashes={int(row['game']):row for row in tab_from(read_compact(arm,'wire-sha256.tsv'))}
    saved_profiles=json.loads((arm/'option-profiles.json').read_text())
    expected=set(range(2*lo-1,2*hi+1))
    records={int(r['game']):r for r in compact_games}
    check(len(records)==len(compact_games) and set(records)==set(meta['finished_game_ids']) and set(records)<=expected,arm)
    check(meta['complete']==(set(records)==expected),(arm,'wrong completion'))
    full=[];identities=set()
    for game,r in sorted(records.items()):
        folder=live/f'g{game:04d}';raw_search=table(folder/'searches.tsv')
        check(raw_search==compact_search[game],(arm,game,'compacted search rows'))
        check(table(folder/'result.tsv')==[r],(arm,game,'compacted game'))
        raw_wire=(folder/'wire.txt').read_bytes();wr=wire_hashes[game]
        check((len(raw_wire),digest(raw_wire))==(int(wr['bytes']),wr['sha256']),(arm,game,'wire'))
        opening=int(r['opening']);check(compact_openings[opening]==book[opening-1],(arm,game,'opening'))
        config=json.loads((folder/'engines.json').read_text())
        for side in ('W','B'):
            x=compact_process[game,side];y=config[side]
            check(int(x['pid'])==y['pid'] and x['start_ticks']==str(y['start_ticks']) and x['role']==y['role'] and x['started_utc']==y['started_utc'],(arm,game,side))
            check(saved_profiles[x['option_profile']]==y['options'],(arm,game,side,'frozen options'))
        g=replay_game(live,r,profile,book);g.pop('seq')
        for ident in g['processes']:
            pair=tuple(ident);check(pair not in identities,(arm,'engine PID reused'));identities.add(pair)
        full.append(g)
    check(sum(sum(g['count'].values()) for g in full)==meta['searches'],(arm,'search totals'))
    check(sum(g['plies'] for g in full)==meta['plies'],(arm,'ply totals'))
    all_pids=len(identities);check(all_pids==2*len(records),(arm,'process count'))
    partial_rows=tab_from(read_compact(arm,'unfinished-searches.tsv'))
    grouped=defaultdict(list)
    for row in partial_rows:grouped[int(row['game'])].append(row)
    for game in meta['unfinished_game_ids']:
        path=live/f'g{game:04d}'/'searches.tsv'
        check(grouped[game]==(table(path) if path.exists() else []),(arm,game,'partial search preservation'))
    check(len(partial_rows)==meta['unfinished_searches'],(arm,'partial search row count'))
    doc=dict(block=block,stage=profile,opening_first=lo,opening_last=hi,complete=meta['complete'],started=meta['started_games'],
        finished=len(full),unstarted=meta['not_started_game_ids'],unfinished=meta['unfinished_game_ids'],finished_ids=sorted(records),
        searches=meta['searches'],unfinished_searches=len(partial_rows),frozen_utc=meta['frozen_utc'],reason=meta['reason'],games=full,
        raw_wire_hashes_verified=len(full),all_named_files_verified=len(meta['files']))
    target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(doc,separators=(',',':'))+'\n');tmp.replace(target)
    return doc


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('live','compact','L27','target'):p.add_argument(k,type=Path)
    a=p.parse_args();book=a.L27.read_bytes();check(digest(book)==BOOK_SHA,'L27 SHA')
    s=verify(a.live,a.compact,book.decode().splitlines(),a.target)
    print('block',s['block'],s['stage'],s['complete'],s['finished'],'games',s['searches'],'completed searches')
