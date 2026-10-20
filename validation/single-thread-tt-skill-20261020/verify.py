#!/usr/bin/env python3
"""Check this documentation update; never execute a chess engine."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SKILL=ROOT/'.agents/skills/validating-shared-chess-tt'
checks=[]
def check(label,value):
 checks.append({'check':label,'passed':bool(value)})
 if not value:raise AssertionError(label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protocol=json.loads((HERE/'PROTOCOL.json').read_text())
check('original main skill unchanged in baseline copy',sha(HERE/'baseline-SKILL.md')==protocol['baseline_skill_sha256'])
check('original scenarios unchanged in baseline copy',sha(HERE/'baseline-scenarios.md')==protocol['baseline_scenarios_sha256'])
main=(SKILL/'SKILL.md').read_text()
check('main skill under500words',len(main.split())<500)
front=main.split('---',2)[1]
check('valid name',bool(re.search(r'^name: [a-z][a-z0-9-]*$',front,re.M)))
check('trigger-only description',bool(re.search(r'^description: Use when ',front,re.M)))
check('frontmatter under1024characters',len(front)<1024)
for name in ('SKILL.md','scenarios.md'):
 text=(SKILL/name).read_text()
 for label,target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',text):
  if '://' in target:continue
  file,sep,anchor=target.partition('#');path=SKILL/file if file else SKILL/name
  check(f'{name} link target {target}',path.resolve().is_file())
  if sep:
   anchors=[re.sub(r'[^\w -]','',h.strip().lower()).replace(' ','-') for h in re.findall(r'^#+ (.+)$',path.read_text(),re.M)]
   check(f'{name} heading {target}',anchor in anchors)
freeze=json.loads((ROOT/'validation/single-thread-tt-20261020/SOURCE-FREEZE.json').read_text())
check('frozen source is actual886 candidate',freeze['gated_candidate_source']==protocol['source_reference'])
check('recorded Release9/9',freeze['release_ctest']=='9/9passed')
check('recorded ASanUBSan9/9',freeze['asan_ubsan_ctest']=='9/9 passed')
check('recorded TSan9/9 default detector',freeze['tsan_ctest']=='9/9 passed; default deadlock detector unchanged')
check('recorded actualAPI7groups per3profiles',freeze['actual_api_groups_per_profile']==7 and len(freeze['actual_api_profiles'])==3)
check('recorded activeUCI8/8','8/8 passed' in freeze['active_uci_tsan_edges'])
check('recorded Windows8checks','8 Wine checks' in freeze['windows_validation'])
check('baseline observed literal categorical conflict','R3 — Categorically prohibited by the current wording' in (HERE/'red-agent.txt').read_text())
check('updated application recognizes reviewed exception','R3 — Eligible for bounded reviewed synchronization' in (HERE/'green-agent.txt').read_text())
result={'status':'PASS','checks':checks,'check_count':len(checks),'main_skill_word_count':len(main.split()),'scope':'documentation structure/references/recorded-evidence consistency only; no engine execution','fresh_agent_sample_count':{'original_skill':1,'updated_skill':1}}
(HERE/'static-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
