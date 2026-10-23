"""Publishable net-only source revision using a private index; preserve active checkout."""
from pathlib import Path
import subprocess, tempfile, os, json, hashlib
R=Path('/workspace/dwqww');H=Path('/workspace/forge-nnue-handoff-20261023');BASE='1ab50b2dd64d9b2f752f7f1285f6968cad2fd792'
F=H/'full-trained-net-freeze-attempt1';freeze=json.loads((F/'FREEZE.json').read_text());net=F/'nnue_weights.inc';net_sha=hashlib.sha256(net.read_bytes()).hexdigest()
assert net_sha==freeze['chosen']['inc_sha256'] and freeze['chosen']['changed_quantized_parameters']>0
out=H/'net-only-source-branch-attempt1';out.mkdir(exist_ok=False)
def git(*args,env=None,data=None):return subprocess.check_output(['git',*args],cwd=R,env=env,input=data)
head=git('rev-parse','HEAD').decode().strip();original_index=git('write-tree').decode().strip()
branch='forge/nnue-net-20261023-'+net_sha[:12];ref='refs/heads/'+branch
assert subprocess.run(['git','show-ref','--verify','--quiet',ref],cwd=R).returncode==1
with tempfile.TemporaryDirectory(dir=H,prefix='private-net-index-') as temp:
 env={**os.environ,'GIT_INDEX_FILE':str(Path(temp)/'index')}
 git('read-tree',BASE,env=env)
 blob=git('hash-object','-w','--stdin',data=net.read_bytes()).decode().strip()
 git('update-index','--cacheinfo','100644,'+blob+',src/nnue_weights.inc',env=env)
 tree=git('write-tree',env=env).decode().strip()
 message=('Forge6.4.24 trained residual-network trial '+net_sha[:12]+'\n\nOnly replace the network include from base1ab; search and all other source bytes remain unchanged. Experimental trial, not Elo accepted. Source and training evidence: forge/nnue-pipeline-20261023, frozen network '+net_sha+'.\n\nIdea source: supplied SOL_PROMPT.md and https://github.com/jw1912/bullet high-level training descriptions; no external engine code copied.\n')
 commit=git('commit-tree',tree,'-p',BASE,data=message.encode()).decode().strip()
 assert git('diff','--name-only',BASE,commit).decode().splitlines()==['src/nnue_weights.inc']
 assert git('show',commit+':src/nnue_weights.inc')==net.read_bytes()
 git('update-ref',ref,commit,'0'*40)
assert git('rev-parse','HEAD').decode().strip()==head and git('write-tree').decode().strip()==original_index
assert (R/'src/nnue_weights.inc').read_bytes()==git('show',BASE+':src/nnue_weights.inc')
result={'status':'ISOLATED_NET_ONLY_SOURCE_COMMIT_CREATED_NOT_YET_PUSHED_OR_QUALIFIED','branch':branch,'commit':commit,'parent_baseline':BASE,'only_changed_path':'src/nnue_weights.inc','net_sha256':net_sha,'freeze_sha256':hashlib.sha256((F/'FREEZE.json').read_bytes()).hexdigest(),'active_checkout_head_unchanged':head,'active_index_tree_unchanged':original_index,'git_diff_name_only':['src/nnue_weights.inc'],'qualification':'Actual full Release/ASan/Wine builds and tests must follow this source commit; no strength acceptance.'}
(out/'SOURCE-BRANCH.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
