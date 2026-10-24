# Original Forge native-Windows qualification protocol. No matches or Elo claims.
# Requires PowerShell 7 on Windows. Linux -DryRun only checks synthetic fixtures.
[CmdletBinding()]
param(
    [ValidateRange(0,63)][int]$Cpu = 6,
    [Parameter(Mandatory=$true)][string[]]$Exes,
    [ValidateSet(11,13,16,20,22)][int]$Depth = 16,
    [string[]]$Labels = @(),
    [string[]]$OracleExes = @(),
    [string]$Out = 'D:\grok-pc-data\forge_push\speed_window',
    [ValidateSet(10000)][int]$OracleChunk = 10000,
    [ValidateRange(1,3600)][int]$TimeoutSeconds = 900,
    [string[]]$OffOptions = @('NnueInt16','SingTtPv','RefutLmr'),
    [hashtable]$OptionProfiles = @{},
    [switch]$Profile,
    [string[]]$ProfileExes = @(),
    [ValidateRange(1,1000000)][int]$ProfileIterations = 10000,
    [switch]$DryRun
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Culture = [Globalization.CultureInfo]::InvariantCulture
$LockNodes = @{11=[int64]308972;13=[int64]745494;16=[int64]2460422;20=[int64]11901452;22=[int64]31111774}
$AARounds = 6
$ABBARounds = 14
$OraclePositions = 1000000
$Owned = [Collections.Generic.List[Diagnostics.Process]]::new()
$RunNumber = 0
$script:FailureStatus = 'ERROR'
$script:BitExact = 'NOT_RUN'
$script:ProfileStatus = 'NOT_REQUESTED'
$script:Rows = [Collections.Generic.List[object]]::new()
$script:Summary = [Collections.Generic.List[object]]::new()

function Log([string]$Message) {
    $line = '{0} | {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Add-Content -LiteralPath $script:LogPath -Value $line -Encoding utf8
    Write-Host $Message
}
function Status([string]$Value) { Set-Content -LiteralPath $script:StatusPath -Value $Value -Encoding utf8 }
function Fail([string]$Code, [string]$Message) {
    $script:FailureStatus = $Code
    throw "$Code $Message"
}
function Number([double]$Value) { return $Value.ToString('F6',$Culture) }
function Median([double[]]$Values) {
    $sorted = @($Values | Sort-Object)
    if ($sorted.Count -eq 0) { throw 'empty median' }
    $mid = [int][Math]::Floor($sorted.Count / 2)
    if ($sorted.Count % 2) { return [double]$sorted[$mid] }
    return ([double]$sorted[$mid-1] + [double]$sorted[$mid]) / 2.0
}
function Verdict([double[]]$Values, [double]$Band) {
    if ($Values.Count -ne 14) { throw 'verdict requires exactly 14 actual ABBA pairs' }
    $faster = @($Values | Where-Object { $_ -gt 0 }).Count
    $slower = @($Values | Where-Object { $_ -lt 0 }).Count
    $median = Median $Values
    if ($faster -ge 12 -and $median -gt $Band) { return 'FASTER' }
    if ($slower -ge 12) { return 'SLOWER' }
    return 'NOISE'
}
function Persist {
    if ($script:Rows.Count) { $script:Rows | Export-Csv -LiteralPath $script:CsvPath -NoTypeInformation -Encoding utf8 }
    if ($script:Summary.Count) { $script:Summary | Export-Csv -LiteralPath $script:SummaryPath -NoTypeInformation -Encoding utf8 }
}
function ResolveExe([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { Fail 'BADINPUT' "executable missing: $Path" }
    return (Resolve-Path -LiteralPath $Path).Path
}
function Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function StartOwned([string]$Exe, [string[]]$Arguments) {
    $psi = [Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $Exe
    foreach ($argument in $Arguments) { [void]$psi.ArgumentList.Add($argument) }
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = [Diagnostics.Process]::new()
    $p.StartInfo = $psi
    if (-not $p.Start()) { Fail 'PROCESS' "start failed: $Exe" }
    $script:Owned.Add($p)
    try {
        # Engines await stdin; oracle/profile producers must await --wait-start.
        # Therefore measured work starts only after affinity and priority are set.
        $p.ProcessorAffinity = [IntPtr]([int64]1 -shl $Cpu)
        if (-not $DryRun) {
            $p.PriorityClass = [Diagnostics.ProcessPriorityClass]::Normal
            if ($p.PriorityClass -ne [Diagnostics.ProcessPriorityClass]::Normal) { throw 'Normal priority did not stick' }
        }
        if ($p.ProcessorAffinity.ToInt64() -ne ([int64]1 -shl $Cpu)) { throw 'affinity did not stick' }
    } catch {
        Fail 'PINFAIL' "cannot pin owned PID $($p.Id) to CPU $Cpu at Normal priority: $_"
    }
    return $p
}
function WaitOwned([Diagnostics.Process]$Process, [string]$Tag) {
    if (-not $Process.WaitForExit($TimeoutSeconds * 1000)) {
        # Only this script's own child may be stopped. No process-name/global kill.
        try { $Process.Kill(); $Process.WaitForExit() } catch { }
        Fail 'TIMEOUT' "$Tag exceeded ${TimeoutSeconds}s (only owned PID $($Process.Id) was stopped)"
    }
    if ($Process.ExitCode -ne 0) { Fail 'BADEXIT' "$Tag exit $($Process.ExitCode)" }
}
function RunText([string]$Exe, [string[]]$Arguments, [string[]]$InputLines, [string]$Tag) {
    $script:RunNumber++
    $stem = Join-Path $script:RawDir ('{0:D4}-{1}' -f $script:RunNumber, $Tag)
    $p = StartOwned $Exe $Arguments
    $stdout = $p.StandardOutput.ReadToEndAsync()
    $stderr = $p.StandardError.ReadToEndAsync()
    $exitProblem = $null
    try {
        foreach ($line in $InputLines) { $p.StandardInput.WriteLine($line) }
        $p.StandardInput.Close()
        WaitOwned $p $Tag
    } catch {
        $exitProblem = $_
        try { if (-not $p.HasExited) { $p.Kill(); $p.WaitForExit() } } catch { }
    }
    $output = $stdout.GetAwaiter().GetResult()
    $errorText = $stderr.GetAwaiter().GetResult()
    [IO.File]::WriteAllText("$stem.stdout.txt", $output)
    [IO.File]::WriteAllText("$stem.stderr.txt", $errorText)
    [IO.File]::WriteAllLines("$stem.stdin.txt", $InputLines)
    if ($null -ne $exitProblem) { throw $exitProblem }
    return $output
}
function RunBench([int]$Index, [int]$BenchDepth, [string]$Tag, [hashtable]$Options = @{}, [hashtable]$ExpectedNodes = @{}) {
    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add('uci')
    $lines.Add('setoption name Threads value 1')
    $lines.Add('setoption name Hash value 16')
    $lines.Add('setoption name OwnBook value false')
    foreach ($option in $OffOptions) { $lines.Add("setoption name $option value false") }
    foreach ($option in @($Options.Keys | Sort-Object)) {
        $value = if ($Options[$option] -is [bool]) { $Options[$option].ToString().ToLowerInvariant() } else { [string]$Options[$option] }
        $lines.Add("setoption name $option value $value")
    }
    $lines.Add('isready')
    $lines.Add("bench $BenchDepth")
    $lines.Add('quit')
    $output = RunText $Exes[$Index] @() $lines.ToArray() $Tag
    foreach ($option in $Options.Keys) {
        $pattern = '(?m)^option name ' + [regex]::Escape($option) + ' type check default false\r?$'
        if ($output -notmatch $pattern) { Fail 'BADOPTION' "$($Labels[$Index]) does not advertise OFF-default UCI option $option; ON profile not accepted" }
    }
    $matches = [regex]::Matches($output, '(?m)^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)\r?$')
    if ($matches.Count -ne 1) { Fail 'BADBENCH' "$($Labels[$Index]) expected one bench line, got $($matches.Count); raw=$Tag" }
    $match = $matches[0]
    $nodes = [int64]$match.Groups[2].Value
    $expected = if ($ExpectedNodes.ContainsKey($BenchDepth)) { [int64]$ExpectedNodes[$BenchDepth] } else { $LockNodes[$BenchDepth] }
    if ([int]$match.Groups[1].Value -ne $BenchDepth -or $nodes -ne $expected) {
        Fail 'BADNODES' "$($Labels[$Index]) depth $BenchDepth nodes $nodes expected $expected; no later test/timing"
    }
    $nps = [double]$match.Groups[4].Value
    if ($nps -le 0) { Fail 'BADBENCH' "$($Labels[$Index]) nonpositive NPS; raw=$Tag" }
    return [pscustomobject]@{Nodes=$nodes;Nps=$nps;TimeMs=[int64]$match.Groups[3].Value}
}
function RunOracle([int]$Index, [int]$Seed, [int]$Count, [string]$Tag) {
    $path = Join-Path $script:RawDir "$Tag.bin"
    $errPath = Join-Path $script:RawDir "$Tag.stderr.txt"
    # Interface: stdout raw deterministic bytes; count/seed appear in header;
    # exit 0 + a JSON coverage line on stderr. Producers await stdin 'start'.
    $p = StartOwned $OracleExes[$Index] @('--seed',"$Seed",'--positions',"$Count",'--wait-start')
    $file = [IO.File]::Create($path)
    $pump = $p.StandardOutput.BaseStream.CopyToAsync($file)
    $stderr = $p.StandardError.ReadToEndAsync()
    try {
        $exitProblem = $null
        try {
            $p.StandardInput.WriteLine('start')
            $p.StandardInput.Close()
            WaitOwned $p $Tag
        } catch {
            $exitProblem = $_
            try { if (-not $p.HasExited) { $p.Kill(); $p.WaitForExit() } } catch { }
        }
        $pump.GetAwaiter().GetResult()
        $err = $stderr.GetAwaiter().GetResult()
        [IO.File]::WriteAllText($errPath,$err)
        if ($null -ne $exitProblem) { throw $exitProblem }
    } finally { $file.Dispose() }
    $expectedBytes = [int64]4216 * $Count + 320
    if ((Get-Item -LiteralPath $path).Length -ne $expectedBytes) { Fail 'ORACLE_FAIL' "oracle $Tag byte count must be $expectedBytes for H256 count=$Count" }
    $jsonLines = @($err -split '\r?\n' | Where-Object { $_.StartsWith('{') })
    if ($jsonLines.Count -ne 1) { Fail 'ORACLE_FAIL' "expected exactly one coverage JSON line from $Tag" }
    try { $coverage = $jsonLines[0] | ConvertFrom-Json } catch { Fail 'ORACLE_FAIL' "invalid coverage JSON from $Tag" }
    foreach ($name in @('kind','positions','records','seed','refresh','updates','parent_checks','inplace_checks','games','starts','moves','captures','en_passant','castles','quiet_promotions','capture_promotions','genuine_boards')) {
        if (-not ($coverage.PSObject.Properties.Name -contains $name)) { Fail 'ORACLE_FAIL' "coverage missing $name from $Tag" }
    }
    if ($coverage.kind -ne 'nnue_million_oracle' -or $coverage.records -ne $Count -or $coverage.positions -ne $Count -or [string]$coverage.seed -ne [string]$Seed -or $coverage.refresh -ne $Count -or ($coverage.updates+$coverage.starts) -ne $Count -or $coverage.parent_checks -ne $coverage.updates -or $coverage.inplace_checks -ne $coverage.updates -or $coverage.genuine_boards -ne $true) {
        Fail 'ORACLE_FAIL' "coverage counts/seed mismatch from $Tag"
    }
    return [pscustomobject]@{Path=$path;Hash=(Hash $path);Bytes=(Get-Item -LiteralPath $path).Length;Coverage=($coverage | ConvertTo-Json -Depth 10 -Compress)}
}
function RunPair([int]$Candidate, [int]$Round, [string]$Kind) {
    $results = @()
    # A B B A: two symmetric repeats constitute ONE actual pair, never two.
    foreach ($index in @(0,$Candidate,$Candidate,0)) {
        $tag = '{0}-{1:D2}-{2}' -f $Kind,$Round,$results.Count
        if ($Kind -eq 'ABBA' -and $OptionProfiles.ContainsKey($Labels[$index])) {
            $p = $OptionProfiles[$Labels[$index]]
            $results += RunBench $index $Depth $tag $p.Options $p.ExpectedNodes
        } else { $results += RunBench $index $Depth $tag }
    }
    $a = ($results[0].Nps + $results[3].Nps) / 2.0
    $b = ($results[1].Nps + $results[2].Nps) / 2.0
    $gain = 100.0 * ($b / $a - 1.0)
    $script:Rows.Add([pscustomobject]@{
        kind=$Kind;candidate=$Labels[$Candidate];exe_sha256=$script:Hashes[$Candidate];pair=$Round;
        A1_nps=(Number $results[0].Nps);B1_nps=(Number $results[1].Nps);B2_nps=(Number $results[2].Nps);A2_nps=(Number $results[3].Nps);
        nodes_ok=$true;A_nodes=$results[0].Nodes;B_nodes=$results[1].Nodes;gain_pct=(Number $gain);depth=$Depth;cpu=$Cpu;threads=1;hash_mib=16;ownbook=$false;oracle_gate=$script:BitExact;option_profile=$OptionProfiles.ContainsKey($Labels[$Candidate]);dry_run=[bool]$DryRun
    })
    Persist
    $denominator = if ($Kind -eq 'AA') { 6 } else { 14 }
    Log ("PAIR {0} {1} {2}/{3} gain_pct={4} nodes_ok=True" -f $Kind,$Labels[$Candidate],$Round,$denominator,(Number $gain))
    return $gain
}

try {
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 required (ProcessStartInfo.ArgumentList + binary async drains)' }
    if (-not $IsWindows -and -not $DryRun) { throw 'Native Windows required. Linux is permitted only with -DryRun and synthetic fixtures.' }
    if ($Exes.Count -lt 4) { throw 'Exes order must be OFF-lock, AVX512-stage1, AVX512-stage2, AVX512-stage3, then optional research builds' }
    if (-not $Labels.Count) {
        $Labels = @('lock','stage1','stage2','stage3')
        for ($i=4;$i -lt $Exes.Count;$i++) { $Labels += "optional$i" }
    }
    if ($Labels.Count -ne $Exes.Count -or @($Labels | Sort-Object -Unique).Count -ne $Labels.Count) { throw 'Labels must be unique and match Exes count' }
    if ($Labels[0] -ne 'lock' -or $Labels[1] -ne 'stage1' -or $Labels[2] -ne 'stage2' -or $Labels[3] -ne 'stage3') { throw 'First four Labels must be lock,stage1,stage2,stage3 in that order' }
    foreach ($label in $OptionProfiles.Keys) {
        if ($Labels -notcontains $label -or @('lock','stage1','stage2','stage3') -contains $label) { throw 'OptionProfiles are permitted only for explicitly supplied optional research builds' }
        $p = $OptionProfiles[$label]
        if ($p -isnot [hashtable] -or -not $p.ContainsKey('Options') -or -not $p.ContainsKey('ExpectedNodes') -or $p.Options -isnot [hashtable] -or $p.ExpectedNodes -isnot [hashtable]) { throw 'OptionProfiles entry requires Options and ExpectedNodes hashtables' }
        if ($p.Options.Count -ne 1 -or -not $p.Options.ContainsKey('NnueInt16') -or $p.Options.NnueInt16 -isnot [bool] -or $p.Options.NnueInt16 -ne $true) { throw 'Only explicit NnueInt16=true research profiles are supported' }
        foreach ($d in @(13,16,$Depth)) { if (-not $p.ExpectedNodes.ContainsKey($d) -or [int64]$p.ExpectedNodes[$d] -le 0) { throw "Frozen int16 expected nodes required at depth $d" } }
    }
    if ($OracleExes.Count -ne 2) { throw 'OracleExes must be two producers in OFF-lock, AVX512-stage3 order' }
    if ($Profile -and $ProfileExes.Count -ne 2) { throw '-Profile requires two ProfileExes in OFF-lock, AVX512-stage3 order' }
    if ($Profile -and $DryRun) { throw '-Profile cannot report synthetic timings; use native Windows' }
    if (Test-Path -LiteralPath $Out) {
        if (@(Get-ChildItem -LiteralPath $Out -Force).Count) { throw 'Out must be new or empty; refusing to replace prior evidence' }
    } else { [void](New-Item -ItemType Directory -Path $Out) }
    $script:RawDir = Join-Path $Out 'raw'
    [void](New-Item -ItemType Directory -Path $script:RawDir)
    $script:LogPath = Join-Path $Out 'zen5_qualify_sol.log'
    $script:StatusPath = Join-Path $Out 'zen5_qualify_sol.STATUS'
    $script:CsvPath = Join-Path $Out 'zen5_qualify_sol.csv'
    $script:SummaryPath = Join-Path $Out 'zen5_qualify_sol_summary.csv'
    Status 'RUNNING_IDENTITY'
    Log "MODE $(if($DryRun){'DRY_RUN_SYNTHETIC_NO_SPEED_CLAIM'}else{'NATIVE_WINDOWS'}) CPU=$Cpu priority=Normal Threads=1 Hash=16 OwnBook=false depth=$Depth"
    Log "PROTOCOL AA=6 palindrome A A A A; ABBA=14 actual pairs/candidate; band=max(abs(all six AA gains)); faster>=12 and median>band; slower>=12 else NOISE"
    $script:Hashes = @()
    # Identity of every executable is printed before the first engine runs.
    for ($i=0;$i -lt $Exes.Count;$i++) {
        $Exes[$i] = ResolveExe $Exes[$i]
        $script:Hashes += Hash $Exes[$i]
        Log "IDENTITY $($Labels[$i]) sha256=$($script:Hashes[$i]) exe=$($Exes[$i])"
    }
    for ($i=0;$i -lt 2;$i++) {
        $OracleExes[$i] = ResolveExe $OracleExes[$i]
        Log "ORACLE_IDENTITY $(if($i -eq 0){'OFF'}else{'AVX512_stage3'}) sha256=$(Hash $OracleExes[$i]) exe=$($OracleExes[$i])"
    }
    $oracleHashes = @($OracleExes | ForEach-Object { Hash $_ })
    $profileHashes = @()
    if ($Profile) {
        for ($i=0;$i -lt 2;$i++) {
            $ProfileExes[$i] = ResolveExe $ProfileExes[$i]
            $profileHashes += Hash $ProfileExes[$i]
            Log "PROFILE_IDENTITY index=$i sha256=$($profileHashes[$i]) exe=$($ProfileExes[$i])"
        }
    }
    # Convert numeric depth keys explicitly: ConvertTo-Json rejects hashtables
    # with integer keys even though those keys are required for node lookup.
    $serialProfiles = [ordered]@{}
    foreach ($label in @($OptionProfiles.Keys | Sort-Object)) {
        $nodeMap = [ordered]@{}
        foreach ($d in @($OptionProfiles[$label].ExpectedNodes.Keys | Sort-Object)) { $nodeMap[[string]$d] = [int64]$OptionProfiles[$label].ExpectedNodes[$d] }
        $serialProfiles[[string]$label] = [ordered]@{options=$OptionProfiles[$label].Options;expected_nodes=$nodeMap}
    }
    $manifest = [ordered]@{cpu=$Cpu;depth=$Depth;threads=1;hash_mib=16;ownbook=$false;exes=$Exes;labels=$Labels;exe_sha256=$script:Hashes;off_options=$OffOptions;option_profiles=$serialProfiles;oracle_exes=$OracleExes;oracle_exe_sha256=$oracleHashes;oracle_seeds='1..100';oracle_positions_per_seed=10000;profile_exes=$ProfileExes;profile_exe_sha256=$profileHashes;profile_iterations=$ProfileIterations;aa_blocks=6;abba_blocks_per_candidate=14;dry_run=[bool]$DryRun}
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $Out 'frozen_protocol.json') -Encoding utf8
    Log "FROZEN_PROTOCOL sha256=$(Hash (Join-Path $Out 'frozen_protocol.json'))"
    # Crucial: d11 is each build's FIRST engine test; no other depth runs if it fails.
    for ($i=0;$i -lt $Exes.Count;$i++) {
        foreach ($d in @(11,13,16,20,22)) {
            $bench = RunBench $i $d "identity-$($Labels[$i])-d$d"
            Log "NODES PASS $($Labels[$i]) depth=$d nodes=$($bench.Nodes) all_experimental_options=OFF"
        }
    }
    foreach ($label in @($OptionProfiles.Keys | Sort-Object)) {
        $index = [array]::IndexOf($Labels,$label)
        $p = $OptionProfiles[$label]
        foreach ($d in (@(13,16,$Depth) | Sort-Object -Unique)) {
            $bench = RunBench $index $d "research-$label-d$d" $p.Options $p.ExpectedNodes
            Log "RESEARCH_ON_NODES PASS $label depth=$d nodes=$($bench.Nodes) NnueInt16=true NON_BIT_EXACT expected_map_frozen_before_measurement=True"
        }
    }
    Status 'RUNNING_ORACLE'
    $oracleRows = [Collections.Generic.List[object]]::new()
    $hashChain = [Collections.Generic.List[string]]::new()
    $positionsChecked = 0
    for ($start=0;$start -lt $OraclePositions;$start += $OracleChunk) {
        $count = [Math]::Min($OracleChunk,$OraclePositions-$start)
        # Alternate OFF/ON and ON/OFF chunk order on the identical pinned CPU.
        $chunk = [int]($start / $OracleChunk)
        $order = if ($chunk % 2 -eq 0) { @(0,1) } else { @(1,0) }
        $r = @{}
        $seed = $chunk+1
        foreach ($index in $order) { $r[$index] = RunOracle $index $seed $count "oracle-$start-$index" }
        if ($r[0].Hash -ne $r[1].Hash -or $r[0].Bytes -ne $r[1].Bytes -or $r[0].Coverage -cne $r[1].Coverage) {
            $script:BitExact = 'FAIL'
            Fail 'ORACLE_FAIL' "start=$start count=$count OFF=$($r[0].Hash) AVX512=$($r[1].Hash); failed raw pair retained; nps not reported"
        }
        $oracleRows.Add([pscustomobject]@{chunk=$chunk;seed=$seed;positions=$count;order=($order -join ',');cpu=$Cpu;off_sha256=$r[0].Hash;avx512_sha256=$r[1].Hash;bytes=$r[0].Bytes;coverage=$r[0].Coverage;result='PASS'})
        $positionsChecked += $count
        $hashChain.Add("$chunk,$seed,$count,$($r[0].Hash),$($r[0].Bytes)`n")
        $oracleRows | Export-Csv -LiteralPath (Join-Path $Out 'oracle_chunks.csv') -NoTypeInformation -Encoding utf8
        Log "ORACLE CHUNK PASS start=$start positions=$count sha256=$($r[0].Hash) bytes=$($r[0].Bytes)"
        Remove-Item -LiteralPath $r[0].Path,$r[1].Path
    }
    if ($positionsChecked -ne 1000000 -or $oracleRows.Count -ne 100) { Fail 'ORACLE_FAIL' 'expected 100 chunks and exactly 1000000 records per producer' }
    $hashChainPath = Join-Path $Out 'oracle_hashchain.txt'
    [IO.File]::WriteAllText($hashChainPath,($hashChain -join ''),[Text.UTF8Encoding]::new($false))
    $script:BitExact = 'PASS'
    Log "BIT_EXACT PASS positions=$positionsChecked chunks=100 seeds=1..100 OFF_vs_AVX512_stage3 same_cpu=$Cpu hashchain_sha256=$(Hash $hashChainPath) (hashchain is not raw-concatenation SHA256)"
    for ($i=0;$i -lt $Exes.Count;$i++) { if ((Hash $Exes[$i]) -ne $script:Hashes[$i]) { Fail 'IDENTITY_CHANGED' "engine changed since identity: $($Labels[$i])" } }
    for ($i=0;$i -lt 2;$i++) { if ((Hash $OracleExes[$i]) -ne $oracleHashes[$i]) { Fail 'IDENTITY_CHANGED' "oracle changed since identity: $i" } }
    Status 'RUNNING_AA'
    $aa = @()
    for ($round=1;$round -le $AARounds;$round++) { $aa += RunPair 0 $round 'AA' }
    $band = [double](($aa | ForEach-Object { [Math]::Abs($_) } | Measure-Object -Maximum).Maximum)
    Log "AA PASS pairs=6 band_pct=$(Number $band) rule=max_absolute_of_all_six median_pct=$(Number (Median $aa))"
    Status 'RUNNING_ABBA'
    # Include lock-vs-lock as the first 14-pair control, then every candidate.
    for ($i=0;$i -lt $Exes.Count;$i++) {
        $gains = @()
        for ($round=1;$round -le $ABBARounds;$round++) { $gains += RunPair $i $round 'ABBA' }
        $median = Median $gains
        $mean = [double](($gains | Measure-Object -Average).Average)
        $faster = @($gains | Where-Object { $_ -gt 0 }).Count
        $slower = @($gains | Where-Object { $_ -lt 0 }).Count
        $verdict = if ($DryRun) { 'DRY_RUN_ONLY' } else { Verdict $gains $band }
        $bitScope = if ($i -eq 0 -or $i -eq 3) { 'PASS_OFF_VS_STAGE3' } else { 'NOT_CHECKED_THIS_RUN' }
        if ($OptionProfiles.ContainsKey($Labels[$i])) { $bitScope = 'NOT_APPLICABLE_QUANTIZED_RESEARCH' }
        $interpretation = if ($i -eq 2 -and $verdict -ne 'FASTER') { 'POSSIBLE_REGRESSION' } elseif ($i -eq 3) { 'EXPLICIT_AVX512_ON_VS_OFF' } else { '' }
        $optionDescription = if ($OptionProfiles.ContainsKey($Labels[$i])) { $OptionProfiles[$Labels[$i]].Options | ConvertTo-Json -Compress } else { 'ALL_EXPERIMENTAL_OFF' }
        $expectedNodeCount = if ($OptionProfiles.ContainsKey($Labels[$i])) { $OptionProfiles[$Labels[$i]].ExpectedNodes[$Depth] } else { $LockNodes[$Depth] }
        $script:Summary.Add([pscustomobject]@{candidate=$Labels[$i];exe_sha256=$script:Hashes[$i];nodes_ok=$true;expected_nodes_at_depth=$expectedNodeCount;option_profile=$optionDescription;per_pair_pct=($gains.ForEach({Number $_}) -join ';');median_pct=(Number $median);mean_pct=(Number $mean);faster=$faster;slower=$slower;pairs=14;aa_band_pct=(Number $band);verdict=$verdict;bit_exact=$bitScope;oracle_gate=$script:BitExact;profile=$script:ProfileStatus;phase_split='NOT_MEASURED';interpretation=$interpretation;dry_run=[bool]$DryRun})
        Persist
        Log "SUMMARY $($Labels[$i]) sha256=$($script:Hashes[$i]) nodes_ok=True median_pct=$(Number $median) mean_pct=$(Number $mean) faster=$faster/14 slower=$slower/14 AA_band_pct=$(Number $band) verdict=$verdict bit_exact=$bitScope oracle_gate=PASS $interpretation"
    }
    if ($Profile) {
        Status 'RUNNING_PROFILE'
        # Explicit native probe contract; no inferred percent from NPS. Each
        # emits one JSON record after --iterations N --wait-start. These probes
        # measure API kernels only; whole-engine phase percentages are unknown.
        $script:ProfileStatus = 'RUNNING'
        for ($i=0;$i -lt 2;$i++) {
            if ((Hash $ProfileExes[$i]) -ne $profileHashes[$i]) { Fail 'IDENTITY_CHANGED' "profile executable changed since identity: $i" }
            $output = RunText $ProfileExes[$i] @('--iterations',"$ProfileIterations",'--wait-start') @('start') "profile-$i"
            $record = $output | ConvertFrom-Json
            foreach ($name in @('kind','iterations','hidden_size','api_phase_only','refresh_ns_per_call','update_ns_per_call','evaluate_ns_per_call','checksum')) {
                if (-not ($record.PSObject.Properties.Name -contains $name)) { Fail 'PROFILE_FAIL' "missing $name from profile-$i" }
            }
            if ($record.kind -ne 'nnue_phase_benchmark' -or $record.iterations -ne $ProfileIterations -or $record.hidden_size -ne 256 -or $record.api_phase_only -ne $true) { Fail 'PROFILE_FAIL' 'unexpected profile identity/count' }
            foreach ($name in @('refresh_ns_per_call','update_ns_per_call','evaluate_ns_per_call')) {
                $value=[double]$record.$name
                if (-not [double]::IsFinite($value) -or $value -lt 0) { Fail 'PROFILE_FAIL' "invalid $name from profile-$i" }
            }
            $split = 'NOT_MEASURED'
            Log "PHASE_SPLIT $(if($i -eq 0){'OFF'}else{'AVX512_stage3'}) $split refresh_ns_per_call=$($record.refresh_ns_per_call) update_ns_per_call=$($record.update_ns_per_call) evaluate_ns_per_call=$($record.evaluate_ns_per_call)"
            $summaryIndex = if ($i -eq 0) { 0 } else { 3 }
            $script:Summary[$summaryIndex].phase_split = $split
            $script:Summary[$summaryIndex].profile = 'PASS'
        }
        $script:ProfileStatus = 'PASS'
        Persist
    } else { Log 'PHASE_SPLIT NOT_MEASURED optional -Profile native instrumented probes were not requested' }
    Status $(if($DryRun){'DRY_RUN_DONE_NO_SPEED_CLAIM'}else{'DONE'})
    Log "SUMMARY END bit_exact=$script:BitExact phase_split=$script:ProfileStatus CSV=$script:CsvPath summary_csv=$script:SummaryPath matches=0 Elo=UNPROVEN"
    exit 0
} catch {
    if (Get-Variable StatusPath -Scope Script -ErrorAction SilentlyContinue) { Status $script:FailureStatus }
    if (Get-Variable LogPath -Scope Script -ErrorAction SilentlyContinue) { Log "STOP $($_.Exception.Message)" } else { Write-Error $_ }
    Persist
    exit 1
} finally {
    foreach ($p in $Owned) {
        try { if (-not $p.HasExited) { $p.Kill(); $p.WaitForExit() } } catch { }
        $p.Dispose()
    }
}
