# table_identity.ps1 - sha256 of every table file in D:\syzygy345 (read only), written to fixtures\TABLES.sha256, compared with the project's list if present.
. 'D:\forge_jobs_20261107\opus1\env.ps1'
[Threading.Thread]::CurrentThread.CurrentCulture = [Globalization.CultureInfo]::InvariantCulture
$out = Join-Path $JobRepo 'opus_syzygy_gaps\fixtures\TABLES.sha256'
$lines = New-Object System.Collections.Generic.List[string]
$bytes = [int64]0
foreach ($f in Get-ChildItem -LiteralPath 'D:\syzygy345' -File | Where-Object { $_.Extension -in '.rtbw', '.rtbz' } | Sort-Object Name) {
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $f.FullName).Hash.ToLower()
    $lines.Add("$h  $($f.Name)")
    $bytes += $f.Length
}
[IO.File]::WriteAllLines($out, $lines, (New-Object Text.UTF8Encoding($false)))
Write-Output "files $($lines.Count) bytes $bytes list $out sha256 $((Get-FileHash -Algorithm SHA256 -LiteralPath $out).Hash) $(Get-ViennaNow) $(Get-JobPinLine)"
