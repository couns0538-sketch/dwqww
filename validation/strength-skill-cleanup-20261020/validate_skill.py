"""Static project-skill metadata/link/evidence checks; launches no workload."""
from pathlib import Path
import datetime,hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SKILL=ROOT/'.agents/skills/validating-chess-strength/SKILL.md'
SCENARIOS=SKILL.with_name('scenarios.md')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
text=SKILL.read_text();assert text.startswith('---\n')
front=text.split('---\n',2)[1];assert len(front)<=1024
metadata={}
for line in front.splitlines():
    key,value=line.split(':',1);assert key not in metadata;metadata[key]=value.strip()
assert set(metadata)=={'name','description'}
assert re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',metadata['name'])
assert metadata['name']==SKILL.parent.name
assert metadata['description'].startswith('Use when ') and len(metadata['description'])<500
links=[]
for source in [SKILL,SCENARIOS]:
    for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',source.read_text()):
        if '://' in target or target.startswith('#'):continue
        path=(source.parent/target.split('#',1)[0]).resolve();assert path.is_file(),str(path)
        links.append({'source':str(source.relative_to(ROOT)),'target':target,'resolved':str(path.relative_to(ROOT)),'exists':True})
assert len(links)==6
before_skill=(OUT/'before-SKILL.md').read_text();before_cases=(OUT/'before-scenarios.md').read_text()
assert text.count('After any successful spawn, keep bounded cleanup/reaping')==1
assert SCENARIOS.read_text().startswith(before_cases)
assert SCENARIOS.read_text().count('## Evidence-persistence failure during cleanup')==1
protected=json.loads((OUT/'OLD-PROOF-PRESERVATION.json').read_text())
assert len(protected)==6 and all(sha(ROOT/name)==digest for name,digest in protected.items())
baseline=json.loads((OUT/'BASELINE-EVIDENCE.json').read_text())
assert sha(ROOT/baseline['source'])==baseline['source_sha256']==sha(OUT/baseline['raw_copy'])
report={'status':'STATIC_CHECKS_PASSED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'skill_sha256':sha(SKILL),'scenarios_sha256':sha(SCENARIOS),'frontmatter_valid':True,'frontmatter_validation':'Bounded validation of the current two scalar YAML fields; not a general YAML parser.','frontmatter':metadata,'relative_links':links,'relative_link_count':len(links),'all_relative_links_exist':True,'protected_old_proof_files':len(protected),'old_proofs_unchanged':True,'existing_mock_retained_byte_identical':True,'one_new_scenario':True,'engine_build_helper_test_network_or_git_executions':0,'global_or_cloud_skill_installation_claim':False}
(OUT/'STATIC-VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['status','skill_sha256','scenarios_sha256','relative_link_count','protected_old_proof_files']},indent=2))
