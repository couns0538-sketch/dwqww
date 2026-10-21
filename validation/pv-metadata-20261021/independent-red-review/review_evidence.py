"""Independent RED evidence check. File reads only outside this review directory."""
import datetime, hashlib, json, pathlib, re, tarfile
ROOT=pathlib.Path('/workspace/dwqww')
P=ROOT/'validation/pv-metadata-20261021'
OUT=P/'independent-red-review'
def digest(data): return hashlib.sha256(data).hexdigest()
def filehash(path): return digest(pathlib.Path(path).read_bytes())
def load(name): return json.loads((P/name).read_text())
checks=[]
def check(name, condition):
    checks.append({'check':name,'pass':bool(condition)})
    if not condition: raise AssertionError(name)
def apply_memory(original, patch):
    source=original.decode().splitlines(keepends=True)
    lines=patch.decode().splitlines(keepends=True)
    out=[]; pos=0; i=0
    while i<len(lines):
        if not lines[i].startswith('@@ '): i+=1; continue
        m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[i]); assert m
        start=int(m[1])-1; assert start>=pos
        out.extend(source[pos:start]); pos=start; old=0; new=0; i+=1
        while i<len(lines) and not lines[i].startswith(('@@ ','--- ','+++ ')):
            line=lines[i]; tag=line[:1]
            if tag in (' ','-'):
                assert source[pos]==line[1:]; pos+=1; old+=1
            if tag in (' ','+'):out.append(line[1:]); new+=1
            assert tag in (' ','-','+')
            i+=1
        assert old==int(m[2] or 1) and new==int(m[4] or 1)
    out.extend(source[pos:]); return ''.join(out).encode()
def archive_members(path):
    data=pathlib.Path(path).read_bytes(); assert data[:8]==b'!<arch>\n'
    pos=8; names=b''; members={}
    while pos<len(data):
        head=data[pos:pos+60]; assert len(head)==60 and head[58:60]==b'`\n'
        name=head[:16].decode().strip(); n=int(head[48:58]); pos+=60
        payload=data[pos:pos+n]; assert len(payload)==n; pos+=n+(n%2)
        if name=='//': names=payload; continue
        if name in ('/','/SYM64/'): continue
        if name.startswith('/') and name[1:].isdigit():
            off=int(name[1:]); name=names[off:names.index(b'/\n',off)].decode()
        else:name=name.rstrip('/')
        assert name not in members
        members[name]=digest(payload)
    assert pos==len(data)
    return members
receipt=load('red-attempt1/result.json')
check('authoritative original RED receipt SHA',filehash(P/'red-attempt1/result.json')=='75b75b5054aa5c34e366005f70c9b27ea82e59abc04b73a1c3a80574d2f2ea7e')
check('RED source and status', receipt['source_commit']=='2e151d019bc58dff2ab4e76e99ef99516af8d222' and receipt['status']=='RED_REPRODUCED_WITH_NATURAL_WITNESS')
source=load('RED-ISOLATED-SOURCE.json')
check('original export TAR SHA',filehash(ROOT/source['archive_path'])==source['archive_sha256']=='05ccb2a72c6a2b1c45d91eccb6cbda7cc101490451a3975a4946c7a594867c6b')
with tarfile.open(ROOT/source['archive_path']) as tar:
    original={a.name:tar.extractfile(a).read() for a in tar if a.isfile()}
check('76 original inputs and recorded SHA inventory',{n:digest(b) for n,b in original.items()}==source['source_before_patch_sha256'] and len(original)==76)
actual={n:(pathlib.Path(source['source_root'])/n).read_bytes() for n in original}
check('actual 76 diagnostic inputs match recorded hashes',{n:digest(b) for n,b in actual.items()}==source['source_after_patch_sha256'])
check('only source difference is search.cpp',[n for n in original if original[n]!=actual[n]]==['src/search.cpp'])
red=apply_memory(original['src/search.cpp'],(P/'diagnostic-unapplied.patch').read_bytes())
check('observer diff applies exactly in memory and reproduces actual compiled RED source',red==actual['src/search.cpp'])
proposed=apply_memory(original['src/search.cpp'],(P/'proposed-unapplied.patch').read_bytes())
green=apply_memory(original['src/search.cpp'],(P/'green-diagnostic-unapplied.patch').read_bytes())
check('proposed production patch adds exactly save and restore lines',proposed.decode().replace('            const bool saved_tt_pv = ss->tt_pv;\n','',1).replace('            ss->tt_pv = saved_tt_pv;\n','',1)==original['src/search.cpp'].decode())
check('GREEN diff is exactly RED observer plus same proposed save/restore',green.decode().replace('            const bool saved_tt_pv = ss->tt_pv;\n','',1).replace('            ss->tt_pv = saved_tt_pv;\n','',1)==red.decode())
core=load('RED-CORE-MEMBER-AUDIT.json')
before=archive_members(core['baseline_core']); after=archive_members(core['diagnostic_core'])
check('actual seven core archive members',set(before)==set(after)=={m['member'] for m in core['members']} and len(before)==7)
check('actual core member SHA inventories equal published audit',all(before[m['member']]==m['baseline_sha256'] and after[m['member']]==m['diagnostic_sha256'] for m in core['members']))
check('six nonsearch objects byte-identical including NNUE',[n for n in before if before[n]!=after[n]]==['search.cpp.o'])
for step in receipt['steps']:
    for suffix in ['stdin','stdout','stderr']:
        check(step['label']+' original '+suffix+' SHA',filehash(P/'red-attempt1'/f"{step['label']}.{suffix}")==step[suffix+'_sha256'])
    expected=1 if step['label']=='actual-worker-probe' else 0
    check(step['label']+' original expected exit and recorded closed ownership',step['exit_code']==step['post_cleanup_exit_code']==expected and step['cleanup']['no_live_owned_processes'] and not step['cleanup']['before'] and not step['cleanup']['after'] and not step['cleanup']['unexpected_live_members_after_command'])
check('six completed recorded command groups',len(receipt['steps'])==6)
for name,h in receipt['frozen_inputs'].items(): check('frozen input '+name,filehash(name if pathlib.Path(name).is_absolute() else ROOT/name)==h==receipt['final_input_hashes'][name])
for name,h in receipt['artifacts'].items():check('actual RED build artifact '+name,filehash(name)==h)
probe=next(s['command'][0] for s in receipt['steps'] if s['label']=='actual-worker-probe')
check('actual Worker probe binary SHA',filehash(probe)==receipt['probe_sha256'])
pre=load('PRE-SPAWN-FAILURE-attempt1.json'); correction=load('ROOT-PREFLIGHT-CORRECTION.json')
old=load('EXECUTION-CLEARANCE.pre-spawn-failed-attempt1.json'); current=load('EXECUTION-CLEARANCE.red-authorized.json')
clearance_changes={k:{'before':old.get(k),'after':current.get(k)} for k in old.keys()|current.keys() if old.get(k)!=current.get(k)}
check('corrected immutable RED clearance SHA',filehash(P/'EXECUTION-CLEARANCE.red-authorized.json')==correction['current_clearance_sha256']=='e68070b657f60a08e4069794226791182ec1fa12233a923e988c495f7d09265d')
check('no failed engine rescue declared',not correction['failed_engine_experiment_rescued'] and not correction['code_protocol_probe_or_source_changed'] and not correction['compiler_engine_or_attempt_dirs_created_before_correction'])
replay=load('independent-red-review/trace-replay.json')
for i in replay['inputs']:check('independent legal replay immutable input '+i['path'],filehash(i['path'])==i['sha256'])
# Reparse natural event accounting independently of the application report.
lines=(P/'red-attempt1/actual-natural-bench11.stderr').read_text().splitlines()
traces=[json.loads(l[len('PV_TRACE '):]) for l in lines if l.startswith('PV_TRACE ')]
summaries=[json.loads(l[len('PV_SUMMARY '):]) for l in lines if l.startswith('PV_SUMMARY ')]
check('natural full emitted losses',len(traces)==25 and len(summaries)==8 and sum(s['events'] for s in summaries)==716 and sum(s['changed'] for s in summaries)==sum(s['emitted'] for s in summaries)==25 and max(s['emitted'] for s in summaries)<64)
check('all observed natural losses are caller PV true to false',all(t['caller_pv']==t['before']==1 and t['after']==0 for t in traces))
check('instrumented incheck/raw/static fields unchanged',all(t['in_check_before']==t['in_check_after'] and t['raw_before']==t['raw_after'] and t['eval_before']==t['eval_after'] for t in traces))
check('24 observed current moves changed',sum(t['current_before']!=t['current_after'] for t in traces)==24)
inputs={str(P/'red-attempt1/result.json'):filehash(P/'red-attempt1/result.json'),str(P/'RED-ISOLATED-SOURCE.json'):filehash(P/'RED-ISOLATED-SOURCE.json'),str(P/'RED-CORE-MEMBER-AUDIT.json'):filehash(P/'RED-CORE-MEMBER-AUDIT.json'),str(P/'independent-red-review/trace-replay.json'):filehash(P/'independent-red-review/trace-replay.json')}
result={'schema':'independent-pv-metadata-red-static-review-v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_RED_CAUSAL_EVIDENCE_SUPPORTS_SEPARATE_GREEN_EXPERIMENT','source_commit':receipt['source_commit'],'checks':checks,'checks_passed':len(checks),'source_files':len(original),'unchanged_nonsearch_sources':75,'core_member_hashes_baseline':before,'core_member_hashes_red':after,'clearance_metadata_changes':clearance_changes,'natural':{'events':716,'losses':25,'traces':25,'summaries':8,'current_move_changes':24},'inputs':inputs,'executed_engine_or_compiler_or_git':False,'production_source_changed_by_review':False,'green_behavior_or_elo_conclusion':None}
(OUT/'REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks_passed':len(checks),'source_files':76,'unchanged_nonsearch_objects':6,'natural_losses':25,'clearance_changes':list(clearance_changes)},sort_keys=True))
