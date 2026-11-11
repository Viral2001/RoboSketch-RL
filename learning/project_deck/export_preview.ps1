# Export every slide of a .pptx to PNG through Microsoft PowerPoint (COM), for visual QA.
# Usage: powershell -File export_preview.ps1 <deck.pptx> <outdir> [first] [last]
# Opens the deck READ-ONLY and without a window; quits PowerPoint afterwards only if it
# was not already running (so a deck the user has open is never touched).
param([string]$pptx, [string]$outdir, [int]$first = 1, [int]$last = 0)
New-Item -ItemType Directory -Force $outdir | Out-Null
$outdir = (Resolve-Path $outdir).Path
$wasRunning = [bool](Get-Process POWERPNT -ErrorAction SilentlyContinue)
$pp = New-Object -ComObject PowerPoint.Application
$pres = $null
try {
    $pres = $pp.Presentations.Open((Resolve-Path $pptx).Path, -1, 0, 0)   # ReadOnly, not Untitled, no window
    $n = $pres.Slides.Count
    if ($last -le 0 -or $last -gt $n) { $last = $n }
    for ($i = $first; $i -le $last; $i++) {
        $f = Join-Path $outdir ("slide_{0:D3}.png" -f $i)
        $pres.Slides.Item($i).Export($f, "PNG", 1600, 900)
    }
    Write-Output "exported slides $first..$last of $n to $outdir"
}
finally {
    if ($pres) { $pres.Close() }
    if (-not $wasRunning) { $pp.Quit() }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null
}
