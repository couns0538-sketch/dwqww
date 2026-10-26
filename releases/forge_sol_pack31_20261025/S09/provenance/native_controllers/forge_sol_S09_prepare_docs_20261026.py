"""Prepare additive documentation only; verify against L/Lprime/B unchanged."""
from pathlib import Path
import difflib,hashlib,importlib.util,json,subprocess

ROOT=Path('/tmp/forge_sol_S09_delivery_stage_20261026')
API=Path('/workspace/forge-pack24-20261026/S09_NATIVE_PREP_20261026/forge_sol_S09_prepare_source_view_20261026.py')
spec=importlib.util.spec_from_file_location('s09_sources',API)
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
ADDITIONS={
 'README.md':'''## S09 source addendum, 2026-10-26

This isolated follow-up uses the supplied, reviewed Forge step 1 unchanged:
`fc_buckets8_h256e12.patch`, SHA256
`ed28132d48b75496732f0ecf25753ad869787c84a4939aaf004b3de8580a9704`.
The newly authored engine delta adds a required available/residual/H256/stored-head
contract test and optional validation-tool targets. It does not rename the
reviewed core patch as a new implementation or promote a network.

The trainer copy adds `--buckets 1|8` with default 1. The converter reuses the
original step-1 include parser. The original one-head h256_e12 net remains the
engine default; there is no new UCI option. Eight replicated heads are separate
offline validation inputs. Accumulators remain float; existing quantized weight
storage is dequantized by the original loader. See the separately dated
`forge_sol_S09_job_report_20261026.md` for evidence and unverified PC/GPU steps.
No speed or playing-strength claim follows from these checks.

''',
 'IDEA_SOURCE.md':'''## S09 idea sources, 2026-10-26

- Crew's S09 specification and its CR-passed, original Forge piece-count output
  head extension: `files/17_buckets8_step1/fc_buckets8_h256e12.patch`, SHA256
  `ed28132d48b75496732f0ecf25753ad869787c84a4939aaf004b3de8580a9704`.
- Forge's own supplied v3b trainer and exporter:
  `files/07_nnue_context/train_resid_v3b.py`, SHA256
  `5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f`.
- Supplied f006 training-run logs and the crew's explicit recipe/default request.
  These identify observed run settings, not a recovered complete settings file.

No external engine implementation or tuned constants were imported. Existing
Forge parsing, native APIs and reviewed implementation are reused as original
project dependencies, with new work and evidence identified separately.

'''}

def main():
    failure=ROOT/'forge_sol_S09_docs_preparation_failure_observation_20261026.json'
    with failure.open('x') as f:json.dump({'scope':'observed tool-output exception before any patch/native/source write; original inline command was not captured to a raw log',
        'error':"AttributeError: module 'difflib' has no attribute 'unifieddiff'. Did you mean: 'unified_diff'?",
        'cause':'misspelled Python standard-library function name in draft inline preparation',
        'correction':'use difflib.unified_diff; all original source files unchanged'},f,indent=2);f.write('\n')
    text=''
    for name,add in ADDITIONS.items():
        old=(api.BASES['L']/name).read_text();lines=old.splitlines(keepends=True)
        new=''.join(lines[:2])+add+''.join(lines[2:])
        text+=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name,n=2))
    patch=ROOT/'forge_sol_S09_documentation_addendum_20261026.patch'
    with patch.open('x') as f:f.write(text)
    records=[]
    for label,source in api.BASES.items():
        command=['patch','--dry-run','-p1','-F0','--batch','--no-backup-if-mismatch','-i',str(patch)]
        r=subprocess.run(command,cwd=source,capture_output=True)
        for suffix,raw in [('stdout',r.stdout),('stderr',r.stderr)]:
            with (ROOT/f'forge_sol_S09_docs_{label}_GNU_applycheck_20261026.{suffix}').open('xb') as f:f.write(raw)
        records.append({'base':label,'argv':command,'returncode':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()})
        if r.returncode:raise ValueError(r.stdout+r.stderr)
    result={'documentation_patch_sha256':hashlib.sha256(patch.read_bytes()).hexdigest(),'checks':records,
        'all_baselines_unchanged':all(x['unchanged'] for x in api.verify_all_baselines().values()),
        'scope':'additive documentation only; no native code or new test-result claim'}
    with (ROOT/'forge_sol_S09_documentation_applychecks_20261026.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))

if __name__=='__main__':main()
