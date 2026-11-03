# Adversarial copies only: originals and completed packs are never edited.
$ErrorActionPreference='Stop'
$fixture='D:/a13/evidence/runs/pack-refusal-fixtures'
if ((Get-PSDrive D).Free -lt (50GB+32MB)) { throw 'allocation refused' }
New-Item -ItemType Directory -Path $fixture -ErrorAction Stop | Out-Null
$qc=Join-Path $fixture 'qc'
$qcRun=Join-Path $fixture 'qc-run'
$suite=Join-Path $fixture 'suite'
New-Item -ItemType Directory -Path $qc,$qcRun,$suite | Out-Null
foreach ($name in @('statistics.json','INPUTS.json','mate_rows.jsonl','COMPLETE.json')) {
    Copy-Item -LiteralPath (Join-Path 'D:/a13/p5qc/runs/qc02' $name) -Destination (Join-Path $qc $name)
}
# Whitespace-only alteration retains parsed values but must break the byte pin.
[IO.File]::AppendAllText((Join-Path $qc 'statistics.json'),' ',[Text.UTF8Encoding]::new($false))
$receipt=Get-Content D:/a13/evidence/runs/qc02/receipt.json -Raw | ConvertFrom-Json
$receipt.arguments[1]=$qc
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $qcRun 'receipt.json') -Encoding utf8
foreach ($name in @('receipt.json','collection.json','test_results.json')) {
    Copy-Item -LiteralPath (Join-Path 'D:/a13/evidence/runs/full-suite06' $name) -Destination (Join-Path $suite $name)
}
$results=Get-Content (Join-Path $suite 'test_results.json') -Raw | ConvertFrom-Json
$removed=$false
$results.results=@($results.results | Where-Object {
    if (-not $removed -and $_.kind -eq 'test') { $removed=$true; $false } else { $true }
})
$results | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $suite 'test_results.json') -Encoding utf8
$cases=@(
    @{name='pack-refuse-bytes';suite='D:/a13/evidence/runs/full-suite06';qc=$qc;qcRun=$qcRun;reason='SHA256 mismatch'},
    @{name='pack-refuse-omission';suite=$suite;qc='D:/a13/p5qc/runs/qc02';qcRun='D:/a13/evidence/runs/qc02';reason='omitted or duplicated'}
)
foreach ($case in $cases) {
    $output=Join-Path $fixture $case.name
    & D:/a13/tools/Invoke-R13.ps1 -Script D:/a13/tools/pack_scoped.py -ScriptArguments @('--out',$output,'--suite',$case.suite,'--qc',$case.qc,'--qc-run',$case.qcRun,'--threads','1') -RunName $case.name -TimeoutSeconds 120 -RequiredBytes 33554432
    $run=Join-Path D:/a13/evidence/runs $case.name
    $result=Get-Content (Join-Path $run 'receipt.json') -Raw | ConvertFrom-Json
    if ($result.exit_code -eq 0 -or (Test-Path -LiteralPath $output) -or -not (Select-String -LiteralPath (Join-Path $run 'stderr.log') -SimpleMatch $case.reason)) {
        throw 'Expected pre-publication rejection was not observed'
    }
    Write-Output ($case.name+': expected refusal PASS')
}
