#!/usr/bin/env python3
"""SOURCE-ONLY RSS draft repair; preserves original6eb988 and controls."""
from pathlib import Path
import ast
import hashlib
import json

HERE=Path(__file__).resolve().parent
OLD=HERE/'forge_sol_S11_resource_guard_v3_20261027.py'
OLD_SHA='6eb98832363e901eff8afd966c972fc758ee8ff1838a04bb40c634a2b30578aa'
S18=Path('/tmp/forge_sol_S18_rss_scope_v3_checkpoint_20261027/prep/forge_sol_S18_train_selected_v3_20261027.py')
S18_SHA='ab02ac6a4579bf37b3ea65f2bb07c4d5d08a33bd6b19d6130bc3f8d1369f1e76'

ADAPTATION='''def _owned_task_identity(pid,tid):
    raw=read_proc_status(Path('/proc')/str(pid)/'task'/str(tid)/'stat')
    if int(raw.split(' (',1)[0])!=tid:raise ValueError('owned stat task PID mismatch')
    tail=raw[raw.rfind(')')+2:].split()
    return (tid,int(tail[19]),int(tail[2]))


def read_owned_rss_bytes(pid,*,observation=None):
    if type(pid) is not int or pid<=0:raise ValueError('positive owned PID required')
    info={} if observation is None else observation
    info.clear();info.update(owned_pid=pid,scope='UNAVAILABLE',tasks=[])
    def parse(raw,tid):
        fields={}
        for line in raw.splitlines():
            key,sep,value=line.partition(':')
            if sep and key in ('Pid','Tgid','State','VmRSS'):
                if key in fields:raise ValueError('duplicate owned status identity/RSS field')
                fields[key]=value.strip()
        if int(fields.get('Pid','-1'))!=tid or int(fields.get('Tgid','-1'))!=pid:raise ValueError('owned task Pid/Tgid mismatch')
        state=fields.get('State','').split()
        if not state:raise ValueError('owned task state unavailable')
        rss=None
        if 'VmRSS' in fields:
            parts=fields['VmRSS'].split()
            if len(parts)!=2 or parts[1]!='kB' or int(parts[0])<0:raise ValueError('malformed owned VmRSS')
            rss=int(parts[0])*1024
        return state[0],rss
    raw=read_proc_status(Path('/proc')/str(pid)/'status');info['leader_status_original']=raw
    state,rss=parse(raw,pid);info['leader_state']=state
    if rss is not None:
        info.update(scope='OWNED_LEADER',selected_tid=pid,rss_bytes=rss);return rss
    if state not in ('Z','X'):raise ValueError('owned VmRSS unavailable on unproven live leader')
    leader_identity=_owned_task_identity(pid,pid);ids=owned_task_ids(pid)
    if not ids or pid not in ids:raise ValueError('owned exited-leader task inventory unavailable')
    samples=[];all_dead=True
    for tid in ids:
        before=_owned_task_identity(pid,tid)
        if before[2]!=leader_identity[2]:raise ValueError('owned task group mismatch')
        raw=read_proc_status(Path('/proc')/str(pid)/'task'/str(tid)/'status')
        thread_state,value=parse(raw,tid);after=_owned_task_identity(pid,tid)
        if before!=after:raise ValueError('owned task identity changed during RSS sample')
        info['tasks'].append({'tid':tid,'identity':before,'state':thread_state,'rss_bytes':value,'status_original':raw})
        if thread_state not in ('Z','X'):
            all_dead=False
            if value is None:raise ValueError('owned live-task VmRSS unavailable')
        if value is not None:samples.append((value,tid))
    if owned_task_ids(pid)!=ids or _owned_task_identity(pid,pid)!=leader_identity:raise ValueError('owned task inventory/leader identity changed during RSS sample')
    if samples and max(samples)[0]>0:
        rss,tid=max(samples)
        info.update(scope='OWNED_LIVE_THREAD_SHARED_MM' if not all_dead else 'OWNED_RETAINED_TASK_SHARED_MM',selected_tid=tid,rss_bytes=rss,aggregation='maximum shared-MM task RSS, never sum threads')
        return rss
    if not all_dead:raise ValueError('owned live-task RSS unproven')
    # S11-specific EOF adaptation: zero is allowed only after the bounded,
    # stable, identity-checked task inventory proved every task Z/X and no RSS.
    info.update(scope='OWNED_VERIFIED_ALL_TASKS_EXITED',rss_bytes=0,aggregation='verified all tasks exited; no live shared MM observed')
    return 0


'''
METHOD='''    def _read_rss(self,pid):
        observation={}
        try:
            value=read_owned_rss_bytes(pid,observation=observation)
            scope=observation['scope'];self.RSS_scope_counts[scope]=self.RSS_scope_counts.get(scope,0)+1
            self.last_RSS_observation=observation
            if scope!='OWNED_LEADER' and self.first_RSS_fallback_observation is None:self.first_RSS_fallback_observation=observation
            return value
        except FileNotFoundError:return None
'''


def main():
    assert hashlib.sha256(OLD.read_bytes()).hexdigest()==OLD_SHA
    assert hashlib.sha256(S18.read_bytes()).hexdigest()==S18_SHA
    source=OLD.read_text();tree=ast.parse(source);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_read_rss')
    lines=source.splitlines(True);source=''.join(lines[:method.lineno-1])+METHOD+''.join(lines[method.end_lineno:])
    upstream=S18.read_text().splitlines(True);upstream_tree=ast.parse(''.join(upstream))
    copied=[]
    for name in ['read_proc_status','owned_task_ids']:
        node=next(n for n in upstream_tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        copied.append(''.join(upstream[node.lineno-1:node.end_lineno]))
    source=source.replace('class OwnedResourceGuard:', '\n\n'.join(copied)+'\n\n'+ADAPTATION+'class OwnedResourceGuard:',1)
    source=source.replace('        self.maximum_rss=0;', '        self.RSS_scope_counts={};self.last_RSS_observation=None;self.first_RSS_fallback_observation=None\n        self.maximum_rss=0;',1)
    source=source.replace("            'guard_launches_or_signals_processes':False}","            'RSS_scope_counts':dict(self.RSS_scope_counts),'last_RSS_observation':self.last_RSS_observation,'first_RSS_fallback_observation':self.first_RSS_fallback_observation,\n            'guard_launches_or_signals_processes':False}",1)
    out=HERE/'forge_sol_S11_resource_guard_v3_reviewv2_20261027.py'
    if out.exists():raise FileExistsError('new source draft required')
    out.write_text(source)
    now=ast.parse(source)
    for name in ['read_proc_status','owned_task_ids']:
        a=next(n for n in upstream_tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        b=next(n for n in now.body if isinstance(n,ast.FunctionDef) and n.name==name)
        assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
    old_methods={n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
    newcls=next(n for n in now.body if isinstance(n,ast.ClassDef))
    new_methods={n.name:ast.dump(n,include_attributes=False) for n in newcls.body if isinstance(n,ast.FunctionDef)}
    changed=[name for name in old_methods if old_methods[name]!=new_methods[name]]
    assert set(changed)=={'__init__','_read_rss','snapshot'},changed
    receipt={'scope':'SOURCE_ONLY_RSS_REPAIR_NO_NATIVE','original_draft_sha256':OLD_SHA,'reviewv2_helper_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'own_S18_source_sha256':S18_SHA,'exact_S18_functions_AST_reused':['read_proc_status','owned_task_ids'],'changed_resource_methods':changed,'guard_cadence_deadline_stop_identity_membership_logic_unchanged':True,'native_retries':0}
    (HERE/'forge_sol_S11_resource_guard_v3_RSS_repair_source_receipt_20261027.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n');print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
