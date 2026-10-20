"""Correct only the first label-link command's relocated dependency-file path."""
import importlib.util,json,shlex
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('original_driver',HERE/'run_prototype_release.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
original_build=d.BUILD;d.SOURCE=Path('/workspace/.cloud-setup/pawn-span-fill-prototype-label-source')
obj=Path('/workspace/.cloud-setup/pawn-span-fill-prototype-label-unit/pawn_span_tests.cpp.o')
unit=Path('/workspace/.cloud-setup/pawn-span-fill-prototype-label-unit-attempt2');out=HERE/'label-only-attempt2'
assert not unit.exists() and not out.exists();unit.mkdir();out.mkdir()
expected=json.loads((HERE/'FINAL-SOURCE-75.json').read_text());names=sorted(expected)
summary={'status':'RUNNING','stages':[],'scope':'Reuse successful finalfixturecompile; repair only relocated linker dependency output. Preserve failedlink/raws/driver and first full12CTest source/build.','first_build_before':d.build_snapshot(),'frozen_inputs_sha256_before':{str(p):d.sha(p) for p in [Path(__file__),HERE/'FINAL-SOURCE-75.json',obj,original_build/'libforge_core.a']}}
link=shlex.split((original_build/'CMakeFiles/forge_pawn_span_tests.dir/link.txt').read_text());link[link.index('-o')+1]=str(unit/'forge_pawn_span_tests')
link=[str(obj) if x.endswith('CMakeFiles/forge_pawn_span_tests.dir/tests/pawn_span_tests.cpp.o') else str(original_build/'libforge_core.a') if x=='libforge_core.a' else '-Wl,--dependency-file='+str(unit/'link.d') if x.startswith('-Wl,--dependency-file=') else x for x in link]
env=d.os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
try:
    for label,argv in [('link-final-unit',link),('run-final-unit',[unit/'forge_pawn_span_tests'])]:d.run_stage(label,argv,60,out,names,expected,env,summary)
    assert (out/'run-final-unit/stdout.bin').read_text()=='pawn_span_tests: 37320 checks, 0 failures\n'
    summary['status']='PASS'
except BaseException as error:
    summary.update(status='FAILED',error=repr(error));raise
finally:
    summary['first_build_after']=d.build_snapshot();summary['working_source_after']=d.source_snapshot(d.REPO,names);summary['exported_source_after']=d.source_snapshot(d.SOURCE,names)
    summary['frozen_inputs_sha256_after']={p:d.sha(p) for p in summary['frozen_inputs_sha256_before']}
    summary['final_unit_artifacts_sha256']={p.name:d.sha(p) for p in unit.iterdir() if p.is_file()}
    if summary['first_build_before']!=summary['first_build_after'] or summary['working_source_after']!=expected or summary['exported_source_after']!=expected or summary['frozen_inputs_sha256_before']!=summary['frozen_inputs_sha256_after']:summary['status']='FAILED'
    d.save(out/'summary.json',summary)
if summary['status']!='PASS':raise SystemExit(1)
