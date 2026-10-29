from pathlib import Path
import json,re,hashlib,shutil
root=Path('/tmp/forge-astra2-b5/astra2_evidence/B5'); out=root/'sanitizers'; ct=out/'ctest_unsandboxed'
log=(ct/'ctest.log').read_text(); raw=(ct/'LastTest.log').read_text()
summary=re.search(r'(\d+)% tests passed, (\d+) tests failed out of (\d+)',log); assert summary
failures=re.findall(r'^\s*\d+ - (.*?) \((.*?)\)$',log,re.M)
findings=[line for line in raw.splitlines() if re.search(r'ERROR: (AddressSanitizer|LeakSanitizer)|SUMMARY: .*Sanitizer|runtime error:',line)]
exe=Path('/tmp/forge-astra2-build-b5-san/forge')
j={'source_commit':'fde944ae38e6bbfef0b38f2c4a207e08285fcc1d','binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'complete_ctest':True,'total':int(summary[3]),'passed':int(summary[3])-int(summary[2]),'failures':failures,'exit':int((ct/'exit.txt').read_text()),'asan':True,'ubsan':True,'leak_detection':True,'tsan':False,'sanitizer_diagnostic_lines':findings,'initial_attempt':'ctest/: interrupted after LeakSanitizer ptrace runtime incompatibility; not an engine result','scope':'Independent B5 only. No claim that all functional tests passed unless failures is empty.'}
(out/'qualification.json').write_text(json.dumps(j,indent=2)+'\n')
p=Path('/tmp/forge-astra2-build-b5-san/singular-v2-uci-regression.log')
if p.exists():shutil.copyfile(p,out/'singular_v2_uci.transcript')
start=raw.find('Testing: singular_v2_uci_regression')
if start>=0:
 text=raw[start:];begin=text.find('{')
 if begin>=0:
  try:
   obj,_=json.JSONDecoder().raw_decode(text[begin:]);(out/'singular_v2_uci.json').write_text(json.dumps(obj,indent=2)+'\n')
   p=root/'BENCH_RESULTS.md';p.write_text(p.read_text()+'\n## ASan/UBSan UCI regression records\n\nInstrumented times are not Release performance measurements.\n\n| Case | Depth | Nodes | ms | NPS |\n|---|---:|---:|---:|---:|\n'+''.join(f"| {b['label']} | {b['depth']} | {b['nodes']} | {b['time_ms']} | {b['nps']} |\n" for b in obj.get('benches',[])))
  except (ValueError,KeyError):pass
print(json.dumps(j,indent=2))
