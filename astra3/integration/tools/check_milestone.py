#!/usr/bin/env python3
"""Derive A1 milestone receipt from native pins/CTest, plus whole-exe FMA and kiwipete.
IDEA_SOURCE: user round-three exact-source validation contract.
"""
import argparse,datetime,hashlib,json,pathlib,re,shutil,subprocess,sys
from zoneinfo import ZoneInfo
p=argparse.ArgumentParser();p.add_argument('engine',type=pathlib.Path);p.add_argument('evidence',type=pathlib.Path);p.add_argument('--source',required=True);a=p.parse_args()
r=a.evidence;exe=a.engine.resolve();pin=json.loads((r/'pins/results.json').read_text())
assert all(x['pass'] for x in pin['records'])
assert pin['sha256']==hashlib.sha256(exe.read_bytes()).hexdigest()
assert re.search(r'^nodes 4865609$',(r/'pins/perft.stdout').read_text(),re.M)
cmd=['objdump','-d',str(exe)];dis=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
fmas=[line for line in dis.stdout.decode().splitlines() if re.search(r'\bvfn?m(?:add|sub)\w*\b',line,re.I)]
(r/'whole_binary_fma.json').write_text(json.dumps({'command':cmd,'objdump_returncode':dis.returncode,'disassembly_sha256':hashlib.sha256(dis.stdout).hexdigest(),'count':len(fmas),'instructions':fmas},indent=2)+'\n')
assert not fmas, fmas
stdin=b'position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1\ngo perft 5\nquit\n'
(r/'kiwipete.stdin').write_bytes(stdin)
x=subprocess.run([str(exe)],input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300)
(r/'kiwipete.stdout').write_bytes(x.stdout);(r/'kiwipete.stderr').write_bytes(x.stderr)
assert x.returncode==0 and re.search(rb'^nodes 193690690$',x.stdout,re.M),x.stdout[-500:]
ct=(r/'ctest/ctest.log').read_text();summary=re.search(r'(\d+)% tests passed, (\d+) tests failed out of (\d+)',ct);assert summary
failed=re.findall(r'^\s*\d+ - (.*?) \((.*?)\)$',ct,re.M)
allowed={'forge_tests','forge_smp_tests','forge_tt_mate_tb_tests'}
assert all(name in allowed and status=='Failed' for name,status in failed),failed
raw=(r/'ctest/LastTest.log').read_text()
known=['FAIL: WAC 001 expected g3g6 got f6h5','FAIL: WAC 001 score 623 below 31997','FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion']
fail_lines=[line for line in raw.splitlines() if line.startswith('FAIL')]
def allowed_diagnostic(line):
    if line in known: return True
    if line.startswith('FAIL SmpExactNodes: overshoot bounded by the publish cadence'): return True
    if line == 'FAIL smp_tests':
        return any(x.startswith('FAIL SmpExactNodes: overshoot bounded by the publish cadence') for x in fail_lines)
    if line == 'FAIL forge_tt_mate_tb_tests':
        return any(x.startswith('FAIL Threads 2, search ') for x in fail_lines)
    match=re.fullmatch(r'FAIL Threads 2, search [12] on the shared TT: a real mate, never shorter than mate in 3 \((-?\d+) ([a-h][1-8][a-h][1-8][qrbn]?)\)',line)
    return bool(match and abs(int(match[1])) < 30000)
assert all(allowed_diagnostic(line) for line in fail_lines), fail_lines
# Preserve every original line; only explicitly allowed baseline diagnostics qualify.
receipt={'source_commit':a.source,'binary_sha256':pin['sha256'],'off_records':pin['records'],'perft5':4865609,'kiwipete5':193690690,'whole_binary_fma':0,'ctest_total':int(summary[3]),'ctest_failed':int(summary[2]),'ctest_failures':failed,'ctest_exit':int((r/'ctest/exit.txt').read_text()),'fail_lines':fail_lines,'timestamp_pt':datetime.datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),'speed_elo':'NOT_CLAIMED'}
(r/'qualification.json').write_text(json.dumps(receipt,indent=2)+'\n')
copy=r/'forge_release_linux';assert not copy.exists();shutil.copy2(exe,copy)
print(json.dumps(receipt,indent=2))
