#!/usr/bin/env python3
"""Linux PowerShell dry-run checks; no actual engine or timing evidence."""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--pwsh", required=True)
parser.add_argument("--output", type=pathlib.Path, help="optional new/empty directory for compact raw fixture evidence")
args = parser.parse_args()
if args.output:
    args.output.mkdir(parents=True, exist_ok=True)
    assert not any(args.output.iterdir()), "fixture output directory must be empty"
here = pathlib.Path(__file__).resolve().parent
script = here.parent / "zen5_qualify_sol.ps1"
cpu = min(os.sched_getaffinity(0))
assert cpu < 64, "fixture needs an available CPU in group0"

def quote(value):
    return "'" + str(value).replace("'", "''") + "'"

parse_and_verdicts = r"""
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile(SCRIPT,[ref]$tokens,[ref]$errors)
if($errors.Count){ $errors | ForEach-Object { Write-Host $_ }; exit 2 }
$functions=$ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and @('Median','Verdict') -contains $n.Name},$true)
foreach($f in $functions){ . ([scriptblock]::Create($f.Extent.Text)) }
$v=(@(2.0)*12)+(@(-1.0)*2); if((Verdict $v 1.0) -ne 'FASTER'){throw 'FASTER gate'}
$v=(@(0.5)*12)+(@(-1.0)*2); if((Verdict $v 1.0) -ne 'NOISE'){throw 'band gate'}
$v=(@(2.0)*11)+(@(-1.0)*3); if((Verdict $v 1.0) -ne 'NOISE'){throw '12-of-14 gate'}
$v=(@(-0.1)*12)+(@(2.0)*2); if((Verdict $v 1.0) -ne 'SLOWER'){throw 'SLOWER gate'}
if((Median @(1.0,3.0)) -ne 2.0){throw 'median'}
Write-Host 'PASS PowerShell syntax and verdict boundary fixtures (synthetic only)'
""".replace("SCRIPT", quote(script))
check = subprocess.run([args.pwsh, "-NoLogo", "-NoProfile", "-Command", parse_and_verdicts], capture_output=True, text=True, timeout=30)
if args.output:
    (args.output / "syntax-verdict.stdout.txt").write_text(check.stdout)
    (args.output / "syntax-verdict.stderr.txt").write_text(check.stderr)
assert check.returncode == 0, (check.stdout, check.stderr)
print(check.stdout.strip())

with tempfile.TemporaryDirectory(prefix="forge-ps-fixtures-") as temp:
    base = pathlib.Path(temp)
    roles = ("lock", "stage1", "stage2", "stage3", "oracle_off", "oracle_on", "int16")
    paths = {}
    for role in roles:
        path = base / (role + ".py")
        shutil.copyfile(here / "fake_uci.py", path)
        path.chmod(0o755)
        paths[role] = path
    for mode, status, max_calls in (("bad_d11", "BADNODES", 6), ("bad_d13", "BADNODES", 7), ("nonzero", "BADEXIT", 6), ("oracle", "ORACLE_FAIL", 21), ("bad_option", "BADOPTION", 26)):
        calls = base / (mode + ".calls.jsonl")
        out = base / mode
        environment = dict(os.environ, FORGE_FIXTURE_MODE=mode, FORGE_FIXTURE_CALLS=str(calls))
        command = "& " + quote(script) + " -Cpu " + str(cpu)
        engine_roles = roles[:4] + (("int16",) if mode == "bad_option" else ())
        command += " -Exes @(" + ",".join(quote(paths[role]) for role in engine_roles) + ")"
        command += " -OracleExes @(" + ",".join(quote(paths[role]) for role in roles[4:6]) + ")"
        if mode == "bad_option":
            command += " -Labels @('lock','stage1','stage2','stage3','int16') -OptionProfiles @{int16=@{Options=@{NnueInt16=$true};ExpectedNodes=@{13=745494;16=2460422}}}"
        command += " -Out " + quote(out) + " -DryRun -TimeoutSeconds 10"
        result = subprocess.run([args.pwsh, "-NoLogo", "-NoProfile", "-Command", command], env=environment, capture_output=True, text=True, timeout=60)
        if args.output:
            (args.output / (mode + ".stdout.txt")).write_text(result.stdout)
            (args.output / (mode + ".stderr.txt")).write_text(result.stderr)
            shutil.copytree(out, args.output / mode)
            shutil.copyfile(calls, args.output / (mode + ".calls.jsonl"))
        assert result.returncode == 1, (mode, result.returncode, result.stdout, result.stderr)
        actual_status = (out / "zen5_qualify_sol.STATUS").read_text(encoding="utf-8-sig").strip()
        assert actual_status == status, (mode, actual_status, result.stdout, result.stderr)
        invoked = [json.loads(line) for line in calls.read_text().splitlines()]
        assert len(invoked) == max_calls, (mode, invoked)
        assert not (out / "zen5_qualify_sol.csv").exists(), "no paired NPS may be published before oracle PASS"
        assert not (out / "zen5_qualify_sol_summary.csv").exists()
        raw = out / "raw"
        assert list(raw.glob("*.stderr.txt")), "raw failure evidence missing"
        if mode.startswith("bad_d"):
            raw_stdin = sorted(raw.glob("*stage1*.stdin.txt"))[-1].read_text()
            assert "setoption name NnueInt16 value false" in raw_stdin
            assert "setoption name OwnBook value false" in raw_stdin
        print(f"PASS synthetic {mode}: status={status}, child_count={len(invoked)}, paired_nps_absent=True")
print("PASS failure gates only; no actual engine, Windows execution, or speed result")
