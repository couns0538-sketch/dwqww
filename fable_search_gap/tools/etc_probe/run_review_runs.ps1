# Runs added after the review (PowerShell 5.1 compatible, ASCII only).
# Node-count probes of the replica harness. Everything goes through tools/pin.ps1: CPU 3-6, Idle.
# Outputs only under D:\forge_jobs_20261109\fable52\out\etc_build.
#
#   -Which fine70       the classic pawn ending, depths 24 to 40: plain, placebo, the cutoff and its variants
#   -Which fine70_hash  the same position with 1, 2, 4 and 8 MB tables (plain, cut6, cut8)
#   -Which wide         the 95-position set: plain, placebo, the cutoff and its variants
#   -Which supp         the supplementary set (positions_supp.epd): plain, placebo, counting, cutoff
#   -Which fine70_grid  the pawn ending under ten placebo-size changes, plain and with every setting
param([string]$Which = 'fine70,fine70_hash,wide')
$ErrorActionPreference = 'Stop'
$J = 'D:\forge_jobs_20261109\fable52'
$T = Join-Path $J 'repo\fable_search_gap\tools'
$B = Join-Path $J 'out\etc_build'
$Exe = Join-Path $B 'etc_probe.exe'
$Pin = Join-Path $T 'pin.ps1'

function Invoke-Probe([string]$Epd, [string]$Tag, [int]$HashMb, [string]$Runs, [string]$Offset = '') {
    $free = [math]::Round((Get-PSDrive D).Free / 1GB, 2)
    if ($free -lt 31) { Write-Output "D: free $free GiB is below 31 GiB: no run"; exit 12 }
    $argLine = ("$Epd $B\$Tag.tsv $HashMb 80000000 $Runs $Offset").Trim()
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Pin -Exe $Exe `
        -ArgLine $argLine -OutFile "$B\$Tag.log" -WorkDir $B
    Write-Output ("{0} exit {1} at {2}" -f $Tag, $LASTEXITCODE, (Get-Date).ToString('HH:mm:ss'))
}

$want = ",$Which,"
$fine = Join-Path $T 'etc_probe\positions_fine70.epd'
if ($want -like '*,fine70,*') {
    Invoke-Probe $fine 'fine70_v2' 16 'off,off_p,etc_cut4,etc_cut6,etc_cut6_ns,etc_cut6_fh,etc_cut8,etc_cut8_ns,etc_cut8_fh,etc_all3'
}
if ($want -like '*,fine70_hash,*') {
    foreach ($mb in 1, 2, 4, 8) { Invoke-Probe $fine "fine70_v2_hash$mb" $mb 'off,etc_cut6,etc_cut8' }
}
if ($want -like '*,wide,*') {
    Invoke-Probe (Join-Path $T 'etc_probe\positions_wide.epd') 'wide_variants' 16 'off,off_p,etc_cut6,etc_cut6_ns,etc_cut6_fh,etc_cut8,etc_cut8_ns,etc_cut8_fh'
}
if ($want -like '*,fine70_grid,*') {
    # Ten placebo-size changes of one history constant (default -32). Each is run plain and with every setting.
    foreach ($o in -40, -38, -36, -34, -33, -31, -30, -28, -26, -24) {
        Invoke-Probe $fine ("fine70_grid_o{0}" -f [math]::Abs($o)) 16 'off,etc_cut4,etc_cut6,etc_cut6_ns,etc_cut6_fh,etc_cut8,etc_cut8_ns,etc_cut8_fh,etc_all3' "$o"
    }
}
if ($want -like '*,supp,*') {
    Invoke-Probe (Join-Path $T 'etc_probe\positions_supp.epd') 'supp' 16 'off,off_p,probe_cut6,probe_cut8,etc_cut6,etc_cut8'
}
exit 0
