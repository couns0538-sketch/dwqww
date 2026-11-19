"""Cross-check both official E files against an independently assembled ordered list of raw edge records."""
from pathlib import Path
from types import SimpleNamespace
import audit
from audit import HERE,WORK,MANIFEST,rows,table,hashlib,load_book,parse_records,subprocess
RESULT=WORK/'j19match/results'
def verify():
    out=HERE/'E';out.mkdir(exist_ok=True)
    edges=rows(MANIFEST)
    settings=[f"E{int(r['edge']):02}" for r in edges if r['status']=='play']
    assembled=[];positions={};joint_ids=[]
    for build in ('r15d','kF'):
        expected=[];receipts=[];origin_rows=[];no_info=[];opens=[];games={};source_games=[]
        for e in edges:
            stage=f"E{int(e['edge']):02}"
            src=RESULT/f'{stage}-{build}'
            if e['status']=='start':
                assert not (src/'records.txt').exists(),(stage,build,'unexpected start-edge output')
                continue
            if not (src/'run.log').exists():continue
            assert (HERE/stage/'verified.txt').is_file(),stage
            lo=int(e['first_game']);hi=int(e['last_game'])
            positions.update(load_book(Path(''),lo,hi))
            raw=(src/'records.txt').read_bytes()
            data=parse_records(raw,lo,hi)
            for g in rows(src/'games.tsv'):
                gid=int(g['book_line'])
                assert gid not in games
                games[gid]=data.get(gid,[])
                receipts.append(g)
            source_games.extend([r for r in rows(HERE/stage/'games.tsv') if r['arm']==src.name])
            expected.append(raw)
            no_info.extend(rows(src/'no-info.tsv'))
            opens.extend(rows(src/'openings.tsv'))
        base=RESULT/f'E-{build}'
        status=(base/'run.log').read_text().rstrip().splitlines()[-1].split()[-1]
        assert status in ('COMPLETE','INCOMPLETE'),(base,status)
        official=(base/'records.txt').read_bytes()
        assert official==b''.join(expected),(base,'official file differs from ordered edge concatenation')
        canonical=rows(base/'games.tsv')
        assert len(canonical)==len(receipts)
        offset=0
        for combined,source in zip(canonical,receipts):
            gid=int(source['book_line'])
            for col,val in source.items():
                if col!='record_bytes':assert combined[col]==val,(build,gid,col,combined,source)
            offset+=sum(len(x[2]) for x in games[gid])
            assert int(combined['record_bytes'])==offset
        assert offset==len(official)
        assert rows(base/'no-info.tsv')==no_info and rows(base/'openings.tsv')==opens
        na=sum(x[1] is None for group in games.values() for x in group)
        nodes=sum(x[1] for group in games.values() for x in group if x[1] is not None)
        count=sum(len(group) for group in games.values())
        sums=[(base.name,int(s['slot']),int(s['book_line']),int(s['plies']),int(s['na_records']),int(s['nodes']),int(s['bytes']),s['sha256'],s['result'],s['termination']) for s in source_games]
        assembled.append(dict(name=base.name,status=status,games=games,sums=sums,raw=official,records=count,nodes=nodes,na=na,digest=hashlib.sha256(official).hexdigest(),notes=[f'{base.name} official record bytes, cumulative offsets, per-game metadata, seeded openings and per-move NA ledger agree with the individually replayed edge sources.']))
        if status=='COMPLETE':assert len(games)==5*len(settings)
    audit.args=SimpleNamespace(results=RESULT)
    total_games=len(settings)*5
    detail=[f'All {len(settings)} playable edges are compared in numeric edge order. The four start edges supply zero input files.']
    for arm in assembled:detail.append(f'{arm["name"]}: {len(arm["games"])} games, {arm["records"]} records, {arm["na"]} NA, {arm["nodes"]} numeric nodes, SHA-256 {arm["digest"]}.')
    (out/'assembly.txt').write_text('\n'.join(detail)+'\n')
    audit.compare(*assembled,positions,out,'E',min(positions),max(positions),requested=total_games)
if __name__=='__main__':verify()
