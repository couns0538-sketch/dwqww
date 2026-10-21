"""Complete physical /workspace discovery, sanitized read-only Git metadata only."""
import os,stat,json,hashlib,subprocess,re
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime,timezone
BASE=Path('/workspace');OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def stamp():return datetime.now(timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def git(where,*args,gitdir=False):
 command=['git','--no-optional-locks']+(['--git-dir='+str(where)] if gitdir else ['-C',str(where)])+list(args)
 env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env['GIT_OPTIONAL_LOCKS']='0';env['GIT_TERMINAL_PROMPT']='0'
 r=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
 # No raw stderr or remote URL is persisted; errors may embed local config values.
 return r.returncode,r.stdout.decode('utf-8','replace').strip(),{'argv':command,'exit_code':r.returncode,'stderr_bytes':len(r.stderr),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()}
def remote(value):
 if '://' in value:
  u=urlsplit(value);return {'transport':u.scheme,'host':u.hostname,'repository_path':u.path.strip('/').removesuffix('.git')}
 m=re.fullmatch(r'(?:[^@/]+@)?([^/:]+):(.+)',value)
 if m:return {'transport':'scp_ssh','host':m[1],'repository_path':m[2].strip('/').removesuffix('.git')}
 return {'transport':'local_path','host':None,'repository_path':str(Path(value).expanduser())}
started=stamp();prior=[]
for name in ['repository-discovery-current-workspace-find.json','repository-discovery-latest.json','forge-onboarding-repository-rescan-latest.json','forge-onboarding-repository-rescan-20261020.json']:
 p=BASE/'.cloud-setup'/name
 if p.is_file():prior.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
errors=[];links=[];markers=[];custom=[];dirs=entries=regular=other=0;stack=[BASE];seen=set()
# Every physical directory is scanned, including Git objects, caches, artifacts and hidden paths.
with (OUT/'DIRECTORIES.jsonl').open('x') as listing:
 while stack:
  directory=stack.pop()
  try:
   meta=directory.stat();identity=(meta.st_dev,meta.st_ino)
   if identity in seen:
    listing.write(json.dumps({'path':str(directory),'action':'already_scanned_physical_alias','device':meta.st_dev,'inode':meta.st_ino})+'\n');continue
   seen.add(identity)
   with os.scandir(directory) as scan:items=list(scan)
  except OSError as e:
   errors.append({'path':str(directory),'operation':'scandir/stat','errno':e.errno,'error_type':type(e).__name__});continue
  dirs+=1;entries+=len(items);names={x.name for x in items}
  listing.write(json.dumps({'path':str(directory),'entries':len(items),'device':meta.st_dev,'inode':meta.st_ino})+'\n')
  if 'HEAD' in names and ('objects' in names or 'commondir' in names):custom.append(str(directory))
  for item in items:
   p=Path(item.path)
   try:
    info=item.stat(follow_symlinks=False)
    if item.name=='.git':markers.append({'path':str(p),'kind':'symlink' if stat.S_ISLNK(info.st_mode) else 'directory' if stat.S_ISDIR(info.st_mode) else 'file' if stat.S_ISREG(info.st_mode) else 'other'})
    if stat.S_ISLNK(info.st_mode):
     target=p.resolve(strict=False);record={'path':str(p),'resolved_target':str(target),'followed':False,'reason':'physical scan; internal targets scanned under real paths, external targets outside workspace scope'}
     try:
      targetstat=p.stat();record['target_kind']='directory' if stat.S_ISDIR(targetstat.st_mode) else 'file' if stat.S_ISREG(targetstat.st_mode) else 'other';record['target_within_workspace']=target.is_relative_to(BASE)
     except OSError as e:record.update(target_kind='unavailable',errno=e.errno,error_type=type(e).__name__)
     links.append(record)
    elif stat.S_ISDIR(info.st_mode):stack.append(p)
    elif stat.S_ISREG(info.st_mode):regular+=1
    else:other+=1
   except (OSError,RuntimeError) as e:errors.append({'path':str(p),'operation':'lstat/resolve','errno':getattr(e,'errno',None),'error_type':type(e).__name__})
candidates={};gitfiles=[]
for marker in markers:
 p=Path(marker['path']);candidates.setdefault(str(p.parent),{'checkout_path':str(p.parent),'marker':marker})
 if marker['kind']=='file':
  try:
   raw=p.read_text();match=re.fullmatch(r'gitdir: (.+)\s*',raw)
   if match:gitfiles.append({'marker':str(p),'gitdir':str((p.parent/match[1].strip()).resolve()),'parse':'valid_gitfile'})
   else:gitfiles.append({'marker':str(p),'parse':'not_gitdir_pointer','bytes':p.stat().st_size,'sha256':sha(p)})
  except OSError as e:errors.append({'path':str(p),'operation':'read_gitfile','errno':e.errno,'error_type':type(e).__name__})
repositories=[];commands=[]
for path,seed in sorted(candidates.items()):
 rc,root,facts=git(Path(path),'rev-parse','--show-toplevel');commands.append(facts)
 if rc:
  repositories.append({**seed,'classification':'empty_platform_marker' if path=='/workspace' and not list(Path(path,'.git').iterdir()) else 'unresolved_git_marker','git_validation_exit':rc});continue
 real=str(Path(root).resolve());rc,head,facts=git(Path(path),'rev-parse','HEAD');commands.append(facts)
 rcgit,gitdir,facts=git(Path(path),'rev-parse','--absolute-git-dir');commands.append(facts)
 rcrem,remnames,facts=git(Path(path),'remote');commands.append(facts);remotes=[]
 if rcrem==0:
  for name in remnames.splitlines():
   rr,url,facts=git(Path(path),'config','--get','remote.'+name+'.url');commands.append(facts)
   if rr==0:remotes.append({'name':name,**remote(url)})
 if real=='/workspace/dwqww':classification='retained_project'
 elif real=='/workspace/.cloud-setup/fastchess':classification='pinned_fastchess_dependency_not_project'
 elif '/strength-openings-research-' in real and real.endswith('/books'):classification='opening_book_dependency_not_project'
 elif '/git-preservation-smoke/throwaway-repo' in real:classification='provenance_smoke_fixture_not_project'
 else:classification='unclassified_checkout_requires_root_review'
 repositories.append({**seed,'real_git_root':real,'absolute_git_dir':gitdir if rcgit==0 else None,'head':head if rc==0 else None,'head_valid_full_oid':bool(re.fullmatch('[0-9a-f]{40,64}',head)) if rc==0 else False,'remotes_sanitized':remotes,'classification':classification})
# Validate alternate Git metadata directories even if their checkout uses a custom pointer.
known={x.get('absolute_git_dir') for x in repositories};metadata=[]
for directory in sorted(set(custom)):
 rc,bare,facts=git(Path(directory),'rev-parse','--is-bare-repository',gitdir=True);commands.append(facts)
 row={'git_metadata_path':directory,'associated_discovered_checkout':directory in known,'validation_exit':rc,'is_bare':bare=='true' if rc==0 else None}
 if rc==0 and directory not in known:
  rr,head,facts=git(Path(directory),'rev-parse','HEAD',gitdir=True);commands.append(facts);row['head']=head if rr==0 else None
  rr,worktree,facts=git(Path(directory),'config','--get','core.worktree',gitdir=True);commands.append(facts);row['configured_worktree']=str((Path(directory)/worktree).resolve()) if rr==0 else None
 metadata.append(row)
retained=[x for x in repositories if x['classification']=='retained_project'];assert len(retained)==1
rc,head_after,facts=git(Path(retained[0]['real_git_root']),'rev-parse','HEAD');commands.append(facts)
retained[0]['head_at_end']=head_after if rc==0 else None;retained[0]['head_stable_during_git_inspection']=head_after==retained[0]['head']
external=[x for x in links if x.get('target_kind')=='directory' and not x.get('target_within_workspace')]
blockers=[x for x in repositories if x['classification'] in ('unresolved_git_marker','unclassified_checkout_requires_root_review')]
blockers += [x for x in metadata if x['validation_exit']==0 and not x['associated_discovered_checkout']]
result={'status':'COMPLETE_PHYSICAL_WORKSPACE_DISCOVERY' if not errors and not blockers else 'DISCOVERY_WITH_EXPLICIT_LIMITATIONS','started_utc':started,'completed_utc':stamp(),'scope':'All physical directories and entries below /workspace, no depth limit, no excluded directories, no truncated marker/alias/error lists. Directory symlinks recorded without recursively following aliases; external targets are outside physical workspace scope.','physical_directories':dirs,'entries_seen':entries,'regular_files':regular,'other_entries':other,'symlinks':len(links),'external_directory_aliases':len(external),'traversal_errors':errors,'blockers':blockers,'markers':markers,'gitfiles':gitfiles,'custom_git_metadata':metadata,'repositories_all_classifications':repositories,'retained_project_membership':[{'root':x['real_git_root'],'head':x['head_at_end'],'remote':x['remotes_sanitized']} for x in retained],'dependency_policy':'Fastchess and opening-book repositories are dependencies, smoke repository is a fixture, empty/workspace marker is platform metadata; only /workspace/dwqww is retained project membership. Source exports/build/archive/toolchain/package trees are physical scanned data, not independent repositories without a validated Git root.','prior_receipts':prior,'git_operations':'Local rev-parse/config --get/remote listing only, GIT_OPTIONAL_LOCKS=0; no index/config/ref/network writes. Remote userinfo/query/fragment never persisted.','source_repository_config_mutations':0,'external_network_actions':0}
save(OUT/'SYMLINKS.json',links);save(OUT/'GIT-COMMAND-FACTS.json',commands);save(OUT/'DISCOVERY.json',result);print(json.dumps({'status':result['status'],'directories':dirs,'entries':entries,'symlinks':len(links),'errors':len(errors),'blockers':len(blockers),'retained':result['retained_project_membership'],'all_checkout_classifications':[{k:x.get(k) for k in ('checkout_path','classification','head')} for x in repositories]},indent=2))
