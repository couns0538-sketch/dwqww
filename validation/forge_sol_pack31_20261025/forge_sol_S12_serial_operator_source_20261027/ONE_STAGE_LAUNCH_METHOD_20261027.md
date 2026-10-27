# One explicit S12 stage launch method — source only

This reuses the existing S11 one-shot parent launch pattern, whose source and hash are in `SOURCE_PREFLIGHT_20261027.json`. Invoke the already frozen CLI directly; do not add a runner, scheduler, shared Python interpreter or automatic next-stage loop. This document is not an execution grant.

## Materialize one reviewable request after the root grant

1. Save root's exact grant message bytes as a NEW `root_grant_verbatim.txt`. Preserve the raw message, date and reference; its SHA256 is captured in the request. A publication SHA or a template is not a lease.
2. Copy `NATIVE_LAUNCH_REQUEST_TEMPLATE_20261027.json` to a NEW literal actual request file outside the frozen source checkpoint. Fill one stage ID, grant reference and exact allowed stage IDs, actual verified S11 closed publication40hex, hashes/paths for root's public-readback and owned-closure proofs, CPU2/nice19 and exclusive-window confirmation. Retain root's stated finite scope. Do not treat an absent answer or placeholder as permission.
3. Read the immutable sequence and select exactly that one row; require the request's sequence SHA and CLI source SHA to match. Verify the frozen packet/dependency pins and source identities recorded in the preflight. Require source-binding endpoint hashes to match their exact proof copies. For every `requires_closed_pass_stage_ids`, require an explicit closed operator snapshot whose endpoint hash still matches. Native B-03 also requires Lprime-26 closure. Check the recorded S11 owned PIDs/groups are absent now and root's exclusive window is still active; inspect only those owned identities, never stop another job.
4. Require the selected output and launch-capture directory to be NEW. Never reuse a failed output. Replace only the two named placeholders in the selected argv; use the frozen literal original corpus manifest already selected in the ledger. Reject any remaining placeholder, changed flag/path/budget or ungranted stage. Hash the actual JSON argv using the ledger's canonical encoding and store both template and actual hashes.
5. For compiler stages the child sets its own4GiB AS cap. For ASAN runtime require both soft and hard RLIMIT_AS unlimited in this fresh owner before launch; use the known qualified escaped runtime from FIRST, leaks ON. Preserve exact owner environment/limits in the started receipt. Never compile inside this runtime process and never run runtime inside the capped compiler process.

## Existing one-shot parent capture pattern

At launch, materialize only this finite selected invocation using the existing S11 direct `subprocess.Popen` pattern. These are the concrete parent captures to produce, all with exclusive creation:

- `root_grant_verbatim.txt` and immutable actual request JSON, with hashes.
- `grant_actual_argv.json`: stage ID, template/actual argv and hashes, CLI/dependency/preregistration hashes, root grant text/hash/reference, actual S11 publication and closure/readback proofs, CPU/nice/budget, previous-stage endpoint hashes, fresh output and disk/AS/ownership preflight.
- `parent.stdin`: exact empty bytes. Open it for the CLI's stdin; all native UCI exchanges stay in the frozen transport's original `.stdin/.stdout/.stderr` files. Helpers receive their preregistered devnull stdin. Parity retains the original sealed corpus identity and complete original stream chunks; it does not invent a substituted stdin text.
- `parent.stdout`, `parent.stderr`: original unfiltered child stdout/stderr, opened with `xb` before launch. Do not pipe through `tee`, trim, decode/re-encode or replace them with summaries.
- `parent_started.json`: parent/controller PIDs, exact argv, grant hash, wall/monotonic start, cwd, limits and selected environment.
- `parent_closed.json`: actual outer rc, elapsed time, original capture lengths/hashes and endpoint existence/hash, plus owned closure. Missing endpoint is a failed stage, including parser/preflight exits that happen before the CLI makes its directory.

The existing launch shape is:

```python
# This is an operator invocation pattern, not a new controller file.
# actual_argv, cwd, grant_receipt and NEW capture_dir have already been
# materialized and verified for one explicitly granted stage as above.
env = dict(os.environ)
env['PYTHONDONTWRITEBYTECODE'] = '1'
with (capture_dir / 'parent.stdin').open('xb') as stream:
    stream.write(b'')
with (capture_dir / 'parent.stdin').open('rb') as saved_stdin, \
     (capture_dir / 'parent.stdout').open('xb') as saved_stdout, \
     (capture_dir / 'parent.stderr').open('xb') as saved_stderr:
    child = subprocess.Popen(actual_argv, cwd=cwd, env=env,
        stdin=saved_stdin, stdout=saved_stdout, stderr=saved_stderr,
        start_new_session=True)
    # Save the exclusive started receipt immediately, then return the
    # tool session for monitoring while this one child runs.
    returncode = child.wait()
# Save exclusive parent_closed receipt with raw capture/endpoint hashes.
# Inspect its actual endpoint and owned closure before doing anything else.
```

The CLI's preregistered finite deadline, root-stop handling, resource guard and owned cleanup remain unchanged. Monitor the tool session without issuing another native invocation; report progress at most60s apart. If the CLI fails to return after its bound and owned-cleanup grace, preserve liveness/process evidence, request its supported stop only for that owned controller, and report BLOCKED to root. Do not continue or silently increase the bound. Do not kill foreign processes or assume a departed controller proves its children closed.

## Close exactly one stage

Require outer rc0, the ledger's exact endpoint status, no error/postflight error, unchanged source/artifacts/parser bindings, and closed/reaped owned groups. Compiler commands require every recorded child rc0 with no stop/error/open members. FIRST/FULL require all engine groups closed, unchanged artifacts/source, and FIRST's exact bare11 exchange for the actual new main. Feature uses the reviewed parser/runner pins and unchanged-source postflight. Baseline RED requires outer PASS plus nested PASS_BASELINE_RED_CONTROL, child rc1 and exactly17 approved failures with zero parity failures. Candidate GREEN requires nested PASS_ACTUAL_WORKER_REGRESSION/rc0. Counters require five PASS_COUNTER_AND_NODE_PAIR checks. Parity requires three PASS_CAPTURE arms, complete original byte comparisons and PASS_MEASURED_ALIAS_ACCOUNTING.

Save a NEW `closed_stage_snapshots/STAGE_ID.json` with `CLOSED_PASS`, endpoint path/hash/status, parent close/grant hashes and explicit closure findings, and append a NEW event to the later mutable run ledger. Never edit the frozen initial source-only ledger. Stop at any failed requirement; do not create a PASS snapshot, delete output or retry. A completed CLI with an invalid ancillary integrity check remains preserved as a failed/blocked stage.

After Lprime-03 closes PASS, the next native invocation must be the separate Lprime-04 FIRST bare11; after FIRST closes PASS, run Lprime-05 FULL, each within its explicit finite grant. The operator inspects and launches each stage individually. No command in this method authorizes the next stage automatically. Root may grant an explicitly listed finite set, but every invocation still has a distinct capture and closure gate.
