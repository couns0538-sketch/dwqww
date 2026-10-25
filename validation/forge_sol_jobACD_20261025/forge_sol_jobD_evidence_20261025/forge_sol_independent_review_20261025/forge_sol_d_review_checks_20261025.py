# Independent bounded review probes; no production source edits.
from pathlib import Path
import hashlib,importlib.util,json,os,sqlite3,sys
ROOT=Path('/workspace/forge-jobACD-D-review-20261025')
TOOL=Path('/workspace/forge-jobACD-D-20261025/forge_sol_datafilter_20261025.py')
spec=importlib.util.spec_from_file_location('forge_sol_review_filter',TOOL);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
work=ROOT/'forge_sol_review_fixtures_20261025';work.mkdir(exist_ok=False)
def row(tag,score=12,meta=4,hce=34):return m.Record(bytes([tag])+bytes(31),score,meta,hce)
def write(stem,rows):
 p=work/(stem+'.pos');m.write_records(p,p.with_suffix('.hce'),rows);return p
checks=[]
# Positive bytes/holdout/identity control, including changed result+score.
t=write('t_review',[row(1),row(2,score=-600,meta=0),row(2,score=600,meta=4),row(2,score=600,meta=5)])
h=write('h013_review',[row(1,score=-13,meta=0)])
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in work.iterdir() if p.is_file()}
s=m.filter_data([t],[h],work,work/'forge_sol_review_positive_20261025',seed=17)
kept=list(m.read_records(next((work/'forge_sol_review_positive_20261025').glob('*.pos')),next((work/'forge_sol_review_positive_20261025').glob('*.hce'))))
assert [(r.board[0],r.meta&1) for r in kept]==[(2,0),(2,1)]
assert s['supplied_holdout_overlap']==0 and s['output_duplicate_positions']==0
assert before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in work.iterdir() if p.is_file()}
checks.append({'name':'board+STM_identity_and_readonly_inputs','status':'PASS'})
# Production collision path rejects distinct identity under the same digest.
db=sqlite3.connect(':memory:');db.execute('CREATE TABLE seen(hash BLOB PRIMARY KEY,key BLOB NOT NULL)');m.insert_key(db,'seen',b'x'*32,b'a'*33)
try:m.insert_key(db,'seen',b'x'*32,b'b'*33)
except ValueError as e:assert 'collision' in str(e)
else:raise AssertionError('collision was silently treated as duplicate')
checks.append({'name':'hash_collision_rejects_false_dedupe','status':'PASS'});db.close()
# Hardlinked holdout alias is excluded without trying to open guessed HCE.
alias=work/'t_hardlink_review.pos';os.link(h,alias)
s=m.filter_data([alias],[h],work,work/'forge_sol_review_hardlink_20261025')
assert s['totals']['kept']==0 and s['excluded_holdout_shards']==[alias.name]
checks.append({'name':'hardlink_holdout_alias_excluded','status':'PASS'})
# Corrupt only a new writer's return product. Independent reread must detect overlap.
original=m.write_records
held=row(1)
def corrupt(pos,hce,records):
 n=original(pos,hce,records)
 if n:
  b=bytearray(Path(pos).read_bytes());b[16:48]=held.board;Path(pos).write_bytes(b)
 return n
m.write_records=corrupt
failed=work/'forge_sol_review_bad_writer_20261025'
try:m.filter_data([t],[h],work,failed)
except ValueError as e:assert 'overlap/uniqueness/count audit failed' in str(e)
else:raise AssertionError('independent audit accepted a valid-shaped holdout output')
finally:m.write_records=original
assert (failed/'forge_sol_datafilter_failed_20261025.json').is_file()
assert not (failed/'forge_sol_datafilter_manifest_20261025.md5').exists()
checks.append({'name':'independent_output_reread_detects_injected_holdout_and_leaves_failure_unsealed','status':'PASS'})
result={'tool_sha256':hashlib.sha256(TOOL.read_bytes()).hexdigest(),'scope':'Small original reviewer fixtures only; no full sample, native timing, training, Git or source mutation','checks':checks,'status':'PASS'}
(ROOT/'forge_sol_d_review_checks_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
