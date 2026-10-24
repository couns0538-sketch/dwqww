# PowerShell qualification packet

Version 1 source and fixture run were checked on 2026-10-24 at 15:02:45UTC; version 2 evidence follows below. Original script and fixtures are under ps-agent only; no engine source, Git/index or production files were changed by this agent. The implementation follows the supplied nps_abba_bc.ps1 style and protocol; no other engine code was used.

Verified on Linux, using privately extracted official Microsoft PowerShell 7.5.2:

- Actual PowerShell parser: PASS.
- Verdict boundaries:12/14+median beyond band => FASTER;12/14 within band => NOISE;11/14 => NOISE;12 negative => SLOWER; even median => PASS.
- Synthetic bad d11 => BADNODES, 6 child invocations, stops before stage1 d13.
- Synthetic bad d13 => BADNODES, 7 child invocations, stops immediately.
- Synthetic nonzero exit => BADEXIT, 6 child invocations, raw exchange retained.
- Synthetic truncated oracle => ORACLE_FAIL, 21 child invocations, paired NPS absent.
- Synthetic missing int16 UCI option => BADOPTION, 26 child invocations after all five OFF identities for five builds. This also exercises numeric-depth frozen-manifest serialization.
- All five failure fixtures produced no paired CSV or summary CSV. Final suite exit 0, stderr 0 bytes.

Raw compact evidence: `verification/frozen-fixtures/`, stdout `verification/frozen-fixtures.stdout.txt` SHA256 `34d73cd8f35d3ca757492a77dd6b405227ff079a6b4cabddac790ac58baf6957`; original startup/serialization failures remain separately in `verification/failures-before-fix.log`. Synthetic NPS values have no performance meaning. No actual engine, full native million-position oracle, Windows run, native profiling, or CPU speed measurement was performed here. Whole-engine phase percentages remain NOT_MEASURED. Optional int16-ON requires supplied frozen counts; no ON counts are invented.

Runtime provenance: HTTPS official Microsoft package returned HTTP200; archive size 75,453,694 bytes, Debian package version 7.5.2-1.deb, executable reports 7.5.2. Download SHA256 `717a62fbec3319948e9df58a89018632712eccd6e94383f1df70f88ece371845` was recorded; the external download archive was then removed to reclaim space. URL: https://packages.microsoft.com/repos/microsoft-debian-bookworm-prod/pool/main/p/powershell/powershell_7.5.2-1.deb_amd64.deb . No installer or persistent environment change was used. The private runtime consumes about 185 MiB and is excluded from source delivery.

Independent repeat command (replace the output path with a new/empty directory):

```bash
XDG_CACHE_HOME=/workspace/forge-sol-next-20261024/ps-agent/pwsh-cache XDG_CONFIG_HOME=/workspace/forge-sol-next-20261024/ps-agent/pwsh-config XDG_DATA_HOME=/workspace/forge-sol-next-20261024/ps-agent/pwsh-data PYTHONDONTWRITEBYTECODE=1 python3 /workspace/forge-sol-next-20261024/ps-agent/tests/test_failure_gates.py --pwsh /workspace/forge-sol-next-20261024/ps-agent/private-pwsh/opt/microsoft/powershell/7/pwsh --output /workspace/forge-sol-next-20261024/ps-agent/verification/independent-repeat
```

Delivered source hashes are in SHA256SUMS.txt. `DELIVERY_FILES.txt` lists the small source packet and explicitly excludes runtime caches. Native grok-pc remains the run owner for performance; no speed or Elo gain is claimed.

## Version 2 activation gate

At root's request, explicit NnueInt16=true profiles now require `info string NnueInt16 active` after the OFF-default UCI advertisement. Missing acknowledgement or exact `info string NnueInt16 unavailable; using float` stops BACKEND_INACTIVE. This prevents a float fallback with coincidentally matching node counts from being labeled active int16. No other protocol behavior changed.

Final v2 suite checked at 2026-10-24 15:13:38UTC: PowerShell syntax/verdict boundaries and all six synthetic failure gates PASS, exit 0, stderr 0 bytes. New advertised-but-inactive case stops BACKEND_INACTIVE after 26 child invocations; no paired NPS/summary CSV exists. Raw evidence is under `verification/v2-fixtures/`; stdout SHA256 `cb095d233bd19d96f7f0ca9ecdf0f7873d3991ba648e58da6945b94c93132751`. Script SHA256 `e52e8ba069aab14bdc78897672c7744f0d6f959f72fc3b0b244348145f0cb8fd`. Source-only independent review found no concrete defect in the small gate. Native Windows/timing remains unrun.

Version 1 script (`b5f12dd07868dc4000d2debbaa37ec3f84623d2edffd42cff23f3e164cc4396e`), source/docs and checksum list are preserved under `archive/v1/`; all earlier logs remain unchanged. The private PowerShell runtime remains available for root's v2 recheck.
