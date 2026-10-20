"""Compile the wording-only final unit; preserve first full source/build unchanged."""
import importlib.util,json,shlex,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
spec=importlib.util.spec_from_file_location('first_driver',HERE/'run_prototype_release.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
original_source=d.SOURCE;original_build=d.BUILD
final_source=Path('/workspace/.cloud-setup/pawn-span-fill-prototype-label-source')
unit=Path('/workspace/.cloud-setup/pawn-span-fill-prototype-label-unit')
out=HERE/'label-only-attempt1';names=sorted(json.loads((HERE/'FINAL-SOURCE-75.json').read_text()));expected=json.loads((HERE/'FINAL-SOURCE-75.json').read_text())
assert not final_source.exists() and not unit.exists() and not out.exists()
before=d.source_snapshot(REPO,names);assert before==expected
first=json.loads((HERE/'EXPECTED-SOURCE-75.json').read_text());assert [n for n in names if first[n]!=expected[n]]==['tests/pawn_span_tests.cpp']
out.mkdir();unit.mkdir();final_source.mkdir()
for name in names:
    target=final_source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/name,target)
d.SOURCE=final_source
summary={'status':'RUNNING','scope':'Finalfixturefailurelabelonly; originalfull12CTestsource/build remains untouched. No newproductionobject/engine/bench.','stages':[],'original_full_ctest':'release-attempt1/summary.json','frozen_inputs_sha256_before':{str(Path(__file__)):d.sha(Path(__file__)),str(HERE/'FINAL-SOURCE-75.json'):d.sha(HERE/'FINAL-SOURCE-75.json')},'first_build_before':d.build_snapshot()}
env=d.os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
commands=json.loads((original_build/'compile_commands.json').read_text());entry=next(x for x in commands if x['file'].endswith('/tests/pawn_span_tests.cpp'))
command=entry.get('arguments') or shlex.split(entry['command']);command=[x.replace(str(original_source),str(final_source)) for x in command]
obj=unit/'pawn_span_tests.cpp.o';command[command.index('-o')+1]=str(obj)
link=shlex.split((original_build/'CMakeFiles/forge_pawn_span_tests.dir/link.txt').read_text());link[link.index('-o')+1]=str(unit/'forge_pawn_span_tests')
link=[str(obj) if x.endswith('CMakeFiles/forge_pawn_span_tests.dir/tests/pawn_span_tests.cpp.o') else str(original_build/'libforge_core.a') if x=='libforge_core.a' else x for x in link]
try:
    for label,argv in [('compile-final-unit',command),('link-final-unit',link),('run-final-unit',[unit/'forge_pawn_span_tests'])]:d.run_stage(label,argv,60,out,names,expected,env,summary)
    assert (out/'run-final-unit/stdout.bin').read_text()=='pawn_span_tests: 37320 checks, 0 failures\n'
    summary['status']='PASS'
except BaseException as error:
    summary.update(status='FAILED',error=repr(error));raise
finally:
    summary['first_build_after']=d.build_snapshot();summary['working_source_after']=d.source_snapshot(REPO,names);summary['exported_source_after']=d.source_snapshot(final_source,names)
    summary['final_unit_artifacts_sha256']={p.name:d.sha(p) for p in unit.iterdir() if p.is_file()}
    summary['frozen_inputs_sha256_after']={p:d.sha(p) for p in summary['frozen_inputs_sha256_before']}
    if summary['first_build_before']!=summary['first_build_after'] or summary['working_source_after']!=expected or summary['exported_source_after']!=expected or summary['frozen_inputs_sha256_before']!=summary['frozen_inputs_sha256_after']:summary['status']='FAILED'
    d.save(out/'summary.json',summary)
if summary['status']!='PASS':raise SystemExit(1)
