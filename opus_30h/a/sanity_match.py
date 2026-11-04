"""sanity_match.py - Opus 30-h job: fixed-length sanity match of a candidate against the lock with fastchess (own code).
SANITY ONLY - never an Elo claim (the crew gates).

usage: python -I -B sanity_match.py --out DIR --cand-exe EXE [--cand-opt "N=V;N2=V2"] [--base-exe EXE] [--games 400]
         [--tc 10+0.1] [--conc 2] [--cpus 0,1] [--book FILE] [--book-format epd] [--seed 30]
The script pins itself (and so fastchess and both engines) to --cpus at Idle priority first (fail closed), refuses an
existing --out, then runs fastchess with Threads 1, Hash 16, OwnBook false, -repeat (each opening with both colours),
order random with a fixed -srand, -recover; output in the crew's gate layout: DIR/<name>.log (fastchess stdout) and
DIR/<name>.pgn, plus DIR/RUN_INFO.json (command, exes with sha256, options). Summarise with
tools/gate_summary.py DIR. --conc must not exceed the number of --cpus (one game = one CPU: the engines alternate).
"""
import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import time

LOCK = r'C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_v23.exe'
FASTCHESS = r'C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe'
UHO = r'C:\Users\Administrator\grok-pc\coder-fuzz\UHO_Lichess_4852_v1.epd'


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--cand-exe', required=True)
    ap.add_argument('--cand-opt', default='')
    ap.add_argument('--base-exe', default=LOCK)
    ap.add_argument('--games', type=int, default=400)
    ap.add_argument('--tc', default='10+0.1')
    ap.add_argument('--conc', type=int, default=2)
    ap.add_argument('--cpus', default='0,1')
    ap.add_argument('--book', default=UHO)
    ap.add_argument('--book-format', default='epd')
    ap.add_argument('--seed', type=int, default=30)
    a = ap.parse_args()
    cpus = [int(x) for x in a.cpus.split(',')]
    if a.conc > len(cpus) or a.conc < 1 or len(cpus) + 0 > 8:
        sys.exit('--conc must be between 1 and the number of --cpus (at most 8 threads)')
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    h = ctypes.c_void_p(k32.GetCurrentProcess())
    if not k32.SetPriorityClass(h, 0x40) or not k32.SetProcessAffinityMask(h, ctypes.c_size_t(sum(1 << c for c in cpus))):
        sys.exit('cannot set Idle / CPU mask (fail closed)')
    os.makedirs(a.out)
    name = os.path.basename(os.path.normpath(a.out))
    opts = [f'option.{kv.strip()}' for kv in a.cand_opt.split(';') if kv.strip()]
    cmd = [FASTCHESS, '-engine', 'name=cand', f'cmd={a.cand_exe}'] + opts + ['-engine', 'name=lock', f'cmd={a.base_exe}',
           '-each', f'tc={a.tc}', 'timemargin=1000', 'proto=uci', 'option.Threads=1', 'option.Hash=16', 'option.OwnBook=false',
           '-openings', f'file={a.book}', f'format={a.book_format}', 'order=random', '-srand', str(a.seed),
           '-games', '2', '-repeat', '-rounds', str(a.games // 2), '-concurrency', str(a.conc), '-recover',
           '-pgnout', f'file={os.path.join(a.out, name + ".pgn")}', '-config', f'outname={os.path.join(a.out, name + ".config.json")}']
    info = {'started': time.strftime('%Y-%m-%d %H:%M:%S'), 'sanity_only': True, 'cmd': cmd, 'cpus': cpus,
            'candidate': {'exe': a.cand_exe, 'sha256': sha256(a.cand_exe), 'options': a.cand_opt},
            'base': {'exe': a.base_exe, 'sha256': sha256(a.base_exe)}, 'book': a.book, 'tc': a.tc, 'games': a.games}
    for kv in a.cand_opt.split(';'):
        if '=' in kv and os.path.isfile(kv.split('=', 1)[1].strip()):
            info['candidate']['option_file_sha256'] = sha256(kv.split('=', 1)[1].strip())
    with open(os.path.join(a.out, 'RUN_INFO.json'), 'x', encoding='utf-8', newline='\n') as f:
        json.dump(info, f, indent=1)
    with open(os.path.join(a.out, name + '.log'), 'x', encoding='utf-8', newline='\n') as log:
        rc = subprocess.call(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=a.out)
    info['ended'] = time.strftime('%Y-%m-%d %H:%M:%S')
    info['fastchess_exit'] = rc
    with open(os.path.join(a.out, 'RUN_INFO_end.json'), 'x', encoding='utf-8', newline='\n') as f:
        json.dump(info, f, indent=1)
    print(f'fastchess exit {rc}; summarise with gate_summary.py {a.out}')
    sys.exit(rc)


if __name__ == '__main__':
    main()
