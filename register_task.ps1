# Phase 4 - register the daily Static Index Tracker job with Windows Task Scheduler.
# Run ONCE from an elevated-or-normal PowerShell:   .\register_task.ps1
#
# NOTE: -At is LOCAL time. 6:00PM == 18:00 IST only if this PC's clock is set to India
# Standard Time. If not, change -At below. Runs as the current user when logged on, and
# catches up if the PC was off at 18:00 (StartWhenAvailable).
$ErrorActionPreference = "Stop"
$root = "C:\Claude developement\static-index-tracker"
$bat  = Join-Path $root "run_daily.bat"
if (-not (Test-Path $bat)) { throw "run_daily.bat not found at $bat" }

$action   = New-ScheduledTaskAction -Execute $bat
$trigger  = New-ScheduledTaskTrigger -Daily -At 6:00PM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
              -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "StaticIndexTracker" -Action $action -Trigger $trigger `
    -Settings $settings -Force `
    -Description "Daily NSE/BSE index constituent fetch + diff + site build (~18:00 IST)"

Write-Host "Registered 'StaticIndexTracker' (daily 18:00 local time)."
Write-Host "  Run now:  schtasks /Run /TN StaticIndexTracker"
Write-Host "  Inspect:  schtasks /Query /TN StaticIndexTracker /V /FO LIST"
Write-Host "  Remove:   Unregister-ScheduledTask -TaskName StaticIndexTracker -Confirm:`$false"
