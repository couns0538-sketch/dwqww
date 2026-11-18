"""Derive and audit small disjoint EPD books using fastchess v1.8.3-alpha's seeded order."""
import argparse
import collections
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile

STAGES = {'K12':(10,7341), 'C12':(50,7342), 'M3':(300,7343), 'M3b':(300,7344)}
HISTORY = {8:{'K8':50,'C8':100,'M1':1000,'M2':400},
           9:{'K9':50,'C9':100,'M1b':1000,'M2b':400},
           11:{'K11':25,'C11':100,'M2c':400,'M2d':400}}
ORIGINAL = '7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
ROOT = Path('/workspace/work')
OUT = Path(__file__).resolve().parent
SHUFFLE = """
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>
int main(int argc, char** argv) {
    std::size_t n = std::stoull(argv[1]), take = std::stoull(argv[2]);
    std::mt19937_64 gen(std::stoull(argv[3]));
    std::vector<std::size_t> items(n);
    std::iota(items.begin(), items.end(), 0);
    for (std::size_t i = 0; i < take; ++i) {
        if (i + 1 < n) std::swap(items[i], items[i + gen() % (n - i)]);
        std::cout << items[i] << '\\n';
    }
}
"""
def sha(data):
    return hashlib.sha256(data).hexdigest()
def marks(s):
    a=s.split()
    if len(a)!=6 or a[1] not in ('w','b'): raise ValueError(s)
    castle=''.join(c for c in 'KQkq' if c in a[2]) or '-'
    position=(a[0],a[1],castle)
    return position, (*position,a[3])
def rounds(path,n):
    data=path.read_bytes()
    headers=re.findall(rb'(?m)^\[Event [^\n]*(?:\n\[[^\n]+)*',data)
    out=collections.defaultdict(list)
    for h in headers:
        r=int(re.search(rb'(?m)^\[Round "(\d+)"\]',h)[1])
        f=re.search(rb'(?m)^\[FEN "([^"]+)"\]',h)[1].decode()
        out[r].append(f)
    if set(out)!=set(range(1,n+1)) or any(len(g)!=2 or g[0]!=g[1] for g in out.values()):
        raise ValueError(f'incomplete rounds or unequal opening pairs: {path}')
    return [out[i][0] for i in range(1,n+1)],sha(data)
def permutation(n,take,seed):
    prog=OUT/'shuffle'
    if not prog.exists():
        with tempfile.TemporaryDirectory(dir=OUT) as d:
            target=Path(d)/'shuffle'
            subprocess.run(['c++','-std=c++17','-O2','-x','c++','-','-o',target],input=SHUFFLE,text=True,check=True)
            target.replace(prog)
    return list(map(int,subprocess.check_output([prog,str(n),str(take),str(seed)],text=True).split()))
def prior(stage):
    h={k:dict(v) for k,v in HISTORY.items()}
    h[12]={k:STAGES[k][0] for k in list(STAGES)[:list(STAGES).index(stage)]}
    used3=set(); used4=set(); meta=[]
    for job,matches in h.items():
        for match,n in matches.items():
            p=ROOT/f'j{job}match/results/{match}.pgn'
            fens,checksum=rounds(p,n)
            for f in fens:
                key3,key4=marks(f); used3.add(key3); used4.add(key4)
            meta.append(f'prior_pgn job{job}/{match}.pgn pairs={n} sha256={checksum}')
    return used3,used4,meta
def run(action,stage):
    needed,seed=STAGES[stage]
    excluded,exact,meta=prior(stage)
    src=ROOT/'j8gate/UHO_Lichess_4852_v1.epd'
    src_bytes=src.read_bytes()
    if sha(src_bytes)!=ORIGINAL: raise ValueError('original UHO book SHA mismatch')
    data=[s for s in src_bytes.splitlines() if s]
    del src_bytes
    take=min(len(data),needed+128)
    while True:
        idx=permutation(len(data),take,seed)
        chosen=[]; seen=set(); prior_hits=0; dup_hits=0
        for i in idx:
            opening=data[i].decode()
            key,_=marks(opening)
            if key in excluded: prior_hits+=1;continue
            if key in seen: dup_hits+=1;continue
            chosen.append(data[i]);seen.add(key)
            if len(chosen)==needed: break
        if len(chosen)==needed: break
        if take==len(data): raise RuntimeError('not enough unused openings')
        take=min(take*2,len(data))
    # Undo the controller's second shuffle on this small book, to preserve the
    # original full-book seeded order even after already-used positions skip.
    sorted_for_file=[None]*needed
    for game,i in zip(chosen,permutation(needed,needed,seed)):
        sorted_for_file[i]=game
    payload=b'\n'.join(sorted_for_file)+b'\n'
    path=OUT/(stage+'.epd')
    if action=='prepare' and not path.exists():
        tmp=path.with_suffix('.tmp')
        tmp.write_bytes(payload);tmp.replace(path)
    if path.read_bytes()!=payload: raise ValueError(f'derived book mismatch {stage}')
    lines=[f'match {stage} seed {seed}',f'original_sha256 {ORIGINAL}',f'original_nonempty_entries {len(data)}',
        'Order uses fastchess Openings::shuffle (std::mt19937_64 Fisher-Yates). Walk the original seeded order until enough eligible positions, skipping historical or within-match duplicates. Inverse-permute the small EPD so fastchess order=random with the required seed emits the chosen sequence.',
        'Four-field EPD key uses placement, side, sorted castling rights and EP target. The exclusion key also drops the EP field to reject the same position under optional, uncapturable, or differing EP encodings. Move counters do not distinguish openings. PGN pairs start at their FEN tags. Book EPD has no prefixed moves.',
        *meta,f'prior_unique_four_field {len(exact)}',f'prior_unique_ignoring_ep {len(excluded)}',f'prior_hits_skipped_in_seeded_prefix {prior_hits}',f'duplicates_skipped_in_seeded_prefix {dup_hits}',
        f'selected_positions {len(chosen)}',f'selected_distinct_ignoring_ep {len(seen)}',f'selected_overlap_prior_ignoring_ep {len(excluded&seen)}',f'derived_sha256 {sha(payload)}']
    if action=='audit':
        actual,checksum=rounds(ROOT/f'j12match/results/{stage}.pgn',needed)
        a3=[marks(f)[0] for f in actual];a4={marks(f)[1] for f in actual}
        if a3!=[marks(f.decode())[0] for f in chosen] or set(a3)&excluded or a4&exact:
            raise ValueError('PGN does not match seeded selections or reuses a prior opening')
        lines += [f'actual_pgn_sha256 {checksum}',f'actual_opening_pairs {needed}',f'actual_distinct_four_field {len(a4)}',f'actual_distinct_ignoring_ep {len(set(a3))}',f'actual_overlap_prior_four_field {len(a4&exact)}',f'actual_overlap_prior_ignoring_ep {len(set(a3)&excluded)}','all_rounds_equal_seeded_original_order_after_exclusions yes']
    suffix='preflight' if action=='prepare' else 'audit'
    (OUT/f'{stage}-opening-{suffix}.txt').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines[-8:]))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','audit']);p.add_argument('stage',choices=STAGES)
    a=p.parse_args();run(a.action,a.stage)
