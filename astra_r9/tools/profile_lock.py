"""Sample only our own lock process; retain RIPs and symbol attribution.

This is an intrusive, wall-clock statistical sampler, not a timing benchmark.
Only the main thread executing synchronous UCI bench is suspended, briefly,
and resumed in finally. Percentages are sample fractions, not hardware cycles.
"""
import bisect, collections, ctypes as C, hashlib, json, os, pathlib, random
import re, struct, subprocess, sys, threading, time
sys.path.insert(0, 'D:/a9/pydeps')
import psutil

EXE = r'C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_v23.exe'
EXPECTED = 'FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072'
OUT = pathlib.Path(sys.argv[1])
SECONDS = int(sys.argv[2]) if len(sys.argv) > 2 else 120
assert hashlib.sha256(pathlib.Path(EXE).read_bytes()).hexdigest().upper() == EXPECTED
OUT.mkdir(parents=True, exist_ok=False)
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
psutil.Process().cpu_affinity([3])
k = C.WinDLL('kernel32', use_last_error=True)
k.OpenThread.argtypes = [C.c_uint32, C.c_int, C.c_uint32]; k.OpenThread.restype = C.c_void_p
k.SuspendThread.argtypes = [C.c_void_p]; k.SuspendThread.restype = C.c_uint32
k.ResumeThread.argtypes = [C.c_void_p]; k.ResumeThread.restype = C.c_uint32
k.GetThreadContext.argtypes = [C.c_void_p, C.c_void_p]
k.CloseHandle.argtypes = [C.c_void_p]
k.K32EnumProcessModules.argtypes = [C.c_void_p, C.c_void_p, C.c_uint32, C.c_void_p]
symbols = subprocess.check_output([r'C:\msys64\ucrt64\bin\nm.exe', '-n', EXE], text=True)
(OUT/'symbols.txt').write_text(symbols)
syms = []
for line in symbols.splitlines():
    m = re.match(r'([0-9a-fA-F]+) [Tt] (.*)', line)
    if m: syms.append((int(m[1],16),m[2]))
syms.sort(); addresses = [x[0] for x in syms]
data = pathlib.Path(EXE).read_bytes(); pe = struct.unpack_from('<I',data,0x3c)[0]
preferred = struct.unpack_from('<Q',data,pe+24+24)[0]
p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     text=True, creationflags=subprocess.IDLE_PRIORITY_CLASS)
owned = psutil.Process(p.pid); owned.cpu_affinity([2])
thread_id = owned.threads()[0].id
h = k.OpenThread(0x0002 | 0x0008 | 0x0040, False, thread_id)
if not h: raise C.WinError(C.get_last_error())
mods = (C.c_void_p*1024)(); needed = C.c_uint32()
assert k.K32EnumProcessModules(int(p._handle), mods, C.sizeof(mods), C.byref(needed))
base = mods[0]
raw = C.create_string_buffer(1248); aligned = (C.addressof(raw)+15)&~15
counts = collections.Counter(); lines = []; errors = 0
def reader():
    with (OUT/'bench.log').open('w') as f:
        for line in p.stdout:
            f.write(line); f.flush(); lines.append(line.strip())
reader_thread = threading.Thread(target=reader, daemon=True); reader_thread.start()
p.stdin.write('uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nisready\n' + 'bench 20\n'*100); p.stdin.flush()
rng=random.Random(9001); start=time.monotonic()
try:
    while time.monotonic()-start < SECONDS and p.poll() is None:
        time.sleep(rng.uniform(.002,.006))
        C.memset(aligned,0,1232); C.c_uint32.from_address(aligned+48).value=0x100001
        old=k.SuspendThread(h)
        if old == 0xffffffff: errors+=1; continue
        try:
            if k.GetThreadContext(h,aligned):
                rip=C.c_uint64.from_address(aligned+248).value
                counts[rip-base+preferred]+=1
            else: errors+=1
        finally:
            if k.ResumeThread(h)==0xffffffff: raise C.WinError(C.get_last_error())
finally:
    k.CloseHandle(h)
    # Queued bench commands are intentionally long; terminate only this owned PID.
    p.terminate(); p.wait(timeout=15); reader_thread.join(timeout=5)
tot=sum(counts.values()); by_symbol=collections.Counter()
for addr,n in counts.items():
    i=bisect.bisect_right(addresses,addr)-1
    name=syms[i][1] if i>=0 and addr-addresses[i]<0x10000 else 'UNRESOLVED_OR_EXTERNAL'
    by_symbol[name]+=n
bench=[x for x in lines if 'bench depth 20 nodes' in x]
assert bench and all('nodes 12389307 ' in x for x in bench), bench
result={'exe':EXE,'sha256':EXPECTED,'method':'owned-main-thread suspend/context statistical sampling',
 'seconds':time.monotonic()-start,'samples':tot,'errors':errors,'core':2,'priority':'Idle',
 'runtime_base':hex(base),'preferred_base':hex(preferred),'completed_benches':len(bench),
 'symbols':[{'name':s,'samples':n,'percent':100*n/tot} for s,n in by_symbol.most_common()],
 'rips':{hex(a):n for a,n in counts.items()}}
(OUT/'profile.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ('rips','symbols')},indent=2))
print(json.dumps(result['symbols'][:18],indent=2))
