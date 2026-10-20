#!/usr/bin/env python3
"""Independent inventory/provenance audit; no engine or runner main execution."""
from pathlib import Path, PurePosixPath
import ast
import datetime
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
import traceback
import zipfile

sys.dont_write_bytecode = True
REPO=Path('/workspace/dwqww')
STAGE=Path('/workspace/.cloud-setup/forge-6.4.8-windows-validation-bundle with spaces')
ARCHIVE=REPO/'releases/forge-6.4.8-windows-validation-bundle.zip'
OLD_ARCHIVE=REPO/'releases/forge-6.4.2-windows-validation-bundle.zip'
EVIDENCE=REPO/'validation/windows-native-648-20261019'
STANDALONE=REPO/'releases/forge-6.4.8-candidate-windows-zen5'
COMMIT='7125b3379a850de34041d42529cf95993607f93c'
EXPECTED_SHA='253f33c129c0f5d4301354f755e03e876c7a76c6da18e13307facaceba7b4e73'
EXPECTED_BYTES=30272872
EXPECTED_MANIFEST_SHA='3a2f1416434fe5737a720cb70170f8825575d5fd603cda134471a5bd7feb4764'
EXPECTED_OLD_SHA='27022666ef6e9eb14ce5b84109810be3f6caa1d97a25066409f915dd0029367c'
EXPECTED_ENGINE_SHA='e39a240e3f7380e84c4e585013c2d602cba379f15e9e23d7a036a9712c415644'
PIN='60d7a7a26c6b0582a15c112fb29a1829bef2adb3'
OUTPUT=Path(__file__).with_suffix('.json')
checks=[]
findings=[]
sha_bytes=lambda b:hashlib.sha256(b).hexdigest()
sha=lambda p:sha_bytes(p.read_bytes())
load=lambda p:json.loads(p.read_text())

def check(name,condition,detail=None):
    item={'name':name,'passed':bool(condition)}
    if detail is not None:item['detail']=detail
    checks.append(item)
    if not condition:findings.append({'check':name,'detail':detail})

def inventory(root):
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}

def safe(name):
    rel=PurePosixPath(name)
    return bool(name and name.isascii() and '\\' not in name and ':' not in name and not rel.is_absolute()
                and '..' not in rel.parts and name==rel.as_posix() and name!='.')

def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args])

def archive_contents(path):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        roots={PurePosixPath(name).parts[0] for name in names}
        assert len(roots)==1
        root=roots.pop()
        return root,{name[len(root)+1:]:z.read(name) for name in names if not name.endswith('/')},names,z.testzip()

report={'audit_kind':'independent_read_only_offline_validation_bundle_audit',
        'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_commit':COMMIT,'stage_directory':str(STAGE),'artifact':str(ARCHIVE),
        'old_artifact':str(OLD_ARCHIVE),'script_path':str(Path(__file__).resolve()),
        'script_sha256':sha(Path(__file__)),
        'execution_scope':'Python stdlib file reads/hashes/decompression, read-only Git blob access and importlib load_bundle only; no engine, Wine, runner main, Fastchess, build, match or timed benchmark execution',
        'checker_correction':{'scope': 'Audit checker correction only; no package/evidence changes', 'failed_check': 'readme_names_648_source_and_correct_candidate', 'cause': 'The checker forbade every occurrence of 6.4.2 candidate, including the correct explicit negative sentence that obsolete source is not carried forward.', 'correction': 'Check the actual positive Forge 6.4.8 Candidate heading and current source commit instead.', 'attempt1_report_sha256': '090a3da520105788a2d4f3759fdaad0e576491482aa27d30fa5f53b10d019903', 'attempt1_script_sha256': 'c7ce66b9b6d83f4270667a1d6ad8628759b3867c537bfa39842197867cf84897'},
        'limitations':['A prepared bundle is not a new A/A, pilot, SPRT or native hardware result.',
                      'Unchanged 6.4.2 dependency smoke logs describe their historical unchanged dependencies only.',
                      'This audit does not independently reproduce the engine/toolchain builds.']}
try:
    manifest=load(STAGE/'manifest.json')
    files=manifest['files']
    before=inventory(STAGE)
    root,new_data,names,badcrc=archive_contents(ARCHIVE)
    oldroot,old_data,oldnames,oldbad=archive_contents(OLD_ARCHIVE)
    old_manifest=json.loads(old_data['manifest.json'])
    report.update(artifact_sha256=sha(ARCHIVE),artifact_bytes=ARCHIVE.stat().st_size,
                  manifest_sha256=sha(STAGE/'manifest.json'),archive_root=root,
                  old_artifact_sha256=sha(OLD_ARCHIVE),old_archive_root=oldroot,
                  listed_files=len(files),actual_files=len(before),archive_members=len(names))
    check('immutable_old_archive_identity',report['old_artifact_sha256']==EXPECTED_OLD_SHA and oldbad is None)
    check('new_archive_expected_sha_and_size',report['artifact_sha256']==EXPECTED_SHA and report['artifact_bytes']==EXPECTED_BYTES)
    check('root_manifest_expected_sha',report['manifest_sha256']==EXPECTED_MANIFEST_SHA)
    check('new_archive_crc',badcrc is None)
    check('new_archive_safe_unique_case_unique_members',len(names)==len(set(names))==len({name.casefold() for name in names})
          and all(safe(name) and not name.endswith('/') for name in names))
    with zipfile.ZipFile(ARCHIVE) as z:
        check('no_archive_symlinks',all(not stat.S_ISLNK(item.external_attr>>16) for item in z.infolist()))
    check('stage_has_no_symlinks',not any(p.is_symlink() for p in STAGE.rglob('*')))
    check('archive_exact_full_stage_membership',set(new_data)==set(before))
    check('every_archive_member_equals_stage',all(sha_bytes(data)==before.get(name) for name,data in new_data.items()))
    check('manifest_schema_and_safe_case_unique_paths',manifest['schema_version']==1 and len(files)==len({name.casefold() for name in files})
          and all(safe(name) and re.fullmatch('[0-9a-f]{64}',digest) for name,digest in files.items()))
    check('manifest_covers_every_actual_file_except_only_root_manifest',set(files)==set(before)-{'manifest.json'}
          and 'manifest.json' not in files and all(files[name]==digest for name,digest in before.items() if name!='manifest.json'))
    nested=[name for name in before if name!='manifest.json' and PurePosixPath(name).name=='manifest.json']
    check('all_nested_manifest_json_files_listed_and_hashed',len(nested)>=2 and all(name in files and files[name]==before[name] for name in nested),nested)
    check('parent_derivation_and_manifest_identity',manifest['derived_from']['archive_sha256']==EXPECTED_OLD_SHA
          and manifest['derived_from']['parent_manifest_sha256']==sha_bytes(old_data['manifest.json']))
    readiness=manifest['readiness']
    check('readiness_is_pending_and_historical_logs_not_new_results',readiness==load(STAGE/'provenance/readiness-6.4.8.json')
          and all(readiness[key]=='pending' for key in ('new_bundle_aa','new_native_pilot','new_native_sprt'))
          and readiness['candidate_source_commit']==COMMIT and readiness['candidate_sha256']==EXPECTED_ENGINE_SHA
          and readiness['equal_clock_gain_established'] is False and 'not new bundle A/A results' in readiness['historical_component_checks'])
    external=load(EVIDENCE/'bundle-verification.json')
    check('external_verification_records_match_actual_frozen_bundle',external['sha256']==EXPECTED_SHA and external['bytes']==EXPECTED_BYTES
          and external['manifest_sha256']==EXPECTED_MANIFEST_SHA and external['members']==len(names)
          and external['source_commit']==COMMIT and external['candidate_sha256']==EXPECTED_ENGINE_SHA
          and (EVIDENCE/'manifest.json').read_bytes()==(STAGE/'manifest.json').read_bytes())
    protocol=manifest['protocol']
    check('entire_protocol_identical_to_642_bundle',protocol==old_manifest['protocol'])
    provenance=manifest['provenance']
    check('all_noncandidate_manifest_provenance_unchanged',{k:v for k,v in provenance.items() if k!='candidate'}
          =={k:v for k,v in old_manifest['provenance'].items() if k!='candidate'})
    candidate=provenance['candidate']
    candidate_dir=candidate['bundled_source_directory']
    old_candidate_dir=old_manifest['provenance']['candidate']['bundled_source_directory']
    allowed_changed={'README.txt','manifest.json','engine/candidate.exe','provenance/candidate-source-files.json',candidate['record'],'provenance/standalone-6.4.8-windows.json','provenance/readiness-6.4.8.json'}
    removed={name for name in old_data if name not in new_data}
    changed={name for name in old_data.keys()&new_data.keys() if old_data[name]!=new_data[name]}
    added={name for name in new_data if name not in old_data}
    report['old_new_changes']={'removed':sorted(removed),'changed':sorted(changed),'added':sorted(added)}
    check('only_old_candidate_sources_provenance_and_optional_test_removed',all(name.startswith(old_candidate_dir+'/')
          or name in {old_manifest['provenance']['candidate']['record'],'engine/forge_tests.exe'} for name in removed))
    check('only_declared_candidate_metadata_and_readme_changed',changed<=allowed_changed,sorted(changed))
    check('only_new_candidate_source_and_provenance_added',all(name.startswith(candidate_dir+'/') or name in {candidate['record'],'provenance/standalone-6.4.8-windows.json','provenance/readiness-6.4.8.json'} for name in added),sorted(added))
    retained={name for name in old_data if name not in removed and name not in changed}
    check('all_other_unchanged_old_files_byte_identical',all(old_data[name]==new_data[name] for name in retained),{'retained_byte_identical_files':len(retained)})
    immutable=[name for name in old_data if name.startswith(('runtime/','fastchess/','openings/','sources/original-6.4.0/'))
               or name in ('windows_validate.py','pgn_stats.py','engine/original-6.4.exe','LICENSE.txt','run-readiness.cmd','run-validation.cmd')]
    check('all_runtime_fastchess_original_source_openings_runner_launchers_unchanged',all(name in new_data and new_data[name]==old_data[name] for name in immutable),{'unchanged_dependencies':len(immutable)})
    check('candidate_is_exact_tested_standalone_648_pe',before['engine/candidate.exe']==EXPECTED_ENGINE_SHA
          ==sha(STANDALONE/'forge-6.4.8-ryzen-9850x3d.exe'))
    check('optional_642_test_pe_not_bundled','engine/forge_tests.exe' not in new_data)
    check('standalone_candidate_provenance_record_consistent',load(STAGE/candidate['record'])==candidate)
    standalone=load(STANDALONE/'provenance.json')
    check('candidate_evidence_copy_exact',load(EVIDENCE/'candidate-provenance.json')==candidate)
    check('candidate_standalone_checks_exactly_match_tested_seven',candidate['standalone_wine_checks']==standalone['wine_checks']
          and len(candidate['standalone_wine_checks'])==7 and candidate['binary_sha256']==EXPECTED_ENGINE_SHA
          and candidate['binary_path']=='engine/candidate.exe' and 'no new bundle A/A or native match has run' in candidate['standalone_wine_scope'])
    check('standalone_provenance_record_is_exact_tested_648_record', (STAGE/'provenance/standalone-6.4.8-windows.json').read_bytes()==(STANDALONE/'provenance.json').read_bytes())
    check('candidate_current_source_and_unproven_strength_hardware_flags',candidate['source_and_tests_commit']==COMMIT
          and candidate['engine_version']=='6.4.8 candidate' and candidate['accepted_elo_gain'] is None
          and candidate['native_windows_tested'] is False and candidate['physical_ryzen_tested'] is False
          and candidate['stockfish_superiority_proven'] is False)
    expected_names={name for name in git('ls-tree','-r','--name-only',COMMIT,'--',
        'CMakeLists.txt','README.md','LICENSE','include','src','bench','tests','tools').decode().splitlines() if not name.endswith('.pyc')}
    candidate_files={name[len(candidate_dir)+1:]:data for name,data in new_data.items() if name.startswith(candidate_dir+'/')}
    check('full_candidate_build_source_tree_membership',set(candidate_files)==expected_names,{'files':len(candidate_files)})
    source_hashes={name:sha_bytes(data) for name,data in candidate_files.items()}
    check('every_candidate_source_file_matches_7125_git_blob',all(data==git('show',COMMIT+':'+name) for name,data in candidate_files.items()))
    source_record=load(STAGE/'provenance/candidate-source-files.json')
    check('candidate_source_manifest_exact',source_record==source_hashes==candidate['source_files_sha256'])
    check('production_and_test_provenance_match_candidate_tree',all(source_hashes[name]==digest for name,digest in
          {**standalone['production_source_sha256'],**standalone['test_source_sha256']}.items()))
    module_spec=importlib.util.spec_from_file_location('forge_648_bundle_static_audit',STAGE/'windows_validate.py')
    module=importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name]=module
    module_spec.loader.exec_module(module)
    denied_calls=[]
    original_run=module.subprocess.run
    original_popen=module.subprocess.Popen
    def forbidden(*args,**kwargs):
        denied_calls.append('subprocess')
        raise RuntimeError('No subprocess permitted while auditing load_bundle')
    module.subprocess.run=forbidden
    module.subprocess.Popen=forbidden
    try:
        loaded_manifest,frozen=module.load_bundle(STAGE)
    finally:
        module.subprocess.run=original_run
        module.subprocess.Popen=original_popen
    check('actual_frozen_runner_load_bundle_passes_without_subprocess',loaded_manifest==manifest and frozen==before and not denied_calls)
    check('load_bundle_did_not_mutate_any_input',inventory(STAGE)==before)
    check('runner_pin_and_phase_settings_unchanged',module.PIN==PIN and module.PHASES=={'aa':(4,2),'pilot':(8,1),'sprt':(5000,1)})
    launcher_data={name:new_data[name].decode('ascii') for name in ('run-readiness.cmd','run-validation.cmd')}
    check('launchers_use_relative_bundled_python_isolation_no_upload',all('runtime\\python.exe' in text and '-I -B' in text
          and 'windows_validate.py' in text and '--zip-results' in text and '%~dp0' in text for text in launcher_data.values())
          and '--aa-only' in launcher_data['run-readiness.cmd'] and '--aa-only' not in launcher_data['run-validation.cmd']
          and not any(re.search(r'(?i)\b(?:curl|wget|powershell|certutil|bitsadmin)\b|https?://',text) for text in launcher_data.values()))
    result_paths=[name for name in new_data if re.search(r'(^|/)(results?|aa|pilot|sprt)(/|\.json$)|(^|/)status\.json$',name)
                  and not name.startswith(('runtime/','sources/'))]
    check('no_bundled_match_results_or_phase_outputs',not result_paths,result_paths)
    readme=new_data['README.txt'].decode()
    check('readme_names_648_source_and_correct_candidate', '6.4.8' in readme and COMMIT in readme
          and 'Forge 6.4.8 candidate, frozen source/test' in readme and 'engine\\candidate.exe' in readme)
    check('readme_explicitly_marks_new_readiness_native_elo_pending',all(term in readme.lower() for term in ('pending','native','a/a','pilot','sprt'))
          and ('no accepted elo gain' in readme.lower() or 'elo impact remain unproven' in readme.lower()) and 'stockfish' in readme.lower())
    check('new_readme_does_not_transfer_old_bundle_validation', not re.search(r'(?i)(?:6\.4\.8|this bundle)[^\n]{0,60}(?:a/a|readiness)[^\n]{0,20}(?:passed|complete)',readme)
          and ('not' in readme.lower() or 'unproven' in readme.lower()))
    secret_patterns={'github_token':r'github_pat_[A-Za-z0-9_]{20,}|\bgh[pousr]_[A-Za-z0-9]{20,}',
                     'aws_access_key':r'\bAKIA[0-9A-Z]{16}\b','private_key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                     'url_user_password':r'https?://[^/\s:@]+:[^@\s/]+@',
                     'bearer_token':r'(?i)authorization:\s*bearer\s+[A-Za-z0-9._~-]{20,}',
                     'token_url':r'(?i)https?://[^\s"<>]+[?&](?:access_token|token|auth|api_key|key|signature|sig)='}
    secret_findings=[]
    for name in changed|added:
        data=new_data[name]
        if b'\0' in data:continue
        text=data.decode('utf-8',errors='replace')
        for rule,pattern in secret_patterns.items():
            if re.search(pattern,text):secret_findings.append({'path':name,'rule':rule})
    check('no_credentials_or_token_urls_in_new_or_changed_text',not secret_findings,secret_findings)
    source_archives=[name for name in added if name.startswith(candidate_dir+'/') and name.endswith(('.tar.gz','.tgz','.zip'))]
    check('candidate_sources_are_direct_git_files_not_unverified_added_source_archives',not source_archives,source_archives)
    report['nested_manifests']=nested
    report['source_files_sha256']=source_hashes
    report['inventory_sha256']=before
    report['readiness_scope']='No new 6.4.8 bundle A/A/pilot/SPRT run; standalone Wine correctness only; all native/strength work pending'
except Exception as exc:
    findings.append({'fatal_exception':str(exc),'traceback':traceback.format_exc()})
report['checks']=checks
report['findings']=findings
report['checks_passed']=sum(item['passed'] for item in checks)
report['checks_total']=len(checks)
report['status']='passed' if not findings else 'findings'
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
OUTPUT.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'checks_passed':report['checks_passed'],'checks_total':report['checks_total'],
                  'findings':findings,'report_path':str(OUTPUT),'report_sha256':sha(OUTPUT)},indent=2))
raise SystemExit(0 if not findings else 1)
