#!/usr/bin/env python3
"""Check the actual relabelled suite result; no expectation values are substituted."""
import argparse, hashlib, json, subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--binary',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
a.out.mkdir(exist_ok=False)
cmd=[str(a.binary.resolve())];proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(a.out/'forge_sol_suite_20261025.stdout').write_bytes(proc.stdout);(a.out/'forge_sol_suite_20261025.stderr').write_bytes(proc.stderr)
lines=(proc.stdout+b'\n'+proc.stderr).decode().splitlines();known=[x for x in lines if x.startswith('KNOWN_FAILURE:')];failed=[x for x in lines if x.startswith('FAIL:')]
passed=proc.returncode==0 and len(known)==4 and len(failed)==0 and any(x=='Known failures explicitly reported: 4' for x in lines)
res={'status':'PASS' if passed else 'FAIL','argv':cmd,'actual_exit':proc.returncode,'binary_sha256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'known_lines':known,'fail_lines':failed,'stdout_sha256':hashlib.sha256(proc.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(proc.stderr).hexdigest()}
(a.out/'forge_sol_suite_result_20261025.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2));raise SystemExit(0 if passed else 1)
