# Register-DesksOnLogon.ps1 — ログオンしたら WS の机 (tmux -L win) が立つようにする。
# Notion「Windows PC（WS）の手順書」節 2 の最後。本社から desks-startup.sh を写し終えてから打つ。
# 使い方 (管理者でなくてよい):  .\Register-DesksOnLogon.ps1 -LinuxUser <Ubuntu の利用者名>
param([Parameter(Mandatory=$true)][string]$LinuxUser)
$script = "/home/$LinuxUser/ai/bin/desks-startup.sh"
wsl.exe -d Ubuntu -- test -x $script
$exists = ($LASTEXITCODE -eq 0)
if (-not $exists) { Write-Host "未確認: $script が無い。先に本社から写す" -ForegroundColor Yellow; exit 1 }
# ノート PC は電池でも起動・継続・時間の上限なし (schtasks の既定は「電池では起動しない」)。
$u = "$env:USERDOMAIN\$env:USERNAME"
$set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
$pr = New-ScheduledTaskPrincipal -UserId $u -LogonType Interactive -RunLevel Limited
# 1) ログオン時に 58 窓を作る (作るだけ・画面は開かない)。
try {
  $tr = New-ScheduledTaskTrigger -AtLogOn -User $u
  $ac = New-ScheduledTaskAction -Execute "wsl.exe" -Argument "-d Ubuntu -- $script"
  Register-ScheduledTask -Force -TaskName "WS-desks" -Trigger $tr -Action $ac -Settings $set -Principal $pr -ErrorAction Stop | Out-Null
  Write-Host "登録した: WS-desks (ログオン時に $script・電池でも)"
} catch { Write-Host "未確認: WS-desks の登録失敗。タスク スケジューラで手で入れる" -ForegroundColor Yellow }
# 2) ログオンの 60 秒後に「WS 机」のタブを開く。既定のタブ (PowerShell) は変えない。
#    studio.sh は作り終えるまで待ってから attach する (空の win は作らない)。
try {
  $wt = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\wt.exe'
  $tr2 = New-ScheduledTaskTrigger -AtLogOn -User $u; $tr2.Delay = 'PT60S'
  $ac2 = New-ScheduledTaskAction -Execute $wt -Argument "-p {4ce7dd61-f5b5-5a52-9a9b-a2b8801eb0b6}"
  Register-ScheduledTask -Force -TaskName "WS-terminal" -Trigger $tr2 -Action $ac2 -Settings $set -Principal $pr -ErrorAction Stop | Out-Null
  Write-Host "登録した: WS-terminal (ログオン 60 秒後に WS 机のタブ)"
} catch { Write-Host "未確認: WS-terminal の登録失敗。タスク スケジューラで手で入れる" -ForegroundColor Yellow }
