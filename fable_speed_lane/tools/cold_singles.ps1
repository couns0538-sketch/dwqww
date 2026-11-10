# cold_singles.ps1 - cold 12,000-FEN runs of single candidates, net on for all of them first, then net off
# (PowerShell 5.1, ASCII only).
# Why: D: was draining towards the 30.3 GiB hold on 2026-11-10 afternoon. The chain (qualify_all.ps1) runs each
# item's two cold runs back to back; this runner takes items out of the chain's hands (their ids are written to
# chain_done.txt by hand, see chain.log) and makes the net-on run of every item before any net-off run, so that
# every new candidate has search-level rows with the net on if the hold cuts the queue short.
# Each run is one qualify.ps1 call (stage cold, one net); its QUAL line goes to out\id\<NAME>\QUALIFY.log as usual.
# A finished run is recorded in out\logs\cold_singles_done.txt and skipped on a restart.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File cold_singles.ps1 -Items CHECKERS_KL:chk:FORGE_SPD_CHECKERS_KL=1,...
param(
    [Parameter(Mandatory = $true)][string]$Items,
    [string]$NetOrder = 'on,off',
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$log = Join-Path $OUT 'logs\cold_singles.log'; $doneFile = Join-Path $OUT 'logs\cold_singles_done.txt'
function Note([string]$s) {
    $line = '[' + (NowVienna) + '] ' + $s
    Add-Content -LiteralPath $log -Value $line -Encoding ASCII
    Write-Output $line
}
$list = @($Items -split ',' | Where-Object { $_ } | ForEach-Object { $f = @($_ -split ':'); @{ N = $f[0]; G = $f[1]; D = ($f[2] -replace '\+', ',') } })
Note ("cold_singles start: " + (($list | ForEach-Object { $_.N }) -join ', ') + "; nets in the order [$NetOrder]; D: free " + (DFree) + ' GiB')
foreach ($net in @($NetOrder -split ',' | Where-Object { $_ })) {
    foreach ($x in $list) {
        $id = 'cold.' + $x.G + '.' + $net
        if (@(Get-Content -LiteralPath $doneFile -ErrorAction SilentlyContinue) -contains $id) { Note "skip $id (done earlier)"; continue }
        for ($i = 0; $i -lt 360 -and (DFree) -lt 30.3; $i++) {
            if ($i -eq 0) { Note ("HOLD before " + $id + " - D: has " + (DFree) + " GiB free, under 30.3; waiting, nothing started") }
            Start-Sleep -Seconds 120
        }
        if ((DFree) -lt 30.3) { Note "GAVE UP $id - D: still under 30.3 GiB"; continue }
        Note "start $id"
        $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $T 'qualify.ps1'), '-Name', $x.N, '-Tag', $x.G, '-Defs', $x.D, '-Stages', 'cold', '-Nets', $net, '-Mask', $Mask)
        $ErrorActionPreference = 'Continue'
        & powershell.exe @a 2>&1 | ForEach-Object { Note ("  " + "$_") }
        $code = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
        if ($code -eq 0) { Add-Content -LiteralPath $doneFile -Value $id -Encoding ASCII; Note "ok $id" } else { Note "FAILED $id (exit $code)" }
    }
}
Note 'cold_singles end'
