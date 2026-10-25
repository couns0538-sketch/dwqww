# Focused portable PowerShell semantics only. No native Session, Win32 API,
# engine compiler, chess engine, profile or performance workload is invoked.
[CmdletBinding()]
param(
    [string]$FixtureRoot = (Join-Path $PSScriptRoot ('forge_sol_pgo_exit_fixtures_20261025_' + [Guid]::NewGuid().ToString('N')))
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$package = [IO.Path]::GetFullPath($PSScriptRoot)
$folder = [IO.Path]::GetFullPath($FixtureRoot)
$prefix = $package.TrimEnd([IO.Path]::DirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
if (-not $folder.StartsWith($prefix,[StringComparison]::Ordinal)) { throw 'FixtureRoot must stay in this fixture own folder' }
if (Test-Path -LiteralPath $folder) { throw 'FixtureRoot already exists; preserve earlier evidence' }
[void][IO.Directory]::CreateDirectory($folder)
$wrapper = Join-Path $package 'forge_sol_pgo_build_20261025.ps1'
$production = Join-Path $package 'forge_sol_pgo_winqual_script_20261025.ps1'
$before = Join-Path $package 'forge_sol_pgo_evidence_20261025/forge_sol_pgo_winqual_pre_exitfix_20261025.ps1'
$text = [IO.File]::ReadAllText($production)
$old = [IO.File]::ReadAllText($before)
if ($text -ne ($old+"exit 0`n")) { throw 'Production change is not exactly the explicit success exit0 append' }
foreach ($file in @($wrapper,$production)) {
    $tokens=$null; $errors=$null
    $null=[Management.Automation.Language.Parser]::ParseFile($file,[ref]$tokens,[ref]$errors)
    if ($errors.Count) { throw "PowerShell parse failure: $file" }
}
$tailStart="if (`$status -notlike 'DONE_*') { exit 1 }"
$tail=$text.Substring($text.LastIndexOf($tailStart,[StringComparison]::Ordinal))
$oldTail=$old.Substring($old.LastIndexOf($tailStart,[StringComparison]::Ordinal))
$pwsh=(Get-Process -Id $PID).Path
$rows=[Collections.Generic.List[object]]::new()
foreach ($case in @(@('success','DONE_SOFTWARE_FIXTURE',$tail,0),
                    @('failure','UNVERIFIED_SOFTWARE_FIXTURE',$tail,1),
                    @('pre_fix_success','DONE_SOFTWARE_FIXTURE',$oldTail,1))) {
    $name=[string]$case[0]
    $childFolder=Join-Path $folder ('forge_sol_pgo_exit_'+$name+'_20261025')
    [void][IO.Directory]::CreateDirectory($childFolder)
    $actualWrapper=Join-Path $childFolder 'forge_sol_pgo_build_20261025.ps1'
    [IO.File]::Copy($wrapper,$actualWrapper,$false)
    # Replace only the private child: actual wrapper bytes and production exit
    # trailer are exercised in a fresh StrictMode PowerShell process.
    $fakeChild=Join-Path $childFolder 'forge_sol_pgo_winqual_script_20261025.ps1'
    $fake="param([string]`$Source,[string]`$Out,[string]`$Recipe,[string]`$Gpp,[string]`$Python,[string]`$CMake)`n"
    $fake+="# SYNTHETIC CHILD: exit forwarding only; no native qualification.`n`$status = '$($case[1])'`n"+[string]$case[2]
    [IO.File]::WriteAllText($fakeChild,$fake,[Text.UTF8Encoding]::new($false))
    $psi=[Diagnostics.ProcessStartInfo]::new()
    $psi.FileName=$pwsh; $psi.UseShellExecute=$false
    $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    foreach ($arg in @('-NoProfile','-NonInteractive','-File',$actualWrapper)) { [void]$psi.ArgumentList.Add($arg) }
    $process=[Diagnostics.Process]::new(); $process.StartInfo=$psi
    if (-not $process.Start()) { throw 'Fresh PowerShell fixture failed to start' }
    $outTask=$process.StandardOutput.ReadToEndAsync(); $errTask=$process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $stdout=$outTask.GetAwaiter().GetResult(); $stderr=$errTask.GetAwaiter().GetResult()
    [IO.File]::WriteAllText((Join-Path $childFolder 'forge_sol_pgo_exit_stdout_20261025.txt'),$stdout)
    [IO.File]::WriteAllText((Join-Path $childFolder 'forge_sol_pgo_exit_stderr_20261025.txt'),$stderr)
    if ($process.ExitCode -ne [int]$case[3]) { throw "Wrong forwarded exit for $name : $($process.ExitCode)" }
    if ($name -eq 'pre_fix_success' -and $stderr -notmatch 'LASTEXITCODE') { throw 'Pre-fix success did not reproduce undefined LASTEXITCODE failure' }
    if ($name -ne 'pre_fix_success' -and $stderr.Length -ne 0) { throw "Unexpected forwarding error for $name : $stderr" }
    $rows.Add([pscustomobject]@{name=$name;actual_exit=$process.ExitCode;expected_exit=[int]$case[3];status='PASS';synthetic_child=$true})
    $process.Dispose()
}
$record=[pscustomobject]@{status='PASS_SOFTWARE_ONLY';cases=$rows;actual_wrapper_sha256=(Get-FileHash $wrapper -Algorithm SHA256).Hash.ToLowerInvariant();production_orchestrator_sha256=(Get-FileHash $production -Algorithm SHA256).Hash.ToLowerInvariant();change='only append explicit success exit0';native_windows_verified=$false;engine_or_profile_or_performance_run=$false;Session_or_Win32_invoked=$false}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $folder 'forge_sol_pgo_exit_forwarding_verification_20261025.json') -Encoding utf8
Write-Host "PASS: actual public wrapper forwards fresh-process success0/failure1; pre-fix success reproduces LASTEXITCODE error. Proof=$folder"
