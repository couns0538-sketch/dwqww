# Isolated native validation tools — 2026-10-29 UTC

Status: DONE. The official tools are callable locally under `/tmp/astra3-tools`; nothing was installed system-wide. All files in this evidence directory are frozen for the parent to checkpoint. Runtime source/package/build trees remain outside the Forge repository.

| Tool | Verified local entry point | Result |
|---|---|---|
| Fastchess | `/tmp/astra3-tools/fastchess-src/fastchess` | `fastchess alpha 1.8.2 20261011-ebfd64c`; build, `-version`, `-help` exit 0; native help includes `-strict` |
| PowerShell | `/tmp/astra3-tools/pwsh` | Private Microsoft PowerShell 7.5.2; version exit 0; stderr empty |

Fastchess source commit: [`ebfd64cb7fac80d4822c50b07dca4fe934779d21`](https://github.com/Disservin/fastchess/commit/ebfd64cb7fac80d4822c50b07dca4fe934779d21). Its tracked source was unchanged after the serial GCC 14.2 build. Command: `nice -n 19 timeout 480 make -j1 CXX=/usr/bin/g++-14 NATIVE=-march=x86-64`. This is the runner's own C++17/O3 build, separate from Forge's C++20/strict-FP recipe.

Fastchess executable SHA256: `91c2f9b6fafe8c2e86c25a2d2d291cbf7c8ab798b43798b9a6fb522e5d990509`.

PowerShell was extracted from the official Microsoft Debian package without executing package installation scripts. Package version `7.5.2-1.deb`, 75,453,694 bytes, SHA256 `717a62fbec3319948e9df58a89018632712eccd6e94383f1df70f88ece371845`. Executable SHA256 `4a89e7904a0d37e8d2d2a1d85df24dbd7c4e06395b19e57dbb48c9d44b47444c`. The wrapper sets XDG/.NET cache directories under `/tmp/astra3-tools` and disables telemetry; it does not repurpose HOME or alter the global PATH. Its exact source is `pwsh-isolated-wrapper.sh`.

`tooling_provenance.json` gives complete URLs, paths, identities, commands and limits. Original build/download/version/help outputs accompany it; `SHA256SUMS.txt` identifies every evidence file.

Only version/help probes ran. No engine, match, benchmark, live PC action, supplied autonomy script or A4 fixture harness ran. PowerShell 5.1 compatibility remains UNVERIFIED; a Linux PowerShell 7.5.2 run cannot establish Windows PowerShell 5.1 behavior. Parent may now schedule the authorized strict smoke and later isolated fixtures. Do not execute or install the live autopromote script.

IDEA_SOURCE: the user's isolated validation-tool setup request, official [Fastchess build instructions](https://github.com/Disservin/fastchess/blob/ebfd64cb7fac80d4822c50b07dca4fe934779d21/README.md), and the official [Microsoft PowerShell package](https://packages.microsoft.com/repos/microsoft-debian-bookworm-prod/pool/main/p/powershell/powershell_7.5.2-1.deb_amd64.deb). No third-party engine implementation was added to Forge.
