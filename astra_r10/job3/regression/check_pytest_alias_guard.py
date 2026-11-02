"""Actual tmp_path integration check of optional current-alias suppression."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    out=args.out.resolve()
    if not out.is_relative_to(Path('D:/a10/job3/regression-runs')):raise ValueError('owned output required')
    out.mkdir(parents=True,exist_ok=False)
    for name in ('temp','cache'):(out/name).mkdir()
    os.environ.update(TEMP=str(out/'temp'),TMP=str(out/'temp'),TMPDIR=str(out/'temp'),
                      PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                      PYTHONPYCACHEPREFIX=str(out/'cache'))
    sys.pycache_prefix=str(out/'cache')
    sys.path.insert(0,'D:/a10/job3/runtime312/packages')
    import pytest
    from pytest_alias_guard import record_current_aliases
    base=out/'pytest-temp'
    with record_current_aliases(base) as aliases:
        code=int(pytest.main(['-q','-p','no:cacheprovider','--log-file',str(out/'pytest.log'),
            '--basetemp',str(base),'--rootdir',str(HERE),'--confcutdir',str(HERE),
            str(HERE/'test_actual_tmp_path.py')]))
    if code or len(aliases)!=1:raise ValueError('real tmp_path fixture did not complete exactly once')
    if any(Path(item['alias']).exists() or Path(item['alias']).is_symlink() for item in aliases):
        raise ValueError('suppressed convenience alias unexpectedly exists')
    target=Path(aliases[0]['target'])/'sentinel.bin'
    expected=b'owned pytest fixture target remains real'
    if target.read_bytes()!=expected:raise ValueError('real fixture target bytes changed')
    for folder,dirs,files in os.walk(out,followlinks=False):
        for name in dirs+files:
            entry=Path(folder)/name
            if entry.is_symlink() or getattr(entry.lstat(),'st_file_attributes',0)&0x400:
                raise ValueError('unexpected reparse artifact')
    result={'status':'PASS','tests':1,'scope':'real pytest tmp_path fixture; no NPT/model import',
            'aliases':aliases,'target_sha256':hashlib.sha256(expected).hexdigest(),
            'guard_sha256':hashlib.sha256((HERE/'pytest_alias_guard.py').read_bytes()).hexdigest()}
    with (out/'RESULT.json').open('x',encoding='utf8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result))
    return 0

if __name__=='__main__':raise SystemExit(main())
