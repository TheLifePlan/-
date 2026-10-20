# Install-WS.ps1 — Windows PC (WS) の「ザラの手」のうち、台本で済む分をまとめて行う。
# Notion「Windows PC（WS）の手順書」節 1 の 1〜3 と 6 (スリープ) に相当。ログイン操作 (Tailscale・3 つの AI・自動ログオン) は人の手。
# 管理者の PowerShell で:  Set-ExecutionPolicy -Scope Process Bypass -Force; .\Install-WS.ps1
# 何度実行しても同じ結果になる。
$ErrorActionPreference = 'Continue'
function Step($t) { Write-Host "`n== $t" -ForegroundColor Cyan }

Step "1. WSL2 + Ubuntu"
$wslList = (wsl.exe -l -q 2>$null) -join ' '
if ($wslList -match 'Ubuntu') {
  Write-Host "   既にある: Ubuntu"
} else {
  wsl.exe --install -d Ubuntu
  Write-Host "   再起動を聞かれたら再起動。終わると Ubuntu が開き、Linux の名前とパスワードを聞く。" -ForegroundColor Yellow
}

Step "2. Windows Terminal"
if (Get-Command wt.exe -ErrorAction SilentlyContinue) {
  Write-Host "   既にある"
} else {
  winget install --id Microsoft.WindowsTerminal -e --accept-source-agreements --accept-package-agreements
}

Step "3. Tailscale (入れるだけ。ログインはザラの手)"
if (Test-Path "$env:ProgramFiles\Tailscale\tailscale.exe") {
  Write-Host "   既にある"
} else {
  winget install --id tailscale.tailscale -e --accept-source-agreements --accept-package-agreements
}
Write-Host "   次: タスクバーの Tailscale からログイン → 100. で始まるアドレスを控える (tailscale ip -4)" -ForegroundColor Yellow

Step "4. Windows Terminal に 4 部署 + WS のタブを足す (fragment)"
$fragDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\Fragments\THELIFEPLAN'
New-Item -ItemType Directory -Force -Path $fragDir | Out-Null
Copy-Item -Force (Join-Path $PSScriptRoot 'wt-fragment.json') (Join-Path $fragDir 'ws-desks.json')
Write-Host "   置いた: $fragDir\ws-desks.json (Windows Terminal を開き直すと「本社」「工場」「ミニ」「Book」「WS 机」のタブが出る)"

Step "4b. ws の一語で WS 机を開く (PowerShell・コマンドプロンプト)"
$binDir = Join-Path $env:USERPROFILE '.local\bin'
New-Item -ItemType Directory -Force -Path $binDir | Out-Null
Copy-Item -Force (Join-Path $PSScriptRoot 'ws.cmd') (Join-Path $binDir 'ws.cmd')
# 本人の PATH だけ (システム共通は触らない)。既にあれば足さない。
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$parts = @($userPath -split ';' | Where-Object { $_ })
if ($parts -notcontains $binDir) {
  [Environment]::SetEnvironmentVariable('Path', (($parts + $binDir) -join ';'), 'User')
  Write-Host "   PATH に足した: $binDir (新しく開いたシェルから効く)"
}
Write-Host "   置いた: $binDir\ws.cmd (ws と打つと WS 机のタブ)"

Step "5. スリープを切る (電源・バッテリーとも)"
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
powercfg /change hibernate-timeout-ac 0
powercfg /change hibernate-timeout-dc 0

Step "6. WSL を起動時に上げておく (sshd の受け口のため)"
# ノート PC は電池でも起動・継続・時間の上限なし (schtasks の既定は「電池では起動しない」・72 時間で止まる。2026-10-21 WS で実際に止まった)。
try {
  $u = "$env:USERDOMAIN\$env:USERNAME"
  $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
  $pr = New-ScheduledTaskPrincipal -UserId $u -LogonType Interactive -RunLevel Limited
  $tr = New-ScheduledTaskTrigger -AtLogOn -User $u
  $ac = New-ScheduledTaskAction -Execute "wsl.exe" -Argument "-d Ubuntu -- sleep infinity"
  Register-ScheduledTask -Force -TaskName "WS-wsl-keepalive" -Trigger $tr -Action $ac -Settings $set -Principal $pr -ErrorAction Stop | Out-Null
  Write-Host "   登録した: WS-wsl-keepalive (ログオン時・電池でも)"
} catch { Write-Host "   未確認: タスク登録に失敗。タスク スケジューラで手で入れる" -ForegroundColor Yellow }

Write-Host "`n================ 残りは人の手 ================" -ForegroundColor Green
Write-Host "a. Tailscale にザラのアカウントでログイン"
Write-Host "b. Ubuntu を開き、キットの wsl/setup-ws.sh を打つ (鍵と接続コマンドが入る)"
Write-Host "c. Ubuntu の中で claude / codex / grok を入れてログイン (手順書 節 1 の 4〜5)"
Write-Host "d. 自動ログオン (netplwiz) はザラが設定画面で。パスワードはどこにも書かない"
