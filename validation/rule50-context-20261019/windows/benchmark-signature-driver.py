from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import subprocess

ROOT=Path('/workspace/dwqww')
OUT=ROOT/'validation/rule50-context-20261019/windows/benchmark-signature-logs'
REPORT=OUT.parent/'benchmark-signatures.json'
WINE=Path('/workspace/.cloud-setup/wine/usr/lib/wine/wine64')
CASES=[('6.4.3',Path('/workspace/.cloud-setup/forge-windows-tt-coherent/forge.exe'),
        Path('/workspace/.cloud-setup/forge-windows-tt-coherent-source'),
        'df5d839a6a03f705310bb958601375fa9411e810'),
       ('6.4.4',Path('/workspace/.cloud-setup/forge-windows-rule50-context/forge.exe'),
        Path('/workspace/.cloud-setup/forge-windows-rule50-context-source'),
        '816423b1ddac23a00244449deef59dba736055a9')]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists() and not REPORT.exists()
OUT.mkdir()
stdin=b'bench 11\nquit\n'
(OUT/'stdin.txt').write_bytes(stdin)
environment=os.environ.copy();environment.update(WINEPREFIX='/workspace/.cloud-setup/wine-prefix-ready',
 WINEDEBUG='-all',XDG_CACHE_HOME='/workspace/.cloud-setup/font-cache')
protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'stdin_text':stdin.decode(),'stdin_sha256':sha(OUT/'stdin.txt'),'hash_mib':16,'threads':1,
 'settings_basis':'Frozen UCI bench uses Searcher(16), default thread_count1, clear per each of8 fixed positions',
 'scope':'Bounded fixed-depth node signatures only; recorded time/NPS fields are not compared or used as speed/Elo evidence',
 'cases':[{'version':version,'binary':str(binary),'source':str(source),'source_commit':commit,
           'command':[str(WINE),str(binary)],'binary_sha256_before':sha(binary),
           'uci_source_sha256_before':sha(source/'src/uci.cpp'),
           'search_header_sha256_before':sha(source/'include/forge/search.hpp')} for version,binary,source,commit in CASES],
 'environment_subset':{key:environment[key] for key in ('WINEPREFIX','WINEDEBUG','XDG_CACHE_HOME')}}
(OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
results=[]
try:
    for (version,binary,source,commit),record in zip(CASES,protocol['cases']):
        with (OUT/(version+'-stdout.log')).open('xb') as stdout, (OUT/(version+'-stderr.log')).open('xb') as stderr:
            completed=subprocess.run(record['command'],input=stdin,stdout=stdout,stderr=stderr,
                                     env=environment,cwd=binary.parent,timeout=300)
        output=(OUT/(version+'-stdout.log')).read_text()
        matches=re.findall(r'^info string bench depth (\d+) nodes (\d+) time \d+ nps \d+\s*$',output,re.M)
        if completed.returncode or len(matches)!=1 or int(matches[0][0])!=11:
            raise RuntimeError(f'{version}: failed exit or missing/unexpected bench signature')
        after=sha(binary)
        assert after==record['binary_sha256_before']
        assert sha(source/'src/uci.cpp')==record['uci_source_sha256_before']
        assert sha(source/'include/forge/search.hpp')==record['search_header_sha256_before']
        results.append({'version':version,'exit_code':completed.returncode,'depth':11,
                        'nodes':int(matches[0][1]),'binary_sha256_before':record['binary_sha256_before'],
                        'binary_sha256_after':after,'stdout_sha256':sha(OUT/(version+'-stdout.log')),
                        'stderr_sha256':sha(OUT/(version+'-stderr.log'))})
        print(json.dumps(results[-1]),flush=True)
    report={'status':'passed','scope':protocol['scope'],'hash_mib':16,'threads':1,'cases':results,
            'same_platform_parent_node_signature_equal':results[0]['nodes']==results[1]['nodes'],
            'timing_or_nps_gain_claim':None,'elo_gain_claim':None,'native_hardware_claim':False,
            'protocol_sha256':sha(OUT/'protocol.json'),'driver_sha256':sha(Path(__file__))}
except Exception as error:
    report={'status':'failed','cases':results,'error':str(error),'scope':protocol['scope']}
    REPORT.write_text(json.dumps(report,indent=2)+'\n');raise
REPORT.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
