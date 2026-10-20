# Register-DesksOnLogon.ps1 — ログオンしたら WS の机 (tmux -L win) が立つようにする。
# Notion「Windows PC（WS）の手順書」節 2 の最後。本社から desks-startup.sh を写し終えてから打つ。
# 使い方 (管理者でなくてよい):  .\Register-DesksOnLogon.ps1 -LinuxUser <Ubuntu の利用者名>
param([Parameter(Mandatory=$true)][string]$LinuxUser)
$script = "/home/$LinuxUser/ai/bin/desks-startup.sh"
$exists = (wsl.exe -d Ubuntu -- test -x $script; $LASTEXITCODE -eq 0)
if (-not $exists) { Write-Host "未確認: $script が無い。先に本社から写す" -ForegroundColor Yellow; exit 1 }
schtasks /Create /F /TN "WS-desks" /SC ONLOGON /RL LIMITED /TR "wsl.exe -d Ubuntu -- $script"
if ($LASTEXITCODE -eq 0) { Write-Host "登録した: WS-desks (ログオン時に $script)" } else { Write-Host "未確認: 登録失敗。タスク スケジューラで手で入れる" -ForegroundColor Yellow }
