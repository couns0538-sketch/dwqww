$ErrorActionPreference = 'Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'Idle'
$root = 'D:\a14'
if ((Get-PSDrive D).Free -lt 50GB -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor' }
$utf8 = New-Object System.Text.UTF8Encoding($false)
$historical = (& git -C D:/a13 show 3e900941:AGENTS.md) -join "`n"
if ($LASTEXITCODE -ne 0) { throw 'Cannot read historical policy' }
$historical += "`n"
$md5 = [BitConverter]::ToString([Security.Cryptography.MD5]::Create().ComputeHash($utf8.GetBytes($historical))).Replace('-','').ToLowerInvariant()
if ($md5 -ne '94169aefef79ccb69c21f8f2c86298f0') { throw "Historical policy MD5 mismatch: $md5" }
$section = $historical.Substring($historical.IndexOf('# Development review and verification'))
$header = @'
# Astra R14 data separation

Follow PLAN.md and current user instructions. All writes belong below D:/a14.
D:/a13 and frozen inputs are read-only. Use only the independent R14 runtime.
No training, GPU, engine changes, production changes, queues or protected imports.
Keep D: above 50 GiB, C: above 30 GiB and owned storage below 5 GB.
Use Idle priority, at most four activity slots including a reviewer, and no more
than two single-thread computation workers. No inferred game-ID clearance.
Commit as Astra <astra@forge.local>; push only astra-r14-20261103 without force.
Times are Vienna wall time. Preserve evidence and follow the nine-hour plan.

'@
[IO.File]::WriteAllText((Join-Path $root 'AGENTS.md'), $header.Replace("`r`n","`n") + "`n" + $section, $utf8)
foreach ($dir in @('evidence\r14','evidence\review\r14','evidence\test_logs\r14','runtime','tmp','sep')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $root $dir) | Out-Null
}
$receipt = @{ historical_policy_md5=$md5; base='11d382085f29310980d4822cd6b8d382d9910185'; start_vienna='2026-11-03 12:41:11 Vienna'; branch='astra-r14-20261103'; origin='https://github.com/couns0538-sketch/dwqww.git'; independent_git_objects= -not (Test-Path -LiteralPath (Join-Path $root '.git\objects\info\alternates')) }
[IO.File]::WriteAllText((Join-Path $root 'evidence\r14\initialization.json'), ($receipt | ConvertTo-Json), $utf8)
