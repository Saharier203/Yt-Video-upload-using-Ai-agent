$Action = New-ScheduledTaskAction -Execute "E:\ai-horror-channel\run_daily.bat" -WorkingDirectory "E:\ai-horror-channel"
$TriggerDaily = New-ScheduledTaskTrigger -Daily -At 17:55
$TriggerWeekly = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 12:55
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -RunOnlyIfNetworkAvailable
$Principal = New-ScheduledTaskPrincipal -UserId (Get-CimInstance Win32_ComputerSystem).UserName -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName "AIHorrorChannel_Daily" -Action $Action -Trigger $TriggerDaily -Settings $Settings -Principal $Principal -Force
Register-ScheduledTask -TaskName "AIHorrorChannel_Weekly" -Action $Action -Trigger $TriggerWeekly -Settings $Settings -Principal $Principal -Force

Write-Host "Tasks registered. Daily at 5:55 PM (posts at 6:00 PM), Weekly Sunday 12:55 PM." -ForegroundColor Green