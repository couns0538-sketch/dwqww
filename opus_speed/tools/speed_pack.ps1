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
  [string]$Note = '',
  [string[]]$ReuseBuildDirs = @(),
  [string]$PriorBitexact = ''
)
# -PriorBitexact <bitexact folder of an earlier pack of the SAME exe>: bitexact_check -ResumeFrom (its L1-L3 PASS lines
# are reused after a sha256 check; L4 runs again).
# -ReuseBuildDirs '<pc1 build folder>,<pc2 build folder>': skip step (2) and reuse two finished build_variants folders
# of an earlier pack (both SUMMARY 'RESULT PASS' with pins OK, no FAILED marker, equal exe sha256, and their src_copy
# include\ + src\ files byte-identical to this pack's build source). For re-running a pack whose later step failed.
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
  Say "speed_pack ${Name}: src $SrcDir variant $Variant defines [$($Define -join ' ')] $Note"
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
  # (2) build twice (or reuse two verified build folders)
  $ReuseBuildDirs = @($ReuseBuildDirs | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
  if ($ReuseBuildDirs.Count -gt 0) {
    if ($ReuseBuildDirs.Count -ne 2) { throw '-ReuseBuildDirs needs exactly two folders (pc1, pc2)' }
    $shas = @()
    foreach ($bd in $ReuseBuildDirs) {
      $sm = Join-Path $bd 'SUMMARY.txt'
      if (-not (Test-Path $sm) -or (Test-Path (Join-Path $bd 'FAILED'))) { throw "reuse: $bd has no SUMMARY or a FAILED marker" }
      $st = Get-Content $sm -Raw
      if ($st -notmatch 'RESULT PASS' -or $st -notmatch 'quick pins .* OK') { throw "reuse: $bd is not RESULT PASS with pins OK" }
      $ex = @(Get-ChildItem (Join-Path $bd 'src_copy') -Filter "forge_$Variant.exe")
      if ($ex.Count -ne 1) { throw "reuse: no forge_$Variant.exe in $bd\src_copy" }
      $shas += (Get-OspdSha256 $ex[0].FullName)
      foreach ($sub in 'include', 'src') {
        foreach ($f in (Get-ChildItem -Recurse -File (Join-Path $buildSrc $sub))) {
          $twin = Join-Path (Join-Path $bd 'src_copy') ($f.FullName.Substring($buildSrc.Length + 1))
          if (-not (Test-Path -LiteralPath $twin) -or (Get-OspdSha256 $f.FullName) -ne (Get-OspdSha256 $twin)) { throw "reuse: $twin differs from this pack's build source" }
        }
        # and the other direction: no extra file in the reused tree (review SHOULD 1)
        $copySub = Join-Path (Join-Path $bd 'src_copy') $sub
        foreach ($g in (Get-ChildItem -Recurse -File $copySub)) {
          $mine = Join-Path $buildSrc ($g.FullName.Substring((Join-Path $bd 'src_copy').Length + 1))
          if (-not (Test-Path -LiteralPath $mine)) { throw "reuse: $($g.FullName) has no twin in this pack's build source (extra file)" }
        }
      }
    }
    if ($shas[0] -ne $shas[1]) { Say "NOT REPRODUCIBLE (reused): $($shas -join ' vs ')"; exit 3 }
    $builtExe = Join-Path (Join-Path $ReuseBuildDirs[0] 'src_copy') "forge_$Variant.exe"
    $repro = "REPRO $Variant pc1 = pc2 sha256 $($shas[0]) (reused build folders $($ReuseBuildDirs -join ', '); sources byte-identical to this pack's)"
    Say $repro
  } else {
  $bv = @(& "$PSScriptRoot\build_variants.ps1" -SrcDir $buildSrc -Tag ("pack_" + $Name) -Variant $Variant -Twice -Work 'F:\ospd\builds')
  $bvRc = $LASTEXITCODE
  $bv | ForEach-Object { Add-OspdLf (Join-Path $Pack 'build_variants.out') "$_" }
  Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
  $exeLine = @($bv | Where-Object { $_ -like 'EXE *_pc1 *' }) | Select-Object -First 1
  $repro = @($bv | Where-Object { $_ -like 'REPRO *' }) | Select-Object -First 1
  if ($bvRc -ne 0 -or -not $exeLine -or -not $repro) { Say "BUILD FAILED or NOT REPRODUCIBLE (rc $bvRc): $($bv -join ' | ')"; exit 3 }
  # fail closed (Code Review blocker): both sides must report 'pins OK'; anything else stops the pack
  $pinLines = @($bv | Where-Object { $_ -like 'EXE *' })
  if ($pinLines.Count -lt 2 -or @($pinLines | Where-Object { $_ -notmatch ' pins OK ' }).Count -ne 0) { Say "PINS NOT OK: $($pinLines -join ' | ')"; exit 3 }
  $builtExe = ($exeLine -split ' ')[2]
  }
  $exe = Join-Path $Pack ("forge_{0}.exe" -f $Name)
  Copy-Item -LiteralPath $builtExe -Destination $exe
  $sha = Get-OspdSha256 $exe; $md5 = Get-OspdMd5 $exe
  if ($repro -notmatch [regex]::Escape($sha)) { throw "pack exe sha256 $sha is not the REPRO sha256 ($repro) (review LOW 11)" }
  Say "exe $exe sha256 $sha md5 $md5 ($repro)"
  Copy-Item -LiteralPath (Join-Path (Split-Path -Parent (Split-Path -Parent $builtExe)) 'SUMMARY.txt') -Destination (Join-Path $Pack 'build_SUMMARY_pc1.txt')
  # (3) bit-exact proof
  $bxArgs = @{ Cand = $exe; Out = (Join-Path $Pack 'bitexact'); SanSrc = $buildSrc }
  if ($Quick) { $bxArgs.Quick = $true }
  if ($PriorBitexact) { $bxArgs.ResumeFrom = $PriorBitexact }
  if ($SanNdebug) { $bxArgs.SanNdebug = $true }
  $bx = @(& "$PSScriptRoot\bitexact_check.ps1" @bxArgs); $bxRc = $LASTEXITCODE
  Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
  $bxVerdict = @($bx | Where-Object { $_ -like 'VERDICT*' -or $_ -like 'ERROR*' }) -join ' '
  Say "bitexact rc ${bxRc}: $bxVerdict"
  $sigFile = Get-ChildItem (Join-Path $Pack 'bitexact\cand') -Filter 'sig_*.json' | Select-Object -First 1
  $sig = $null; if ($sigFile) { $sig = Get-Content $sigFile.FullName -Raw | ConvertFrom-Json }
  $sigTxt = 'n/a'
  if ($sig) {
    $sigTxt = ("net on d11/13/16/20/22 {0}/{1}/{2}/{3}/{4}; net off {5}/{6}/{7}/{8}/{9}; perft 5 startpos {10} kiwipete {11}" -f $sig.on.d11, $sig.on.d13, $sig.on.d16, $sig.on.d20, $sig.on.d22, $sig.off.d11, $sig.off.d13, $sig.off.d16, $sig.off.d20, $sig.off.d22, $sig.perft.startpos, $sig.perft.kiwipete)
    Write-OspdLf (Join-Path $Pack 'signature.txt') @("exe $exe sha256 $sha", $sigTxt)
  }
  $bxState = 'CHECK ERROR (no verdict: the proof did not finish)'; if ($bxRc -eq 0) { $bxState = 'BIT-EXACT' } elseif ($bxRc -eq 3) { $bxState = 'NOT BIT-EXACT' }
  # the qualifier belongs in the state line, not only in the quoted verdict (review SHOULD 3)
  if ($bxRc -eq 0 -and $bxVerdict -match 'ASan N/A') { $bxState = 'BIT-EXACT with L4 = UBSan only (ASan N/A for this source under MSVC)' }
  if ($bxRc -eq 0 -and $bxVerdict -match 'quick subset') { $bxState += '; L3 on the first 2,000 of the 12k FENs (quick)' }
  if ($bxRc -ne 0) { Say "$bxState : no ABBA (pack kept as a record)" }
  # (4) ABBA
  $abbaDir = Join-Path $Pack ("abba_d{0}" -f $Depth)
  $abbaTxt = 'skipped (-SkipAbba)'
  if ($bxRc -ne 0) { $abbaTxt = "not run: $bxState" }
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
  $patchFile = Join-Path $RepoDir ("patches\{0}.patch" -f (Split-Path $SrcDir -Leaf))
  $patchTxt = "no patch file (source = the lock or a stack made by make_stack.sh)"
  if (Test-Path -LiteralPath $patchFile) {
    $patchTxt = "patch opus_speed/patches/{0} md5 {1}" -f (Split-Path $patchFile -Leaf), (Get-OspdMd5 $patchFile)
    # verify that lock + patch IS the built source (review SHOULD 2): diff the lock against -SrcDir now and compare the
    # hunks with the patch file, ignoring the '--- ' / '+++ ' / 'diff ' header lines (they carry paths and times)
    $srcParent = Split-Path -Parent ($SrcDir -replace '/', '\')
    if ((Resolve-Path $srcParent).Path -eq (Resolve-Path 'F:\ospd\src').Path) {
      $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
      try { Push-Location 'F:\ospd\src'; $now = @(& 'C:\Program Files\Git\usr\bin\diff.exe' -ruN lock (Split-Path $SrcDir -Leaf) 2>&1 | ForEach-Object { "$_" }) } finally { Pop-Location; $ErrorActionPreference = $eap }
      $body = { param($ls) @($ls | Where-Object { $_ -notmatch '^(--- |\+\+\+ |diff )' }) -join "`n" }
      if ((& $body $now) -eq (& $body (Get-Content $patchFile))) { $patchTxt += ' (verified: lock + this patch = the built source)' }
      else { $patchTxt += ' (WARNING: the patch DOES NOT MATCH the built source; see the source tree)' }
    } else { $patchTxt += ' (not verified: the source is not under F:\ospd\src)' }
  }
  $headTxt = 'branch head at pack time: unknown'
  $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try { $hd = @(& git -C (Split-Path -Parent $RepoDir) rev-parse --short=8 HEAD 2>&1 | ForEach-Object { "$_" }); if ($LASTEXITCODE -eq 0 -and $hd.Count) { $headTxt = "branch head at pack time: $($hd[0])" } } catch {} finally { $ErrorActionPreference = $eap }
  $gver = (& 'C:\msys64\ucrt64\bin\g++.exe' --version | Select-Object -First 1)
  $flags = @(Get-Content (Join-Path $Pack 'build_SUMMARY_pc1.txt') | Where-Object { $_ -like 'flags*' -or $_ -like 'training*' })
  $csvMd5 = ''; if (Test-Path (Join-Path $abbaDir 'runs.csv')) { $csvMd5 = Get-OspdMd5 (Join-Path $abbaDir 'runs.csv') }
  $md = @(
    "# Speed candidate $Name",
    '',
    "- State: $bxState; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.",
    "- Exe: ``$exe`` md5 ``$md5`` sha256 ``$sha`` ($repro)",
    "- Source: ``$SrcDir``$(if ($Define.Count) { " with defaults flipped in ``$buildSrc``: $($Define -join ', ')" }); $patchTxt; $headTxt (the candidate file itself is added in a later commit)",
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
  $candFile = Join-Path $RepoDir ("candidates\{0}.md" -f $Name)
  if (Test-Path -LiteralPath $candFile) { $candFile = Join-Path $RepoDir ("candidates\{0}_{1}.md" -f $Name, (New-OspdRunId)) }   # new file per run
  Write-OspdLf $candFile $md
  Say "pack written: $Pack ; candidate file $candFile"
  if ($bxRc -eq 3) { exit 3 }
  if ($bxRc -ne 0) { exit 1 }
  exit 0
} catch {
  Write-Output "ERROR: $($_.Exception.Message)"
  try { Add-OspdLf (Join-Path $Pack 'pack.log') "ERROR: $($_.Exception.Message)" } catch {}
  exit 1
}
