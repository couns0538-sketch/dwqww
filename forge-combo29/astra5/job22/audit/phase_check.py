"""Check the matched L1 releases and per-process resident-memory points independently."""
from datetime import datetime,timezone
from pathlib import Path
import re,sys,time
from audit import HERE,RAW,STAGES,rows,table
def barriers():
    pairs=rows(RAW/'L1-barriers.tsv')
    sampled=[rows(RAW/f'L1-{s}'/'rss-all.tsv') for s in ('r15d','kF')]
    flag=(RAW/'L1-boundary.txt').read_text()
    assert len(pairs)==len(sampled[0])==len(sampled[1]) and pairs
    assert re.search(r'^common_completed_games '+str(len(pairs))+'$',flag,re.M)
    assert re.search(r'^last_game_id '+pairs[-1]['game']+'$',flag,re.M)
    reason=re.search(r'^reason (.+)$',flag,re.M)[1]
    if reason=='target':assert len(pairs)==5000
    else:assert reason=='minute40' and len(pairs)<5000
    previous=None
    for idx,r in enumerate(pairs):
        assert (int(r['ordinal']),int(r['game']))==(idx+1,700001+idx)
        rls=datetime.fromisoformat(r['released_utc']);end=datetime.fromisoformat(r['both_done_utc'])
        assert rls<=end and (previous is None or previous<=rls)
        previous=end
        for j,b in enumerate(('r15d','kF')):
            s=sampled[j][idx]
            assert s['pid']==r[b+'_pid'] and s['vmrss_kb']==r[b+'_vmrss_kb']
            read=datetime.fromisoformat(s['observed_utc'])
            assert rls<=read<=end,(idx,s,rls,end)
    assert previous<datetime.fromisoformat('2026-11-19T02:28:38+00:00'),(previous,'late L1 game')
    (HERE/'L1/barriers.txt').write_text(f'{len(pairs)} common L1 game boundaries were released serially. The previous pair completed before each next release. Both actual child PIDs and both per-game VmRSS values agree with the independent engine receipts on every boundary. Last completed game {pairs[-1]["game"]}; reason {reason}; last shared completion time {previous.isoformat()}.\n')
def forecast():
    txt=(HERE.parent/'astra5/forge-combo29/astra5/job22/prediction.txt').read_text()
    vals=re.findall(r'^(L0|L1)\s+(r15d|kF)\s+(\d+) to (\d+)\s+(\d+) to (\d+)$',txt,re.M)
    assert len(vals)==4
    grades=[]
    for phase,build,a,b,c,d in vals:
        stage='L1' if phase=='L1' else 'L0-'+build
        mm=[r for r in rows(HERE/stage/'rss.tsv') if r['arm']==phase+'-'+build]
        for name,s,low,high in [('first',mm[0],a,b),('last',mm[-1],c,d)]:
            n=int(s['vmrss_kb'])
            grades.append((phase,build,name,s['completed'],s['game'],n,low,high,int(low)<=n<=int(high)))
    table(HERE/'memory-prediction.tsv',('stage','build','when','ordinal','game','actual_kB','lower_kB','upper_kB','inside'),grades)
if __name__=='__main__':
    while not (HERE/'L1/verified.txt').is_file():time.sleep(1)
    barriers()
    while not (HERE/'reading.txt').is_file():time.sleep(1)
    forecast()
