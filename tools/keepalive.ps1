# keepalive.ps1 - ONE check cycle (Task Scheduler runs it at logon and every 5 minutes).
# For every job in jobs.json that is not finished and not running -> relaunch it (sweeps are resumable).
#   PAUSE   : create the file tools\STOP  (delete it to resume)
#   FINISHED: tools\done\<name>.done      (delete it to run that job again)
$root = 'D:\RoboSketch-RL'
$log  = "$root\tools\keepalive.log"
if (Test-Path "$root\tools\STOP") { exit 0 }

$jobs = Get-Content "$root\tools\jobs.json" -Raw | ConvertFrom-Json
$procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'"

foreach ($j in $jobs) {
    if (Test-Path "$root\tools\done\$($j.name).done") { continue }
    if ($procs | Where-Object { $_.CommandLine -like "*$($j.script_args)*" }) { continue }   # already running

    $f = "$root\tools\fails\$($j.name).count"
    if ((Test-Path $f) -and ([int](Get-Content $f) -ge 20)) {
        "$(Get-Date -Format s) GIVEUP $($j.name) (20 failed launches - look at it by hand)" | Add-Content $log
        continue
    }
    "$(Get-Date -Format s) RELAUNCH $($j.name)" | Add-Content $log
    Start-Process powershell -WindowStyle Hidden -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "$root\tools\run_job.ps1",
        '-Name', $j.name, '-ScriptArgs', "`"$($j.script_args)`"")
}
