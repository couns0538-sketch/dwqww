# pp_identity.ps1 (opus2, PowerShell 5.1) - preprocessed-source identity of two trees with the kit's exact flags.
# For every src/*.cpp unit of tree A: g++ -E -P <kit flags> [-D...] on A and on B, blank lines stripped, sha256 compared.
# IDENTICAL for all units means the compiler gets the same code from both trees (macro-0 proof of SPEC section 2).
# Runs inside the job envelope (Idle, CPUs 12-15, set on itself first and read back). Exit 0 = all identical, 1 = diff.
param(
  [Parameter(Mandatory=$true)][string]$TreeA,
  [Parameter(Mandatory=$true)][string]$TreeB,
  [Parameter(Mandatory=$true)][string]$OutDir,
  [string]$ExtraDefine = ''      # e.g. 'FORGE_SMP_LAYOUT=1' to inspect the gate preprocessing (expected to differ)
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\o2_uci_lib.ps1"
Set-OspdPlacement 0xF000 'Idle'
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
$tmp = 'D:\forge_jobs_20261107\opus2\tmp'; $env:TMP = $tmp; $env:TEMP = $tmp; $env:TMPDIR = $tmp
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$flags = @('-std=c++20', '-O3', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread', '-Iinclude', '-DFORGE_EXPOSE_TUNABLES=1', '-E', '-P')
if ($ExtraDefine) { $flags += "-D$ExtraDefine" }
$units = @(Get-ChildItem -LiteralPath (Join-Path $TreeA 'src') -Filter *.cpp | Sort-Object Name | ForEach-Object { $_.Name })
$unitsB = @(Get-ChildItem -LiteralPath (Join-Path $TreeB 'src') -Filter *.cpp | Sort-Object Name | ForEach-Object { $_.Name })
$rows = New-Object System.Collections.Generic.List[string]
$rows.Add("pp_identity $(Get-OspdNow) A=$TreeA B=$TreeB extra=[$ExtraDefine] flags: $($flags -join ' ')")
if (($units -join ',') -ne ($unitsB -join ',')) { $rows.Add("UNIT LISTS DIFFER: A [$($units -join ' ')] B [$($unitsB -join ' ')]") }
$allSame = (($units -join ',') -eq ($unitsB -join ','))
foreach ($u in $units) {
  $h = @{}
  foreach ($side in @(@('A', $TreeA), @('B', $TreeB))) {
    Push-Location -LiteralPath $side[1]
    try {
      $pp = @(& g++ @flags ("src/" + $u) 2>&1 | ForEach-Object { "$_" }); $rc = $LASTEXITCODE
    } finally { Pop-Location }
    if ($rc -ne 0) { throw "g++ -E failed on $($side[0]) $u (exit $rc): $($pp | Select-Object -First 3)" }
    $lines = @($pp | Where-Object { $_.Trim() -ne '' })
    $f = Join-Path $OutDir ("{0}_{1}.ii" -f $side[0], $u)
    [System.IO.File]::WriteAllText($f, (($lines -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false)))
    $h[$side[0]] = Get-OspdSha256 $f
  }
  $same = $h['A'] -eq $h['B']; if (-not $same) { $allSame = $false }
  $rows.Add(("{0,-16} A {1} B {2} {3}" -f $u, $h['A'].Substring(0, 16), $h['B'].Substring(0, 16), $(if ($same) { 'IDENTICAL' } else { 'DIFFERENT' })))
}
$rows.Add($(if ($allSame) { "PP IDENTITY: ALL $($units.Count) UNITS IDENTICAL" } else { "PP IDENTITY: DIFFERENT" }))
Write-OspdLf (Join-Path $OutDir 'pp_identity.txt') $rows -Force
$rows
if ($allSame) { exit 0 } else { exit 1 }
