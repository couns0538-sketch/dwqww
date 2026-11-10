# make_bundle.ps1 - build the ALL-ON bundle tree from the single patches (PowerShell 5.1, ASCII only).
# Applies the single patches to fresh copies of the combo29 snapshot in two different orders with plain
# `git apply` (no fuzz, no 3-way), requires both trees to be identical, and writes out\work\<Name>\{a,b}.
# The bundle patch itself is then written by cand_step.ps1 -Stage patch -Name <Name>.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File make_bundle.ps1 -Singles A,B,C [-Name BUNDLE]
param(
    [Parameter(Mandatory = $true)][string[]]$Singles,
    [string]$Name = 'BUNDLE',
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$Singles = @($Singles | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
if ($Singles.Count -lt 2) { throw 'a bundle needs at least two singles' }
$base = Join-Path $OUT 'base\combo29_src'
$work = Join-Path $OUT "work\$Name"
if (Test-Path $work) { throw "refusing: $work exists" }
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
function ApplyAll([string]$dir, [string[]]$order) {
    Copy-Item -Recurse $base $dir
    Get-ChildItem $dir -Recurse -File | ForEach-Object { $_.IsReadOnly = $false }
    foreach ($s in $order) {
        $patch = Join-Path $PACK "patches\${s}_after_combo29.patch"
        Push-Location $dir
        try {
            $ErrorActionPreference = 'Continue'
            $msg = & git -c core.autocrlf=false apply -v --whitespace=nowarn $patch 2>&1 | ForEach-Object { "$_" }
            $code = $LASTEXITCODE
            $ErrorActionPreference = 'Stop'
        } finally { Pop-Location }
        if ($code -ne 0) { throw "git apply of $s failed in order [$($order -join ' ')]: $($msg -join ' | ')" }
        $off = @($msg | Where-Object { $_ -match 'offset' }).Count
        Write-Output ("  applied {0} ({1} hunks moved by an offset, none with fuzz)" -f $s, $off)
    }
}
$rev = @($Singles); [Array]::Reverse($rev)
$t1 = Join-Path $OUT "tmp\bundle_o1_$Name"; $t2 = Join-Path $OUT "tmp\bundle_o2_$Name"
foreach ($d in $t1, $t2) { if (Test-Path $d) { Remove-Item -Recurse -Force $d } }
Write-Output ("order 1: " + ($Singles -join ', ')); ApplyAll $t1 $Singles
Write-Output ("order 2: " + ($rev -join ', ')); ApplyAll $t2 $rev
$diff = 0; $changed = @()
foreach ($f in Get-ChildItem $t1 -Recurse -File) {
    $rel = $f.FullName.Substring($t1.Length + 1)
    if ((Sha $f.FullName) -ne (Sha (Join-Path $t2 $rel))) { $diff++ }
    if ((Sha $f.FullName) -ne (Sha (Join-Path $base $rel))) { $changed += $rel.Replace('\', '/') }
}
if ($diff -ne 0) { throw "the two apply orders give different trees ($diff files)" }
New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item -Recurse $base (Join-Path $work 'a')
Move-Item $t1 (Join-Path $work 'b')
Remove-Item -Recurse -Force $t2
Write-Output ("BUNDLE {0}: {1} singles, both apply orders give the same tree; changed files [{2}]; tree at {3}" -f $Name, $Singles.Count, ($changed -join ' '), (Join-Path $work 'b'))
