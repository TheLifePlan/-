# WS 接続キット — Windows PC から全部署 (本社・工場・ミニ・Book) へつなぐ

Notion「会社の仕組み・取り決め → 端末ごとの取り決め → Windows PC（WS）の手順書」(2026-10-20) を、
貼って動く台本にしたもの。手順書の**節 1 (ザラの手)・節 2 (鍵と ssh の受け口)・節 3 (本社側)・節 4 (確かめ)** を担う。
本社の file のコピー (scp) と机の起動表 (`~/ai/builder/windows.conf`) は手順書のとおり別に打つ。

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
| `windows/wt-fragment.json` | (Install が置く) | Windows Terminal に「本社・工場・ミニ・Book・WS 机・疎通」のタブ |
| `windows/Register-DesksOnLogon.ps1` | Windows の Claude・PowerShell | ログオン時に WS の机 (desks-startup.sh) が立つタスク。本社から写した後に |
| `wsl/setup-ws.sh` | Windows の Claude・Ubuntu | 道具・置き場・鍵・ssh 設定・sshd・接続コマンドを一度に入れる |
| `wsl/hosts.tsv.example` | → `~/ai/ws/hosts.tsv` に写して埋める | 部署ごとの宛先・tmux ソケット・セッション・着く窓 |
| `wsl/bin/desk` | Ubuntu | `desk <部署>` で窓へ。`desk <部署> sh` で普通のシェル。`DESK_MOSH=1` で mosh |
| `wsl/bin/desks-check` | Ubuntu | 4 部署の疎通を表に |
| `wsl/bin/accept-keys` | Ubuntu | 他部署の公開鍵の行を authorized_keys に足す (鍵の行だけ通す・重複しない) |
| `honsha/register-ws-key.sh` | 01・本社 prod@Studio | WS の公開鍵 1 行を 本社・工場 (ai@127.0.0.1)・ミニ・Book に足す |

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
3. **節 3・本社側 (01)** — prod@Studio で
   ```bash
   MINI=dev@<ミニの100.> BOOK=zara@<Bookの100.> ./honsha/register-ws-key.sh "ssh-ed25519 AAAA... WS-xxx"
   ```
   さらに `~/ai/CONTACTS.md` に WS の 1 行、`~/ai/bin/tell-targets.tsv` に WS の 11 窓 (ソケット `win`・セッション `win`) を足す (手順書どおり・手で)。
   4 部署の公開鍵を WS へ渡し、WS 側で `accept-keys` に貼る。
4. **節 2 の続き** — 手順書の scp で本社の file を写し、`windows.conf` (11 窓) を書き、`studio.sh --create-only`。その後 `.\windows\Register-DesksOnLogon.ps1 -LinuxUser <Ubuntuの名前>`。
5. **節 4・確かめ** — Ubuntu で `desks-check`。4 行 `ok` + 「窓 … あり」になれば行きは済。本社から `ssh -o BatchMode=yes <WSの利用者>@<WSの100.> echo win-ok` が返れば戻りも済。

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
