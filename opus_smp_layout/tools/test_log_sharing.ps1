# test_log_sharing.ps1 (opus2, PowerShell 5.1) - fault injection for the fable bug hunt MINOR-1 (log sharing).
# Starts identity_check.ps1 (cold, a short FEN slice) from -ToolsDir in a child PowerShell and, while it runs, keeps
# opening its UCI log with FileShare.Read (a "hostile" reader that refuses to share writing), holding it for 200 ms each
# time. Reports whether the identity run still finished cleanly (exit 0, a COLD verdict line) and how often the reader got
# the file. Expected: the current tools PASS (the persistent writer holds the log, so the hostile open fails on the reader
# side); the tools of a675c04 (per-line AppendAllText) FAIL, which shows that the test can fail.
# Runs inside the job envelope: pins itself (CPUs 12-15, Idle) first; children inherit it. Never ends a process.
param(
  [Parameter(Mandatory=$true)][string]$ToolsDir,
  [Parameter(Mandatory=$true)][string]$Exe,
  [Parameter(Mandatory=$true)][string]$OutDir,
  [Parameter(Mandatory=$true)][string]$Tag,
  [int]$Count = 300,
  [int]$Depth = 10
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\o2_uci_lib.ps1"
Set-OspdPlacement 0xF000 'Idle'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$log = Join-Path $OutDir "$Tag.cold.uci.log"
if (Test-Path -LiteralPath $log) { throw "log already exists (use a fresh -Tag): $log" }
$runOut = Join-Path $OutDir "$Tag.run.txt"
$childArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $ToolsDir 'identity_check.ps1'), '-Exe', $Exe, '-Tag', $Tag,
          '-Mode', 'cold', '-OutDir', $OutDir, '-First', '0', '-Count', "$Count", '-Depth', "$Depth")
$p = Start-Process -FilePath 'powershell.exe' -ArgumentList $childArgs -NoNewWindow -PassThru -RedirectStandardOutput $runOut -RedirectStandardError "$runOut.stderr.txt"
$null = $p.Handle
$grabs = 0; $refused = 0
while (-not $p.HasExited) {
  if (Test-Path -LiteralPath $log) {
    try {
      $f = [System.IO.File]::Open($log, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
      $grabs++
      Start-Sleep -Milliseconds 200
      $f.Dispose()
    } catch { $refused++ }
  }
  Start-Sleep -Milliseconds 30
}
$p.WaitForExit()
$verdict = (Get-Content -LiteralPath $runOut -ErrorAction SilentlyContinue | Select-Object -First 1)
$clean = ($p.ExitCode -eq 0) -and ($verdict -like 'COLD:*')
$summary = "test_log_sharing tools=$ToolsDir tag=$Tag | identity exit $($p.ExitCode) | verdict: $verdict | hostile reader: got the log $grabs times, refused $refused times | RESULT $(if ($clean) { 'RUN SURVIVED' } else { 'RUN BROKEN' })"
Write-OspdLf (Join-Path $OutDir "$Tag.sharing.txt") @($summary) -Force
$summary
if ($clean) { exit 0 } else { exit 1 }
