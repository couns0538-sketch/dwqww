"""Cross-check job 22 process lifetimes, between-game resident samples, and the two fresh L0 tails."""
import csv
from datetime import datetime
import hashlib
from itertools import zip_longest
from pathlib import Path
import re
import sys

W=Path('/workspace/work')
REVIEW=Path(__file__).resolve().parent
RES=W/'j22match/results'
PINS={'r15d':(W/'j7base/build/forge','9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671'), 'kF':(W/'j16kf/build/forge','c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb')}
def rows(p):
    with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def utc(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def digest(data):return hashlib.sha256(data).hexdigest()
def check(arm):
    folder=RES/arm
    log=(folder/'run.log').read_text()
    assert log.endswith(('status COMPLETE\n','status CUT_MINUTE40\n'))
    pid,aff=re.search(r'^P1_Both pid (\d+) child_cpu_affinity \[(\d+)\]$',log,re.M).groups()
    ticks=re.search(r'^engine_start_ticks (\d+)$',log,re.M)[1]
    b='kF' if arm.endswith('-kF') else 'r15d'
    exe,pin=PINS[b]
    assert f'executable {exe} sha256 {pin}' in log
    if arm.startswith('L') or 'proc_pid_exe' in log:assert f'proc_pid_exe {pid} {exe}' in log
    assert 'P1_Both readyok' in log and re.search(r'P1_Both info string NNUE v3 active: .*checksum 30ab43b4ba5db5f3',log)
    opts=re.findall(r'^engine (setoption .*)$',log,re.M)
    expected=(W/'j7base/pc20.txt').read_text().splitlines()+['setoption name NNUEArchFile value '+str(W/'j7net/net768.nnue'),'setoption name NNUEArch value true']
    if arm=='C22':expected[expected.index('setoption name LmrQuietBase value 93')]='setoption name LmrQuietBase value 60'
    assert opts==expected
    per=rows(folder/'games.tsv')
    a=rows(folder/'rss-all.tsv'); selected=rows(folder/'rss.tsv')
    raw=(folder/'rss-source.txt').read_text().splitlines()
    starts=re.findall(r'^game_start (\d+) (\S+) (\S+) (\d+)$',log,re.M)
    assert len(per)==len(a)==len(raw)==len(starts)
    prev_stamp=None;zeroes=0
    for i,(g,r,m,start) in enumerate(zip(per,a,raw,starts),1):
        n=int(g['book_line']);assert n==int(per[0]['book_line'])+i-1
        assert r['completed']==str(i) and r['game']==str(n)
        assert g['p1_pid']==g['p2_pid']==r['pid']==start[3]==pid and r['start_ticks']==ticks
        assert int(g['p1_search'])+int(g['p2_search'])==int(g['plies'])
        assert int(g['p1_na'])+int(g['p2_na'])==int(g['na'])
        assert int(r['vmrss_kb'])>0
        tokens=re.fullmatch(r'(\d+) (\d+) (\d+) (\S+) VmRSS:\s+(\d+) kB',m)
        assert tokens and list(tokens.groups())==[r['completed'],r['game'],pid,r['observed_utc'],r['vmrss_kb']]
        assert start[0]==str(n)
        terminating=n in {700591,701791,704280}
        assert (int(g['plies'])==0)==terminating
        assert start[2]==('terminal_random_opening_readyok_all' if terminating else 'readyok_all')
        first,last=utc(start[1]),utc(r['observed_utc'])
        assert first<=last<=utc(g['end_utc'])
        if prev_stamp:assert prev_stamp<=first
        prev_stamp=last
        zeroes+=int(terminating)
    milestones=[i for i in (1,1000,2000,3000,4000,len(a)) if i<=len(a)]
    assert selected==[a[i-1] for i in sorted(set(milestones))]
    live={r['arm']:r for r in rows(REVIEW/'live-pid-identity.tsv')}
    identity='worker ancestry and start ticks'
    if arm in live:
        ob=live[arm]
        assert ob['pid']==pid and ob['proc_starttime_ticks']==ticks and ob['exe_sha256']==pin and ob['exe']==str(exe)
        assert ob['cpu_affinity']==aff
        identity='worker plus independent live proc observation'
    elif arm.startswith('L'):raise AssertionError(f'Missing independent observation for {arm}.')
    sample=(folder/'sample-uci.txt').read_text()
    for section in sample.split('begin ')[1:]:
        data=section.splitlines()
        if data[-1]!='end':raise ValueError(arm)
        game,ply=data[0].split(); reply=[s.removeprefix('< ') for s in data if s.startswith('< ')]
        inf=[s for s in reply if s.startswith('info ')]
        last=re.search(r'(?:^| )nodes (\d+)(?: |$)',inf[-1])[1] if inf else 'NA'
        assert reply[-1].startswith('bestmove ')
        assert data[-2]==f'record {game} {ply} {reply[-1].split()[1]} {last}'
    p=(folder/'records.txt').read_bytes()
    total=sum(int(g['plies']) for g in per)
    assert len(p.splitlines())==total and int(per[-1]['record_bytes'])==len(p)
    assert f'records_sha256 {digest(p)}' in log
    stat=(arm,b,pid,ticks,aff,len(per),per[0]['book_line'],per[-1]['book_line'],zeroes,total,identity)
    return stat,selected,p,per
def main():
    controls=sys.argv[1:] or ['K22-1','K22-2','C22','L1-r15d','L1-kF','L0-r15d','L0-kF']
    verified={key:check(key) for key in controls}
    assert len({(v[0][2],v[0][3]) for v in verified.values()})==len(controls)
    print('arm\tbuild\tPID\tproc_start_ticks\tCPU\tgames\tfirst_id\tlast_id\tterminal_zero_ply_games\trecords\tidentity_check')
    for stat,samples,data,per in verified.values():print(*stat,sep='\t')
    if len(controls)!=7:return
    assert verified['K22-1'][2]==verified['K22-2'][2]!=verified['C22'][2]
    assert verified['L1-r15d'][0][5]==verified['L1-kF'][0][5]
    barriers=rows(RES/'L1-barriers.tsv')
    assert len(barriers)==verified['L1-r15d'][0][5]
    perbuild={name:rows(RES/f'L1-{name}'/'rss-all.tsv') for name in PINS}
    for i, barrier in enumerate(barriers,1):
        assert barrier['ordinal']==str(i) and barrier['game']==str(700000+i)
        low,high=utc(barrier['released_utc']),utc(barrier['both_done_utc'])
        for name in PINS:
            sample=perbuild[name][i-1]
            assert barrier[f'{name}_pid']==sample['pid']
            assert barrier[f'{name}_vmrss_kb']==sample['vmrss_kb']
            assert low<=utc(sample['observed_utc'])<=high
        if i<len(barriers):
            assert high<=utc(barriers[i]['released_utc'])
    with (REVIEW/'memory-audit.tsv').open('w') as out:
        print('arm\tcompleted\tgame\tengine_pid\tproc_start_ticks\tVmRSS_kB\tobserved_utc',file=out)
        for arm in ('L1-r15d','L1-kF'):
            for s in verified[arm][1]:
                print(arm,*s.values(),sep='\t',file=out)
    with (REVIEW/'fresh-tail-audit.txt').open('w') as out:
        for build in ('r15d','kF'):
            old=verified['L1-'+build];fresh=verified['L0-'+build]
            assert int(old[0][2])!=int(fresh[0][2])
            assert int(old[0][3])<int(fresh[0][3])
            assert [g['book_line'] for g in fresh[3]]==[g['book_line'] for g in old[3][-10:]]
            offset=int(old[3][-11]['record_bytes'])
            tail=old[2][offset:]
            print(f'{build} fresh L0 PID {fresh[0][2]} after L1 PID {old[0][2]}. Last ten IDs {fresh[0][6]}..{fresh[0][7]}. L1 byte offset {offset}. L1 tail sha256 {digest(tail)}. L0 sha256 {digest(fresh[2])}. Exact equality {fresh[2]==tail}.',file=out)
if __name__=='__main__':main()
