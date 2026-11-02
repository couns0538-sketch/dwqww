$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../scripts/Invoke-GrokPcSafeRun.ps1')
$checks = 0
function Must-Refuse([scriptblock]$Action) {
    $failed = $false
    try { & $Action | Out-Null } catch { $failed = $true }
    if (-not $failed) { throw 'Expected policy refusal' }
    $script:checks++
}
if ((Assert-R10WritePath 'D:\a11\runtime\fixture' @()) -ne 'D:\a11\runtime\fixture') { throw 'R11 output rejected' }
$checks++
Must-Refuse { Assert-R10WritePath 'D:\a10\fixture' @() }
Must-Refuse { Assert-R10WritePath 'C:\fixture' @() }
Must-Refuse { Assert-R10WritePath 'F:\fixture' @() }
Must-Refuse { Assert-DPath 'D:\a11\x.nnue' @() }
Must-Refuse { Assert-DPath 'D:\a11\forge_queue_state.json' @() }
Must-Refuse { Assert-DPath 'D:\a11\STOP' @() }
Must-Refuse { Assert-DPath 'D:\a11\PAUSE' @() }
Must-Refuse { Assert-DPath 'D:\a11\x.nnue.' @() }
Must-Refuse { Assert-DPath 'D:\a11\x.nnue ' @() }
Must-Refuse { Assert-DPath 'D:\a10.\fixture' @() }
Must-Refuse { Assert-DPath 'D:\a11\forge_queue_state.json.' @() }
Must-Refuse { Assert-R10StorageBudget 29GB 100GB 0 0 51200 }
Must-Refuse { Assert-R10StorageBudget 40GB 50GB 0 1 51200 }
Assert-R10StorageBudget 30GB 51GB 0 1GB 51200
$checks++
$script:r11Visited=@()
$oldGetItem=Get-Command Get-Item -CommandType Function -ErrorAction SilentlyContinue
try {
    Set-Item Function:\Get-Item {
        param([string]$LiteralPath,[switch]$Force,[object]$ErrorAction)
        $script:r11Visited+=$LiteralPath
        return [pscustomobject]@{Attributes=$(if($LiteralPath -eq 'D:\a11\junction'){[IO.FileAttributes]::ReparsePoint}else{[IO.FileAttributes]::Directory})}
    }
    Must-Refuse { Assert-NoReparsePath 'D:\a11\junction\must-not-inspect' }
    if(($script:r11Visited -join '|') -cne 'D:\|D:\a11|D:\a11\junction'){throw 'Reparse check inspected descendants before ancestors'}
    $checks++
} finally {
    if($oldGetItem){Set-Item Function:\Get-Item $oldGetItem.ScriptBlock}else{Remove-Item Function:\Get-Item}
}
Write-Output "PASS $checks R11 path/storage checks; no forbidden path inspected"
