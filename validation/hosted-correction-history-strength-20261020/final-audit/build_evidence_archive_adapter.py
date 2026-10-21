"""Mandatory source/build evidence before any hosted readiness process. No execution."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import tarfile

RELEASE_FLAGS='-O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto'
BASELINE_TESTS=('forge_tests','forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests',
                'match_tool_tests','windows_validation_tests','uci_regression','ponder_regression','ownbook_regression')
CANDIDATE_TESTS=(BASELINE_TESTS[0],'forge_correction_history_tests',*BASELINE_TESTS[1:])

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_json(path):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate JSON key in '+str(path))
            result[key]=value
        return result
    return json.loads(Path(path).read_text(),object_pairs_hook=unique)

def relative_path(root,name):
    path=PurePosixPath(name)
    if not isinstance(name,str) or path.is_absolute() or '..' in path.parts or path.as_posix()!=name:
        raise ValueError('Unsafe evidence path: '+str(name))
    target=Path(root)/name
    if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Missing or unsafe required evidence: '+name)
    return target

def source_inventory(path,commit):
    inventory={}
    with tarfile.open(path) as archive:
        if archive.pax_headers.get('comment')!=commit:
            raise ValueError('Source archive commit identity mismatch: '+str(path))
        for member in archive:
            name=PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts or name.as_posix()!=member.name:
                raise ValueError('Unsafe source archive member')
            if member.isdir():continue
            if not member.isfile() or member.name in inventory:
                raise ValueError('Nonregular or duplicate source archive member')
            inventory[member.name]=hashlib.sha256(archive.extractfile(member).read()).hexdigest()
    if not inventory:raise ValueError('Empty source archive')
    return inventory

def required_paths():
    names=['source/fastchess.tar','fastchess-build-provenance.json','artifacts-SHA256.json',
           'collector.stdout','collector.stderr','collector-exit-code.txt']
    for label in ('baseline','candidate'):
        names += ['source/'+label+'.tar',label+'-build-provenance.json',label+'-compile-commands.json',
                  label+'-CMakeCache.txt',label+'-LastTest.log']
        for stage in ('configure','build','ctest'):
            names += [label+'-'+stage+suffix for suffix in ('.stdout','.stderr','-command.json')]
    for stage in ('compiler','fastchess-build'):
        names += [stage+suffix for suffix in ('.stdout','.stderr','-command.json')]
    return sorted(names)

def verify_stage(root,name):
    record=read_json(relative_path(root,name+'-command.json'))
    if type(record.get('exit_code')) is not int or record['exit_code']!=0 or not record.get('command'):
        raise ValueError('Unsuccessful or unrecorded build stage: '+name)
    for stream in ('stdout','stderr'):
        if record.get(stream+'_sha256')!=sha(relative_path(root,name+'.'+stream)):
            raise ValueError('Stage output hash mismatch: '+name)
    return record

def verify_build_evidence(root,cfg,baseline,candidate,fastchess):
    root=Path(root).resolve()
    required=[relative_path(root,name) for name in required_paths()]
    manifest_path=relative_path(root,'build-evidence-SHA256.json')
    manifest=read_json(manifest_path)
    if not isinstance(manifest,dict) or not set(required_paths()).issubset(manifest):
        raise ValueError('Required build evidence inventory is incomplete')
    consumed=[manifest_path]
    for name,digest in manifest.items():
        path=relative_path(root,name)
        if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest) or sha(path)!=digest:
            raise ValueError('Published build evidence hash mismatch: '+name)
        consumed.append(path)
    if (root/'collector-exit-code.txt').read_text().strip()!='0' or (root/'collector.stderr').read_bytes():
        raise ValueError('Collector did not finish cleanly')
    artifacts=read_json(root/'artifacts-SHA256.json')
    runtime={'baseline/forge':Path(baseline),'baseline/libforge_core.a':Path(baseline).parent/'libforge_core.a',
             'candidate/forge':Path(candidate),'candidate/libforge_core.a':Path(candidate).parent/'libforge_core.a',
             'runner/fastchess':Path(fastchess)}
    if set(artifacts)!=set(runtime):raise ValueError('Artifact inventory file set mismatch')
    for name,path in runtime.items():
        if not path.is_file() or path.is_symlink() or artifacts[name]!=sha(path):
            raise ValueError('Runtime artifact hash mismatch: '+name)
        # Archive serializer stores raw bytes with mode0600. Original hosted
        # executable-bit check cannot be replayed on relocated archive metadata.
        consumed.append(path)
    verify_stage(root,'compiler');verify_stage(root,'fastchess-build')
    if not re.search(r'g\+\+.*\b14\.',(root/'compiler.stdout').read_text()):
        raise ValueError('Compiler version evidence is not GCC14')
    for label,engine,names in [('baseline',baseline,BASELINE_TESTS),('candidate',candidate,CANDIDATE_TESTS)]:
        provenance=read_json(root/(label+'-build-provenance.json'))
        archive=root/'source'/(label+'.tar')
        inventory=source_inventory(archive,cfg[label+'_sha'])
        if (provenance.get('source_commit')!=cfg[label+'_sha'] or
                provenance.get('source_tar_sha256')!=sha(archive) or
                provenance.get('exported_source_sha256')!=inventory or
                provenance.get('last_test_log_sha256')!=sha(root/(label+'-LastTest.log'))):
            raise ValueError('Source/build provenance mismatch: '+label)
        for name in ('forge','libforge_core.a'):
            if provenance.get('built_artifacts_sha256',{}).get(name)!=sha(Path(engine).parent/name):
                raise ValueError('Executable/core provenance mismatch: '+label+'/'+name)
        for stage in ('configure','build','ctest'):verify_stage(root,label+'-'+stage)
        cache={}
        for line in (root/(label+'-CMakeCache.txt')).read_text().splitlines():
            match=re.match(r'([^:#]+):[^=]+=(.*)',line)
            if match:cache[match[1]]=match[2]
        if (cache.get('CMAKE_BUILD_TYPE')!='Release' or cache.get('CMAKE_CXX_FLAGS')!='' or
                cache.get('CMAKE_CXX_FLAGS_RELEASE')!=RELEASE_FLAGS or
                cache.get('CMAKE_INTERPROCEDURAL_OPTIMIZATION')!='OFF' or cache.get('FORGE_NATIVE')!='OFF' or
                Path(cache.get('CMAKE_CXX_COMPILER','')).name!='g++-14'):
            raise ValueError('Frozen compiler/cache configuration mismatch: '+label)
        commands=read_json(root/(label+'-compile-commands.json'))
        if not isinstance(commands,list) or not commands:raise ValueError('Empty compilation records')
        production={name for name in inventory if name.startswith('src/') and name.endswith('.cpp')}
        observed=set()
        for command in commands:
            tokens=command.get('arguments') or shlex.split(command.get('command',''))
            if (not tokens or Path(tokens[0]).name!='g++-14' or
                    not set(shlex.split(RELEASE_FLAGS)).issubset(tokens) or
                    any(t in ('-ffast-math','-Ofast') or t.startswith('-flto') or
                        (t.startswith('-ffp-contract=') and t!='-ffp-contract=off') for t in tokens)):
                raise ValueError('Frozen compile command flags mismatch: '+label)
            file=Path(command.get('file','')).as_posix()
            observed.update(name for name in production if file.endswith('/'+name))
        if observed!=production:raise ValueError('Production source compilation inventory incomplete: '+label)
        output=(root/(label+'-ctest.stdout')).read_text()
        passed=re.findall(r'^\s*(\d+)/(\d+)\s+Test\s+#\d+:\s+(\S+)\s+\.*\s+Passed\b',output,re.M)
        if ([(int(i),int(n),name) for i,n,name in passed]!=[(i,len(names),name) for i,name in enumerate(names,1)] or
                not re.search(r'100% tests passed, 0 tests failed out of '+str(len(names))+r'\b',output) or
                (root/(label+'-ctest.stderr')).read_bytes()):
            raise ValueError('Incomplete/wrong named CTest suite: '+label)
        last=(root/(label+'-LastTest.log')).read_text()
        if last.count('Test Passed.')!=len(names) or any('Testing: '+name+'\n' not in last for name in names):
            raise ValueError('LastTest completion evidence mismatch: '+label)
    fast=read_json(root/'fastchess-build-provenance.json')
    source_inventory(root/'source/fastchess.tar',cfg['fastchess_sha'])
    if (fast.get('source_commit')!=cfg['fastchess_sha'] or
            fast.get('source_tar_sha256')!=sha(root/'source/fastchess.tar') or
            fast.get('built_artifacts_sha256',{}).get('fastchess')!=sha(fastchess)):
        raise ValueError('Fastchess source/build provenance mismatch')
    return sorted(set(consumed+required),key=lambda path:path.as_posix())
