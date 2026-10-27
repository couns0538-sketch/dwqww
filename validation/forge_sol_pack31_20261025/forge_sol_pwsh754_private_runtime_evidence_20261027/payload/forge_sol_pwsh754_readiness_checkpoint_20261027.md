# Private PowerShell7.5.4 readiness checkpoint — 2026-10-27

READY for later explicitly authorized local PowerShell checks, using the private launcher below. No global pwsh/PATH installation was made. No project PC scripts, live autonomy scripts, chess engines or compilers ran in this preflight. S15 remains frozen and its10 manifest members reverified unchanged.

```bash
PYTHONDONTWRITEBYTECODE=1 taskset -c 4 nice -n 19 python -B /tmp/forge_sol_pwsh754_preflight_20261027/forge_sol_pwsh754_launch_20261027.py -Command '$PSVersionTable.PSVersion.ToString()'
```

Use `-File /path/to/authorized_script.ps1` and its arguments for later granted checks. The launcher itself supplies `-NoLogo -NoProfile -NonInteractive`; don't add duplicate startup switches. It hash-checks the apphost and redirects module analysis, XDG cache/data/config and temporary files into this private subtree. HOME/PATH are inherited unchanged. Telemetry/update checks and .NET diagnostics are disabled for the launched process only. CPU4/nice19 were used for preflight; caller controls later resource policy.

Official source URLs:

- https://github.com/PowerShell/PowerShell/releases/download/v7.5.4/powershell-7.5.4-linux-x64.tar.gz
- https://github.com/PowerShell/PowerShell/releases/download/v7.5.4/hashes.sha256

Archive75396784B, SHA256 `1fd7983fe56ca9e6233f126925edb24bf6b6b33e356b69996d925c4db94e2fef`, verified against the untouched official checksum asset. The official hash file uses UTF16 BOM; SHA256 `c1013e31e30ccb8c68366fe6a6e4cea50f4ddd12ff115078019e4d1d71d58f00`. One archive was downloaded. Strict member scan plus Python tarfile data filtering excluded traversal/devices/links;674 members,627 regular files,192473406 regular-file bytes, below100MB archive/500MB extraction caps. The private extracted apphost required owner execute permission; only that mode bit changed, not bytes. Its SHA256 is `e0c6c82153c6655a842602be4ea7607d4e3a137b1956668ef44d1b1b7bf939b8`.

Actual -NoProfile/-NonInteractive runtime proof: PowerShell7.5.4/Core, .NET9.0.10, X64, Debian13, FullLanguage; en-US ICU culture and SHA256 self-check passed. Five critical native dependency scans passed with no missing libraries. The reusable launcher passed again in the normal sandbox, rc0 and empty stderr, returning7.5.4. Launcher SHA256 `88c31419ee1f65f223d6c3a8ec03720352c3158cd7b7faf0490f14fcafa3d613`.

The raw failures are preserved: initial sandbox network proxy refusal, UTF8 decoding rejection on Microsoft's UTF16 checksum file, ptrace denial before runtime execution, and missing archive execute bit. The first successful traced startup also created three empty home cache/module directories despite module-cache redirection. Only those proven-new, still-empty directories were removed; no existing user file was touched. Parent directory timestamps are not claimed restored. After private XDG redirection, the complete file trace contains zero home mutation candidates, home-target metadata is unchanged, and the launcher leaves those home PowerShell paths absent. This corrected startup recipe is required for subsequent use.

Readiness JSON binds archive/runtime/launcher identities and all caveats. Raw headers/download/checksum assets, member/file inventories, command receipts, original stdout/stderr, traces and rollback proof remain in this private directory. Don't copy the75MB runtime archive or192MB extracted runtime to the nearly-full primary checkout. A small evidence index/manifest is provided; Git publication is root-owned. No environment draft, apt, system/root configuration or user profile change was made.

This proves Linux runtime readiness only. Windows APIs/filesystem semantics, actual project scripts and S35/S46 remain UNVERIFIED until their own ordered execution. A later environment reset may require downloading/verifying the portable archive again; no persistent installation is claimed.
