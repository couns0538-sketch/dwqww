#!/usr/bin/env python3
"""Default-off actual-call instrumentation. Frozen baseline only, no timing claims."""
import argparse, hashlib, json, pathlib, re, subprocess, tempfile
LOCK='16833ecc03b425586f91f4c8834dea8807bf4c22'
p=argparse.ArgumentParser()
p.add_argument('--run',action='store_true')
p.add_argument('--cxx',default='g++')
p.add_argument('--output',type=pathlib.Path)
a=p.parse_args()
if not a.run: p.exit(message='Default off. Execution requires coordinator CPU release.\n')
repo=pathlib.Path(__file__).resolve().parents[2]
def git(*args): return subprocess.check_output(['git','-C',str(repo),*args])
assert git('branch','--show-current').decode().strip()=='dot/review-20261110'
# Destructor emits once in each fresh, single-threaded bench process.
preamble=r'''
#include <cstdio>
namespace {
struct EvasionProbe {
    unsigned long long calls=0, fallback=0, checked=0, eligible=0, reject=0,
        double_reject=0, king_bypass=0, ep_bypass=0, survivor_illegal=0, mismatch=0;
    ~EvasionProbe() {
        std::fprintf(stderr,"EVASION_COUNTS {\"calls\":%llu,\"fallback\":%llu,\"checked\":%llu,\"eligible\":%llu,\"reject\":%llu,\"double_reject\":%llu,\"king_bypass\":%llu,\"ep_bypass\":%llu,\"survivor_illegal\":%llu,\"mismatch\":%llu}\n",calls,fallback,checked,eligible,reject,double_reject,king_bypass,ep_bypass,survivor_illegal,mismatch);
    }
} evasion_probe;
}
'''
predicate=r'''
    ++evasion_probe.fallback;
    bool evasion_reject = false;
    bool evasion_eligible = false;
    if (checkers_ != 0) {
        ++evasion_probe.checked;
        if (piece_type(moving) == King) ++evasion_probe.king_bypass;
        else if ((move.flags & EnPassant) != 0) ++evasion_probe.ep_bypass;
        else {
            evasion_eligible = true;
            ++evasion_probe.eligible;
            if ((checkers_ & (checkers_ - 1)) != 0) {
                evasion_reject = true;
                ++evasion_probe.double_reject;
            } else {
                evasion_reject = ((checkers_ | attacks::between(king_square(us), lsb(checkers_))) & square_bb(move.to)) == 0;
            }
            evasion_probe.reject += evasion_reject;
        }
    }
'''
ending=r'''
    const bool evasion_original = !square_attacked_with_occupancy(king, opposite(us), occupancy, removed);
    evasion_probe.mismatch += evasion_reject && evasion_original;
    evasion_probe.survivor_illegal += evasion_eligible && !evasion_reject && !evasion_original;
    return evasion_original;
'''
with tempfile.TemporaryDirectory(prefix='forge-evasion-calls-') as tmp:
    root=pathlib.Path(tmp); manifest={}
    # Explicit directory allowlist, source/header extensions only. No windows_build.
    names=git('ls-tree','-r','--name-only',LOCK,'forge-combo29/src','forge-combo29/include').decode().splitlines()
    for name in names:
        assert pathlib.Path(name).suffix in ('.hpp','.h','.cpp','.inc')
        data=git('show',f'{LOCK}:{name}'); target=root/pathlib.Path(name).relative_to('forge-combo29')
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(data)
        manifest[name]=hashlib.sha256(data).hexdigest()
    source=root/'src/board.cpp'; original=source.read_text()
    start=original.index('#if FORGE_SPD_KING_LINES\nbool Board::is_legal(')
    end=original.index('bool Board::is_pseudo_legal(',start)
    section=original[start:end]
    entry='bool Board::is_legal(const Move& move) const {'
    occupancy='    Bitboard occupancy = occupied() & ~square_bb(move.from);'
    ret='    return !square_attacked_with_occupancy(king, opposite(us), occupancy, removed);'
    assert section.count(entry)==section.count(occupancy)==section.count(ret)==2
    instrumented=preamble+original[:start]+section.replace(entry,entry+'\n    ++evasion_probe.calls;').replace(occupancy,predicate+occupancy).replace(ret,ending)+original[end:]
    flags=['-std=c++20','-O3','-DNDEBUG','-DFORGE_NNUE_HIDDEN=256','-DFORGE_EXPOSE_TUNABLES=1',
           '-DFORGE_SPD_TT_NOTLS=1','-DFORGE_SPD_NO_ZERO_MOVELISTS=2','-DFORGE_SEARCH_SPEED2=1',
           '-DFORGE_SPD_PREFETCH_EARLY=1','-DFORGE_SPD_SLIDER_PEXT=1','-DFORGE_SPD_NNUE_ZMM=1',
           '-ffp-contract=off','-fno-fast-math','-march=x86-64-v4','-pthread']
    records=[]
    for king_lines in (0,1):
        for variant,contents in [('baseline',original),('instrumented',instrumented)]:
            source.write_text(contents); exe=root/f'{variant}-{king_lines}'
            command=[a.cxx,*flags,f'-DFORGE_SPD_KING_LINES={king_lines}','-I'+str(root/'include'),
                     *map(str,sorted((root/'src').glob('*.cpp'))),'-o',str(exe)]
            subprocess.run(command,check=True,timeout=240)
            binary_hash=hashlib.sha256(exe.read_bytes()).hexdigest()
            for mode,pin in [('true',3024920),('false',2448617)]:
                commands=f'setoption name Threads value 1\nsetoption name UseNNUE value {mode}\nbench 16\nquit\n'
                completed=subprocess.run([str(exe)],input=commands,text=True,capture_output=True,check=True,timeout=120,cwd=root)
                nodes=re.findall(r'info string bench depth 16 nodes (\d+)',completed.stdout)
                assert nodes==[str(pin)],(king_lines,variant,mode,nodes)
                matches=re.findall(r'^EVASION_COUNTS (.+)$',completed.stderr,re.M)
                counts=None
                if variant=='instrumented':
                    assert len(matches)==1,completed.stderr
                    counts=json.loads(matches[0]); assert counts['mismatch']==0
                # Keep raw diagnostics for identity/review, but never interpret reported engine times.
                records.append(dict(king_lines=king_lines,variant=variant,nnue=mode,depth=16,nodes=int(nodes[0]),
                    binary_sha256=binary_hash,counts=counts,stdin=commands,stdout=completed.stdout,stderr=completed.stderr))
    receipt=dict(baseline=LOCK,purpose='actual-call counts only; instrumented timings invalid',
                 compiler=subprocess.check_output([a.cxx,'--version']).decode().splitlines()[0],flags=flags,
                 snapshot_sha256=manifest,instrumented_board_sha256=hashlib.sha256(instrumented.encode()).hexdigest(),
                 script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),runs=records)
    output=json.dumps(receipt,indent=2)+'\n'
    if a.output: a.output.write_text(output)
    print(output,end='')
