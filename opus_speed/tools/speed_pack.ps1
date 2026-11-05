# speed_pack.ps1 - one command: source tree in, lock-candidate exe + proof pack out (speed job, PowerShell 5.1).
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File speed_pack.ps1 -SrcDir <tree> -Name <pack name>
#          [-Variant lp_v1] [-Define 'FORGE_SPD_X=1',..] [-Depth 20] [-Rounds 10] [-AaCsv <session A/A runs.csv>]
#          [-Quick] [-SkipAbba] [-SanNdebug] [-Note '<one line>']
# Steps: (1) -Define given -> src_kit = copy of -SrcDir with each '#define N 0' default flipped to the value (exactly one
# match per switch; the kit takes no -D flags, so QA's kit builds src_kit as it is); (2) build_variants -Twice: pc1 and
# pc2 must give the same exe sha256; (3) bitexact_check (full 12k unless -Quick) incl. the clang ASan+UBSan level on
# the built source; stop if not bit-exact; (4) abba vs the lock exe (net on, CPU 2) with the session's A/A band;
# (5) F:\ospd\packs\<Name>\: exe, SUMMARY.md, signature.txt, build logs, bitexact\, abba_d<D>\ and the repo file
# opus_speed\candidates\<Name>.md. Exit 0 pack written (any ratio), 3 not bit-exact / not reproducible, 1 error.
param(
  [Parameter(Mandatory = $true)][string]$SrcDir,
  [Parameter(Mandatory = $true)][string]$Name,
  [string]$Variant = 'lp_v1',
  [string[]]$Define = @(),
  [int]$Depth = 20,
  [int]$Rounds = 10,
  [string]$AaCsv = '',
  [switch]$Quick,
  [switch]$SkipAbba,
  [switch]$SanNdebug,
  [string]$Note = ''
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\uci_lib.ps1"
# -File passes a list as ONE comma-joined string: split every list parameter on commas
$Define = @($Define | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$RepoDir = Split-Path -Parent $PSScriptRoot
$Pack = Join-Path 'F:\ospd\packs' $Name
function Say([string]$Msg) { $l = "$(Get-OspdNow) $Msg"; Write-Output $l; Add-OspdLf (Join-Path $Pack 'pack.log') $l }

try {
  if (Test-Path $Pack) { throw "$Pack exists; use a new -Name" }
  $null = Assert-OspdDisk -PlannedGB 0.4
  New-Item -ItemType Directory -Path $Pack | Out-Null
  Say "speed_pack $Name: src $SrcDir variant $Variant defines [$($Define -join ' ')] $Note"
  # (1) kit source variant
  $buildSrc = $SrcDir
  if ($Define.Count -gt 0) {
    $buildSrc = Join-Path $Pack 'src_kit'
    Copy-Item -Recurse -LiteralPath $SrcDir -Destination $buildSrc
    Get-ChildItem -Recurse -File $buildSrc | ForEach-Object { $_.IsReadOnly = $false }
    foreach ($kv in $Define) {
      $nm = $kv.Split('=')[0]; $val = $kv.Split('=')[1]
      $hits = @(Get-ChildItem -Recurse -File $buildSrc -Include *.hpp, *.cpp, *.inc | Select-String -Pattern ("^#define {0} 0\r?$" -f [regex]::Escape($nm)))
      if ($hits.Count -ne 1) { throw "switch $nm : found $($hits.Count) '#define $nm 0' lines (need exactly 1)" }
      $f = $hits[0].Path
      $bytes = [System.IO.File]::ReadAllText($f)
      $new = [regex]::Replace($bytes, ("(?m)^#define {0} 0(\r?)$" -f [regex]::Escape($nm)), ("#define {0} {1}`$1" -f $nm, $val))
      [System.IO.File]::WriteAllText($f, $new, (New-Object System.Text.UTF8Encoding($false)))
      Say "kit default flipped: $nm = $val in $f"
    }
  }
  # (2) build twice
  $bv = @(& "$PSScriptRoot\build_variants.ps1" -SrcDir $buildSrc -Tag ("pack_" + $Name) -Variant $Variant -Twice -Work 'F:\ospd\builds')
  $bvRc = $LASTEXITCODE
  $bv | ForEach-Object { Add-OspdLf (Join-Path $Pack 'build_variants.out') "$_" }
  Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
  $exeLine = @($bv | Where-Object { $_ -like 'EXE *_pc1 *' }) | Select-Object -First 1
  $repro = @($bv | Where-Object { $_ -like 'REPRO *' }) | Select-Object -First 1
  if ($bvRc -ne 0 -or -not $exeLine -or -not $repro) { Say "BUILD FAILED or NOT REPRODUCIBLE (rc $bvRc): $($bv -join ' | ')"; exit 3 }
  $builtExe = ($exeLine -split ' ')[2]
  $exe = Join-Path $Pack ("forge_{0}.exe" -f $Name)
  Copy-Item -LiteralPath $builtExe -Destination $exe
  $sha = Get-OspdSha256 $exe; $md5 = Get-OspdMd5 $exe
  Say "exe $exe sha256 $sha md5 $md5 ($repro)"
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent (Split-Path -Parent $builtExe)) 'SUMMARY.txt') -Destination (Join-Path $Pack 'build_SUMMARY_pc1.txt')
  # (3) bit-exact proof
  $bxArgs = @{ Cand = $exe; Out = (Join-Path $Pack 'bitexact'); SanSrc = $buildSrc }
  if ($Quick) { $bxArgs.Quick = $true }
  if ($SanNdebug) { $bxArgs.SanNdebug = $true }
  $bx = @(& "$PSScriptRoot\bitexact_check.ps1" @bxArgs); $bxRc = $LASTEXITCODE
  Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
  $bxVerdict = @($bx | Where-Object { $_ -like 'VERDICT*' -or $_ -like 'ERROR*' }) -join ' '
  Say "bitexact rc $bxRc: $bxVerdict"
  $sigFile = Get-ChildItem (Join-Path $Pack 'bitexact\cand') -Filter 'sig_*.json' | Select-Object -First 1
  $sig = $null; if ($sigFile) { $sig = Get-Content $sigFile.FullName -Raw | ConvertFrom-Json }
  $sigTxt = 'n/a'
  if ($sig) {
    $sigTxt = ("net on d11/13/16/20/22 {0}/{1}/{2}/{3}/{4}; net off {5}/{6}/{7}/{8}/{9}; perft 5 startpos {10} kiwipete {11}" -f $sig.on.d11, $sig.on.d13, $sig.on.d16, $sig.on.d20, $sig.on.d22, $sig.off.d11, $sig.off.d13, $sig.off.d16, $sig.off.d20, $sig.off.d22, $sig.perft.startpos, $sig.perft.kiwipete)
    Write-OspdLf (Join-Path $Pack 'signature.txt') @("exe $exe sha256 $sha", $sigTxt)
  }
  if ($bxRc -ne 0) { Say "NOT BIT-EXACT or check error: no ABBA (pack kept as a record)"; $abbaTxt = 'not run (not bit-exact)' }
  # (4) ABBA
  $abbaDir = Join-Path $Pack ("abba_d{0}" -f $Depth)
  $abbaTxt = 'skipped (-SkipAbba)'
  if ($bxRc -eq 0 -and -not $SkipAbba) {
    $ab = @{ A = $script:OspdLockExe; B = $exe; Out = $abbaDir; Depth = $Depth; Rounds = $Rounds; LabelA = 'lock FD3A5190'; LabelB = $Name }
    if ($AaCsv) { $ab.AaCsv = $AaCsv }
    $abOut = @(& "$PSScriptRoot\abba.ps1" @ab); $abRc = $LASTEXITCODE
    Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
    $abOut | ForEach-Object { Say "abba: $_" }
    if ($abRc -ne 0) { throw "abba failed rc $abRc" }
    $abbaTxt = ($abOut -join "`n")
  }
  # (5) records
  $gver = (& 'C:\msys64\ucrt64\bin\g++.exe' --version | Select-Object -First 1)
  $flags = @(Get-Content (Join-Path $Pack 'build_SUMMARY_pc1.txt') | Where-Object { $_ -like 'flags*' -or $_ -like 'training*' })
  $csvMd5 = ''; if (Test-Path (Join-Path $abbaDir 'runs.csv')) { $csvMd5 = Get-OspdMd5 (Join-Path $abbaDir 'runs.csv') }
  $md = @(
    "# Speed candidate $Name",
    '',
    "- State: $(if ($bxRc -eq 0) { 'BIT-EXACT' } else { 'NOT BIT-EXACT / check error' }); ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.",
    "- Exe: ``$exe`` md5 ``$md5`` sha256 ``$sha`` ($repro)",
    "- Source: ``$SrcDir``$(if ($Define.Count) { " with defaults flipped in ``$buildSrc``: $($Define -join ', ')" }); patch / commit: see opus_speed/patches and the branch commit that adds this file.",
    "- Build: build_variants.ps1 -Variant $Variant -Twice (QA kit v2.3 command lines, -Expose); compiler $gver",
    ($flags | ForEach-Object { "  - $_" }),
    "- Bench signature: $sigTxt",
    "- Bit-exact log: ``$Pack\bitexact\bitexact.log`` -> $bxVerdict",
    "- ABBA CSV: ``$abbaDir\runs.csv`` md5 ``$csvMd5``",
    '- ABBA summary:',
    '```',
    $abbaTxt,
    '```',
    "- Note: $Note"
  )
  $md = @($md | ForEach-Object { $_ })
  Write-OspdLf (Join-Path $Pack 'SUMMARY.md') $md
  Write-OspdLf (Join-Path $RepoDir ("candidates\{0}.md" -f $Name)) $md
  Say "pack written: $Pack ; candidate file opus_speed\candidates\$Name.md"
  if ($bxRc -ne 0) { exit 3 }
  exit 0
} catch {
  Write-Output "ERROR: $($_.Exception.Message)"
  try { Add-OspdLf (Join-Path $Pack 'pack.log') "ERROR: $($_.Exception.Message)" } catch {}
  exit 1
}
