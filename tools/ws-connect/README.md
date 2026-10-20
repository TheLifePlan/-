# WS 接続キット — Windows PC から全部署 (本社・工場・ミニ・Book) へつなぐ

Notion「会社の仕組み・取り決め → 端末ごとの取り決め → Windows PC（WS）の手順書」(2026-10-20) を、
貼って動く台本にしたもの。手順書の**節 1 (ザラの手)・節 2 (鍵と ssh の受け口)・節 3 (本社側)・節 4 (確かめ)** を担う。
本社の補助台本は下の専用refresh段で取り直す。机の起動表は同梱の本社57行テンプレートからWS向けに生成する。

**このリポジトリは公開**なので、Tailscale の宛先・利用者名・鍵はここに書かない。宛先は PC の中の `~/ai/ws/hosts.tsv` に置く。

## 仕組み

```
Windows Terminal のタブ ──▶ WSL2 Ubuntu ──▶ desk <部署> ──▶ ssh (Tailscale 100.x) ──▶ 部署の tmux の窓
  本社 / 工場 / ミニ / Book                                  honsha → SMCL01   koujou → SFCL01
                                                              mini   → MDCL01   book   → BVCL01
他部署 ──▶ ssh <WSの利用者>@<WSの100.アドレス> ──▶ Ubuntu の sshd ──▶ tmux -L win (WS の机)
```

- **行き**: `desk honsha` のように打つと、その部署の tmux の **名前の窓** (SMCL01 など) に着く。番号でなく名前で着く (zv と同じ考え)。
- **戻り**: Ubuntu の sshd が受け口。4 部署の公開鍵を `accept-keys` で足す。
- **確かめ**: `desks-check` が 4 部署へ鍵だけで届くか、窓が見えるかを表にする。中には入らない・書かない。
- 全端末同権限・ssh 双方向 (共通の取り決め 2026-10-20) に沿う。秘密鍵は AI が読まない・写さない。

## 置いてある物

| 場所 | 誰が・どこで | 何をする |
| --- | --- | --- |
| `windows/Install-WS.ps1` | ザラ・Windows の管理者 PowerShell | WSL2+Ubuntu、Windows Terminal、Tailscale を入れる。タブ fragment を置く。スリープを切る |
| `windows/wt-fragment.json` | (Install が置く) | Windows Terminal に「本社・工場・ミニ・Book・Claude (WSCL01)・WS 机・疎通」のタブ |
| `windows/Register-DesksOnLogon.ps1` | Windows の Claude・PowerShell | ログオン時に WS の机 (desks-startup.sh) が立つタスク WS-desks と、60 秒後に「WS 机」のタブを開く WS-terminal。どちらも電池でも起動。本社から写した後に |
| `windows/ws.cmd` | (Install が置く) | PowerShell・コマンドプロンプトで `ws` と打つと「WS 机」のタブ。置き場 = 本人の `.local\bin` (本人の PATH) |
| `wsl/bin/ws` | (setup-ws が置く) | Ubuntu のシェルで `ws` と打つと `~/ai/bin/studio.sh` で WS 机へ入る |
| `wsl/setup-ws.sh` | Windows の Claude・Ubuntu | 道具・置き場・鍵・ssh 設定・sshd・接続コマンドを一度に入れる |
| `wsl/install-ai.sh` | ザラか Windows の Claude・Ubuntu | **claude / codex / grok を Ubuntu に入れる** (手順書 節 1 の 4)。ログインは人の手。無い物は未確認で先へ進む |
| `wsl/bin/ws-claude` | Ubuntu | `ws-claude` で WSCL01 Claudeコマンダー を立てる (02/03 で助さん・格さん)。tmux の机に同じ窓があればそこへ着く |
| `wsl/hosts.tsv.example` | → `~/ai/ws/hosts.tsv` に写して埋める | 部署ごとの宛先・tmux ソケット・セッション・着く窓 |
| `wsl/bin/desk` | Ubuntu | `desk <部署>` で窓へ。`desk <部署> sh` で普通のシェル。`DESK_MOSH=1` で mosh |
| `wsl/bin/desks-check` | Ubuntu | 4 部署の疎通を表に |
| `wsl/bin/accept-keys` | Ubuntu | 他部署の公開鍵の行を authorized_keys に足す (鍵の行だけ通す・重複しない) |
| `honsha/register-ws-key.sh` | 01・本社 prod@Studio | WS の公開鍵 1 行を 本社・工場 (ai@127.0.0.1)・ミニ・Book に足す |

## キットを引いた後の場所

この変更の配布ブランチは `claude/blissful-planck-hf89at`（リポジトリ `TheLifePlan/-`）。既にcloneした場合も、このブランチの最新版を使う。以下の相対パスのコマンドは、リポジトリ内の `tools/ws-connect` を開いてから実行する。Ubuntuでは `cd <cloneした場所>/tools/ws-connect`、PowerShellでも同じフォルダへ移動する。`setup-ws.sh` 実行後の `~/ai/bin/...` はどこからでも実行できる。

## 順番 (手順書の節に対応)

1. **節 1・ザラの手** — Windows の管理者 PowerShell で
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass -Force
   .\windows\Install-WS.ps1
   ```
   再起動 → Ubuntu の名前とパスワードを決める → Tailscale にログインして `100.` のアドレスを控える。
2. **節 2・Windows の Claude** — Ubuntu で (キットは `git clone` か、この `tools/ws-connect` を丸ごと写す)
   ```bash
   bash wsl/setup-ws.sh
   ```
   最後に出る **公開鍵の 1 行だけ** を本社 (SMCL01) へ渡す。続けて `~/ai/ws/hosts.tsv` の `100.x.x.x` を本物に書き換える (値は手順書 節 2・3 と各端末の頁)。
   **この PC の机に3つのCLIを入れる** (手順書 節 1 の 4) — 同じ Ubuntu で
   ```bash
   bash wsl/install-ai.sh      # claude / codex / grok を入れる
   source ~/.bashrc
   claude                      # ブラウザが開く → claude.ai のアカウントで許可 (人の手)
   codex                       # 同じく ChatGPT でログイン
   grok                        # 本人がブラウザで許可してログイン
   ws-claude                   # WSCL01 Claudeコマンダー の窓が立つ (Windows Terminal の「Claude」タブも同じ)
   ```
   Grok CLIのLinux版は[公式installer](https://x.ai/cli/install.sh)で入る。`install-ai.sh` は無ければ `curl -fsSL https://x.ai/cli/install.sh | bash` を実行し、`~/.grok/bin` を今と新しいshellのPATHへ追加する。失敗した時だけ `~/ai/flags/ws-grok-unconfirmed.txt` を残す。ログインは本人が `grok` を起動してブラウザで許可する（手順書 節1の4・節5）。Grokが入れば変換表はGR11窓を含む57行。
3. **節 3・本社側 (01)** — prod@Studio で
   ```bash
   MINI=dev@<ミニの100.> BOOK=zara@<Bookの100.> ./honsha/register-ws-key.sh "ssh-ed25519 AAAA... WS-xxx"
   ```
   さらに `~/ai/CONTACTS.md` に WS の 1 行、`~/ai/bin/tell-targets.tsv` に WS の生成された全窓 (ソケット `win`・セッション `win`) を足す (手順書どおり・手で)。
   4 部署の公開鍵を WS へ渡し、WS 側で `accept-keys` に貼る。
4. **節 2 の続き** — 手順書の scp で必要な補助台本を写す。鍵が通った後、helperの配置は下の「補助台本の束」を使う。旧7本だけのscpではtell/guard等が欠けるため使わない。`setup-ws.sh` でWS向け台本を配置した後、次の1行で本社と同じ番号・順番の表を作る。
   ```bash
   python3 ~/ai/bin/ws-windows-conf.py > ~/ai/builder/windows.conf
   ```
   実行前に `command -v claude` と `command -v codex` の両方が通ることを確認する。既存表を再生成する時は、失敗で元の表を空にしないよう `python3 ~/ai/bin/ws-windows-conf.py > ~/ai/builder/windows.conf.new && mv ~/ai/builder/windows.conf.new ~/ai/builder/windows.conf` を使う。
   手順書 節2の旧 `cat > windows.conf`（11行）は使わない。
   続けて `~/ai/bin/studio.sh --create-only`。その後 `.\windows\Register-DesksOnLogon.ps1 -LinuxUser <Ubuntuの名前>`。
   `studio.sh` は `tmux -L win`・セッション `win` を使い、既存セッションを作り直さない。表と番号・名前が違う場合は未変更のまま止まる。表のフォルダはHOME内だけ作る。CLIや補助台本が未設置なら窓はshellで残り、`~/ai/flags/ws-cli-unconfirmed.txt` に窓番号を残す。業務可能とは扱わない。
   Grokが見つからない時はGR行を除外し、番号は詰めず `~/ai/flags/ws-grok-unconfirmed.txt` に残す。
5. **節 4・確かめ** — Ubuntu で `desks-check`。4 行 `ok` + 「窓 … あり」になれば行きは済。本社から `ssh -o BatchMode=yes <WSの利用者>@<WSの100.> echo win-ok` が返れば戻りも済。

## 補助台本の束（配置・以後の取り直し）

キットの最新版を引き、`tools/ws-connect` からUbuntuのbashで実行する。本社の実宛先へ書き換えてから `bash wsl/refresh-helpers.sh --source '本社の利用者@Tailscale名'`。`~/ai/ws/hosts.tsv` のhonsha行が設定済みなら `bash wsl/refresh-helpers.sh` だけでもよい。配置後の更新も同じ1行。`setup-ws.sh` 全体をやり直さず、このhelper専用段だけを使う。

公開キットは取り直しのレシピだけを持つ。本社の31ファイルを明示一覧でSCPし、WSの私有一時フォルダで全件検査してから配置する。フォルダ丸ごとのSCPはしない。本社の台本は変更しない。対象はtell/hand・秘書3種・ayako/health/新聞/YouTube/builder・desk/home-window/menu-navigationと必要module、guardのコード/固定hook設定だけ。guardのstate/alerts/diagnostics/backup/tests、鍵/auth/.env、会話、HQのhead/hands snapshotは写さない。

WS用にHOME・記号WS・win/winを読み替え、tell宛先は既存57窓の表からAI56窓だけを生成する。メニューとshellは本文を誤投入しないためtellの宛先から除く。元のwindows.confや窓番号/名前/稼働AIは変更しない。YouTubeはHQのresume IDを使わず新規起動、builder/YouTubeの初回紙はWS本人の接続確認だけを行って待機する内容を生成する。必要最小の規則/STARTUPは無い場合だけ置き、既存のWS規則は残す。healthの承認印は作らない。

head/hands/snapshotが全て無いWSだけ、今回本社コマンダーが確認した `claude/claude` でWS独自generationを初期化する。既存が1つでもあれば上書きしない。役割の初期値であり、費用/外部送信/本番の権限を広げない。

専用段はレシピも `~/ai/ws/bin/refresh-hq-helpers` へ配置する。配置だけの確認は `python3 ~/ai/ws/bin/refresh-hq-helpers --inspect`。ファイル名/件数の確認で、AI・tell・hand・guard巡回は起動しない。稼働窓をまとめて再起動しない。未起動窓の立て直しは担当の実プロセス確認後に対象だけ行う。導入済みと、実際に各窓が使えることは別に検収する。

## WSのメニューとFキー

`wsl/bin/menu.sh` はWSの窓一覧から番号か記号で移動する。`SMCL01` のような本社記号の入力も `WSCL01` として探す。`wsl/builder/tmux.conf` は全端末共通の `~/.tmux.conf` と同じ中身 (2026-10-21)。`wsl/bin/studio.sh` も起動時に `~/.tmux.conf` を読み (`WS_TMUX_CONFIG` で上書き可)、Fキー・帯・Home は `~/ai/terminal.conf` を `tmux-terminal-config.py` が当てる (F1=Codex01・F5=Claude01・F9=Grok01、Home=WSCD01)。窓は左から 1 WSCD01・2 WSCL01・3 WSGR01、MENU窓は廃止。帯の[WS]を押すと `~/ai/work-menu.tsv` の仕事順の一覧 (3コマンダー→仕事→全机)。`wsl/builder/work-menu.tsv` は1行=表示名<TAB>hands|all|note<TAB>番号。hands は今の手足の家の机へ (入力/申込 42 と照合 03 は別机)。最終提出の命令は無い。

本社専用の動的status/head/hands切替helperは同梱しない。Shift+F1のhands09への動的移動も未対応。AI wrapperと各机の引継ぎ/規則、業務サービスの導入・稼働確認はこの窓配置だけでは完了しない。

## Terminalの入口（iTermのプロファイルに相当）

5入口は「WS 机・本社・工場・ミニ・Book」。WS 机は `~/ai/bin/studio.sh` で `tmux -L win` の `win` へ入る。win が無ければ表どおり57窓を作ってから入り、ほかの起動が作っている間は終わるまで待つ (空の win は作らない)。本社などの実宛先は公開JSONへ入れず、WS内の `~/ai/ws/hosts.tsv` を `terminal-entry` が読む。工場は専用の `factory-remote.sh` へ入り、端末ごとに別の今の窓を保つ。

`setup-ws.sh` は手動設定用の断片を `~/ai/ws/windows-terminal/profiles.json` へ置く。設定は自動で書き換えない。Windows Terminalで `Ctrl+,` →「JSONファイルを開く」を選ぶ。通常版の実体は `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`、非Store版は `%LOCALAPPDATA%\Microsoft\Windows Terminal\settings.json`、Preview版は `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json`。開いたsettings.jsonを先に控え、次のどちらか1つで入れる。

- **Install-WSの自動fragmentを使う**: `windows/wt-fragment.json` が配置する7入口（5入口＋Claude・疎通）を使う。新断片の `profiles.list` は追加しない。新断片の `keybindings` の項目だけをsettings.jsonの一番外側へ併合する。既存の `defaultProfile` は変更しない。settings.json全体を新断片で置き換えない。
- **手動で5入口を入れる**: Install-WSを使った場合は、先に `%LOCALAPPDATA%\Microsoft\Windows Terminal\Fragments\THELIFEPLAN\ws-desks.json` だけをFragments外へ退避する。他のfragmentは触らない。その後、新断片の `profiles.list` の5要素をsettings.jsonの既存 `profiles.list` へ足す。同じGUIDが既にあれば追加せずその要素を更新する。`keybindings` は一番外側の同名設定へ併合する。既存の `defaultProfile` は変更しない。既存の別プロファイル/キー設定を丸ごと置き換えない。手動版はClaude・疎通の補助2入口を含まない。

5入口のGUIDと名前は両方式で共通。入口はメニューから選んだ時だけ開く。既定は既存のWindows PowerShellのまま変更しない。`keybindings` の `{"id":null,"keys":"f11"}` でTerminalのF11全画面を外し、tmuxへ渡す。既存の `f11` キー設定がある場合はその要素をnull設定へ置き換え、同じキーを重複追加しない。F1〜12はWSのtmux.confが扱う。別のFキーもTerminalに登録されている時は同じ方法で該当キーだけ外す。古いTerminalで `keybindings` が使えない場合は更新するか、旧式の `actions` に `{"command":"unbound","keys":"f11"}` を設定する。fragment側にはdefaultProfile/keybindingsを足さない。

前の設定で新しいタブが「WS 机」になった場合は、Windows Terminalの `設定 → スタートアップ → 既定のプロファイル` で `Windows PowerShell` を選び、`保存` する。既存利用者のGUIDは書き換えずGUIで戻す。

moshがWS側と接続先の両方にあれば、Ubuntuで `DESK_MOSH=1 ~/ai/ws/bin/terminal-entry honsha`（他は `koujou` / `mini` / `book`）で同じ入口を使える。profileをmoshにしたい場合はcommandline内のhelperの前に `DESK_MOSH=1 ` を付ける。未導入なら既定のsshを使う。

**先に57窓の表を生成して `~/ai/bin/studio.sh --create-only` を行うのが通常の順番。** 2026-10-21 から「WS 机」も studio.sh を通るので、1窓だけの win はできない。前の版の fallback で1窓だけの win が残っている場合は、57窓の表と一致しないため studio.sh は未変更のまま止まる。既存winを自動削除しない。本社へ状態を伝えて配置を整える。

本社・ミニ・Book側へ将来追加する「WS」の入口は `ssh -t <WS利用者>@<WSのTailscale名または100アドレス> tmux -L win attach -t win`。PC名/Tailscale名の本人回答後に各端末の担当が値を入れる。今は空欄で、各端末のメニューは今回変更していない。

公式: [settings.jsonの場所](https://learn.microsoft.com/en-us/windows/terminal/install)、[既定プロファイルの設定](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/startup)、[キー解除](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/actions)、[fragment形式](https://learn.microsoft.com/en-us/windows/terminal/json-fragment-extensions)。Windows Terminal/WSL実機での表示とFキー到達は未確認。

## hosts.tsv の書き方

タブ区切り。`記号 表示名 ユーザー@アドレス tmuxソケット セッション 窓`。ソケット・セッションが無い所は `-`。

```
honsha	本社	prod@100.…	-	main	SMCL01
koujou	工場	ai@100.…	studio	-	SFCL01
mini	ミニ	dev@100.…	mini	mini	MDCL01
book	Book	zara@100.…	-	zara	BVCL01
```

工場は本社と同じ Studio の `ai` 利用者なので、アドレスは本社と同じ。工場の tmux セッション名は未確認なので `-` (最後に使った部屋に着く)。

## 分かっていないこと (手順書 節 5 と同じ)

- WSL の sshd へ Tailscale の `100.` 宛てで届くかは、Windows 側 Tailscale だけでは通らないことがある。届かなければ Ubuntu の中にも Linux 版 Tailscale を入れる (`curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`) のが 01 の候補。届いた方だけ残す。
- Grok CLIのLinux版はある（[公式installer](https://x.ai/cli/install.sh)）。WSでの導入結果とブラウザログインは実機確認する。
- 工場の tmux セッション名。`desk koujou` が違う部屋に着いたら hosts.tsv の 5 列目に名前を書く。

## 決まりとの対応

- 鍵の中身は Notion・手順書・このリポジトリに書かない (共通の取り決め「権限と守る線」)。
- `desks-check` は読むだけ。再起動・書込みは `desk` で入ってから人が押す。
- 設定が入ったことと、実機で届いたことは分けて記録する。`desks-check` の表がその記録になる。
