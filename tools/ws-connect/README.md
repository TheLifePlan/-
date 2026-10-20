# WS 接続キット — Windows PC から全部署 (本社・工場・ミニ・Book) へつなぐ

Notion「会社の仕組み・取り決め → 端末ごとの取り決め → Windows PC（WS）の手順書」(2026-10-20) を、
貼って動く台本にしたもの。手順書の**節 1 (ザラの手)・節 2 (鍵と ssh の受け口)・節 3 (本社側)・節 4 (確かめ)** を担う。
本社の補助台本のコピー (scp) は手順書に沿って行う。机の起動表は同梱の本社58行テンプレートからWS向けに生成する。

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
| `windows/Register-DesksOnLogon.ps1` | Windows の Claude・PowerShell | ログオン時に WS の机 (desks-startup.sh) が立つタスク。本社から写した後に |
| `wsl/setup-ws.sh` | Windows の Claude・Ubuntu | 道具・置き場・鍵・ssh 設定・sshd・接続コマンドを一度に入れる |
| `wsl/install-ai.sh` | ザラか Windows の Claude・Ubuntu | **claude / codex (/ grok があれば) を Ubuntu に入れる** (手順書 節 1 の 4)。ログインは人の手。無い物は未確認で先へ進む |
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
   **この PC の机に Claude を入れる** (手順書 節 1 の 4) — 同じ Ubuntu で
   ```bash
   bash wsl/install-ai.sh      # claude / codex を入れる (Node 不要の公式インストーラ → 無理なら npm)
   source ~/.bashrc
   claude                      # ブラウザが開く → claude.ai のアカウントで許可 (人の手)
   codex                       # 同じく ChatGPT でログイン
   ws-claude                   # WSCL01 Claudeコマンダー の窓が立つ (Windows Terminal の「Claude」タブも同じ)
   ```
   Grok CLI の Linux 版が見つからなければ `~/ai/flags/ws-grok-unconfirmed.txt` が残り、GR の窓は立てない (手順書 節 5)。
3. **節 3・本社側 (01)** — prod@Studio で
   ```bash
   MINI=dev@<ミニの100.> BOOK=zara@<Bookの100.> ./honsha/register-ws-key.sh "ssh-ed25519 AAAA... WS-xxx"
   ```
   さらに `~/ai/CONTACTS.md` に WS の 1 行、`~/ai/bin/tell-targets.tsv` に WS の生成された全窓 (ソケット `win`・セッション `win`) を足す (手順書どおり・手で)。
   4 部署の公開鍵を WS へ渡し、WS 側で `accept-keys` に貼る。
4. **節 2 の続き** — 手順書の scp で必要な補助台本を写す。`setup-ws.sh` でWS向け台本を配置した後、次の1行で本社と同じ番号・順番の表を作る。
   ```bash
   python3 ~/ai/bin/ws-windows-conf.py > ~/ai/builder/windows.conf
   ```
   実行前に `command -v claude` と `command -v codex` の両方が通ることを確認する。既存表を再生成する時は、失敗で元の表を空にしないよう `python3 ~/ai/bin/ws-windows-conf.py > ~/ai/builder/windows.conf.new && mv ~/ai/builder/windows.conf.new ~/ai/builder/windows.conf` を使う。
   手順書 節2の旧 `cat > windows.conf`（11行）は使わない。
   続けて `~/ai/bin/studio.sh --create-only`。その後 `.\windows\Register-DesksOnLogon.ps1 -LinuxUser <Ubuntuの名前>`。
   `studio.sh` は `tmux -L win`・セッション `win` を使い、既存セッションを作り直さない。表と番号・名前が違う場合は未変更のまま止まる。表のフォルダはHOME内だけ作る。CLIや補助台本が未設置なら窓はshellで残り、`~/ai/flags/ws-cli-unconfirmed.txt` に窓番号を残す。業務可能とは扱わない。
   Grokが見つからない時はGR行を除外し、番号は詰めず `~/ai/flags/ws-grok-unconfirmed.txt` に残す。
5. **節 4・確かめ** — Ubuntu で `desks-check`。4 行 `ok` + 「窓 … あり」になれば行きは済。本社から `ssh -o BatchMode=yes <WSの利用者>@<WSの100.> echo win-ok` が返れば戻りも済。

## WSのメニューとFキー

`wsl/bin/menu.sh` はWSの窓一覧から番号か記号で移動する。`SMCL01` のような本社記号の入力も `WSCL01` として探す。`wsl/builder/tmux.conf` はF1〜4=Codex、F5〜8=Claude、F9〜12=Grok、各組はコマンダー→さな→えま→みおの固定。HomeでWSメニュー。Grok未設置時のF9〜12は行先が無い。

本社専用の動的status/head/hands切替helperは同梱しない。Shift+F1のhands09への動的移動も未対応。AI wrapperと各机の引継ぎ/規則、業務サービスの導入・稼働確認はこの窓配置だけでは完了しない。

## Terminalの入口（iTermのプロファイルに相当）

5入口は「WS 机・本社・工場・ミニ・Book」。WS 机は `tmux -L win` の `win` へ入り、不在時だけ1窓を作る。本社などの実宛先は公開JSONへ入れず、WS内の `~/ai/ws/hosts.tsv` を `terminal-entry` が読む。工場は専用の `factory-remote.sh` へ入り、端末ごとに別の今の窓を保つ。

`setup-ws.sh` は手動設定用の断片を `~/ai/ws/windows-terminal/profiles.json` へ置く。設定は自動で書き換えない。Windows Terminalで `Ctrl+,` →「JSONファイルを開く」を選ぶ。通常版の実体は `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`、非Store版は `%LOCALAPPDATA%\Microsoft\Windows Terminal\settings.json`、Preview版は `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json`。開いたsettings.jsonを先に控え、次のどちらか1つで入れる。

- **Install-WSの自動fragmentを使う**: `windows/wt-fragment.json` が配置する7入口（5入口＋Claude・疎通）を使う。新断片の `profiles.list` は追加しない。新断片の `defaultProfile` と `keybindings` の項目だけをsettings.jsonの一番外側へ併合する。settings.json全体を新断片で置き換えない。
- **手動で5入口を入れる**: Install-WSを使った場合は、先に `%LOCALAPPDATA%\Microsoft\Windows Terminal\Fragments\THELIFEPLAN\ws-desks.json` だけをFragments外へ退避する。他のfragmentは触らない。その後、新断片の `profiles.list` の5要素をsettings.jsonの既存 `profiles.list` へ足す。同じGUIDが既にあれば追加せずその要素を更新する。`defaultProfile` と `keybindings` は一番外側の同名設定へ併合する。既存の別プロファイル/キー設定を丸ごと置き換えない。手動版はClaude・疎通の補助2入口を含まない。

5入口のGUIDと名前は両方式で共通。既定は「WS 机」。`keybindings` の `{"id":null,"keys":"f11"}` でTerminalのF11全画面を外し、tmuxへ渡す。既存の `f11` キー設定がある場合はその要素をnull設定へ置き換え、同じキーを重複追加しない。F1〜12はWSのtmux.confが扱う。別のFキーもTerminalに登録されている時は同じ方法で該当キーだけ外す。古いTerminalで `keybindings` が使えない場合は更新するか、旧式の `actions` に `{"command":"unbound","keys":"f11"}` を設定する。fragment側にはdefaultProfile/keybindingsを足さない。

moshがWS側と接続先の両方にあれば、Ubuntuで `DESK_MOSH=1 ~/ai/ws/bin/terminal-entry honsha`（他は `koujou` / `mini` / `book`）で同じ入口を使える。profileをmoshにしたい場合はcommandline内のhelperの前に `DESK_MOSH=1 ` を付ける。未導入なら既定のsshを使う。

**先に58窓の表を生成して `~/ai/bin/studio.sh --create-only` を行うのが通常の順番。** 「WS 机」のfallbackで1窓だけのwinが先にできた場合、58窓の表とは一致しないためstudio.shは未変更のまま止まる。既存winを自動削除しない。本社へ状態を伝えて配置を整える。

本社・ミニ・Book側へ将来追加する「WS」の入口は `ssh -t <WS利用者>@<WSのTailscale名または100アドレス> tmux -L win attach -t win`。PC名/Tailscale名の本人回答後に各端末の担当が値を入れる。今は空欄で、各端末のメニューは今回変更していない。

公式: [settings.jsonの場所](https://learn.microsoft.com/en-us/windows/terminal/install)、[defaultProfile](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/startup)、[キー解除](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/actions)、[fragment形式](https://learn.microsoft.com/en-us/windows/terminal/json-fragment-extensions)。Windows Terminal/WSL実機での表示とFキー到達は未確認。

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
- Grok CLI の Linux 版の有無。`command -v grok` で確かめる。
- 工場の tmux セッション名。`desk koujou` が違う部屋に着いたら hosts.tsv の 5 列目に名前を書く。

## 決まりとの対応

- 鍵の中身は Notion・手順書・このリポジトリに書かない (共通の取り決め「権限と守る線」)。
- `desks-check` は読むだけ。再起動・書込みは `desk` で入ってから人が押す。
- 設定が入ったことと、実機で届いたことは分けて記録する。`desks-check` の表がその記録になる。
