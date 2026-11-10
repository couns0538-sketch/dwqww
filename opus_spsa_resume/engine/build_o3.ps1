# build_o3.ps1 - safe wrapper for clang_build_o3.ps1 (Windows PowerShell 5.1).
# The recipe's parameter defaults still name QA's D:\sdk_jobs tree, exactly as QA's 1fd87517 does. The recipe file
# stays byte-identical to the one that produced the receipted builds (sha256 77d4e79b...), so this wrapper adds the
# guards instead:
#   - -Tag, -Src, -OutRoot and -Workload are mandatory;
#   - another job's tree (D:\sdk_jobs, D:\forge_jobs_20261109) is refused for -Src and -OutRoot;
#   - -OutRoot must lie under -AllowedRoot (default: this job's out\ folder);
#   - the recipe's sha256 must be the receipted one.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File build_o3.ps1 -Tag <9-char tag> -Src <tree>
#       -OutRoot <dir> -Workload <frozen_train_cmds.txt> [-ExtraDefines 'NAME=V;NAME=V'] [-AllowedRoot <dir>]
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$Src,
    [Parameter(Mandatory = $true)][string]$OutRoot,
    [Parameter(Mandatory = $true)][string]$Workload,
    [string]$ExtraDefines = '',
    [string]$AllowedRoot = 'D:\forge_jobs_20261107\opus3\out',
    [long]$Mask = 0xF000
)
$ErrorActionPreference = 'Stop'
function Full([string]$p) { [IO.Path]::GetFullPath($p).TrimEnd('\') }
$out = Full $OutRoot; $src = Full $Src; $allowed = Full $AllowedRoot
foreach ($bad in 'D:\sdk_jobs', 'D:\forge_jobs_20261109') {
    foreach ($p in $out, $src) {
        if (($p + '\').StartsWith($bad + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "refusing: $p lies in another job's tree ($bad)" }
    }
}
if (-not ($out + '\').StartsWith($allowed + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "refusing: -OutRoot $out is outside -AllowedRoot $allowed" }
$recipe = Join-Path $PSScriptRoot 'clang_build_o3.ps1'
$sha = (Get-FileHash -LiteralPath $recipe -Algorithm SHA256).Hash.ToLower()
if ($sha -ne '77d4e79bc97685cef835157ff007cce0fe1508c7e3a64ed8393511b32c886417') { throw "recipe sha256 $sha is not the receipted 77d4e79b..." }
$ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$argv = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $recipe, '-Tag', $Tag, '-Src', $src, '-OutRoot', $out,
          '-Workload', $Workload, '-Mask', "$Mask")
if ($ExtraDefines) { $argv += @('-ExtraDefines', $ExtraDefines) }
& $ps @argv
exit $LASTEXITCODE
