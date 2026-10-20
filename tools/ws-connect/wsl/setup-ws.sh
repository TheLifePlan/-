#!/usr/bin/env bash
# setup-ws.sh — WS (Windows PC) の WSL2 Ubuntu に「全部署へつなぐ仕組み」を入れる。
# Notion「Windows PC（WS）の手順書」節 2 の、鍵・ssh の受け口・接続コマンドの部分を 1 回で行う。
# WS向けの窓生成・menu・tmux設定を同梱する。AI wrapper等の本社fileは別途手順書で写す。
# 何度打っても同じ結果になる。秘密鍵は読まない・表示しない。
set -eu
KIT="$(cd "$(dirname "$0")" && pwd)"
WS="$HOME/ai/ws"

echo "== 1. 道具を入れる (tmux / openssh-server / mosh / python3 / zsh)"
if command -v apt-get >/dev/null; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq tmux python3 zsh openssh-server mosh >/dev/null
fi

echo "== 2. 置き場を作る"
mkdir -p ~/.ssh ~/.claude "$WS/bin" \
  ~/ai/bin ~/ai/builder ~/ai/flags \
  ~/ai/grok/02 ~/ai/grok/03 ~/ai/codex/02 ~/ai/codex/03 ~/ai/hands/02 ~/ai/hands/03
chmod 700 ~/.ssh

echo "== 3. この PC の鍵 (無ければ作る。あれば触らない)"
if [ ! -f ~/.ssh/id_ed25519 ]; then
  ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "WS-$(hostname)" >/dev/null
  echo "   作った: ~/.ssh/id_ed25519"
else
  echo "   既にある: ~/.ssh/id_ed25519"
fi

echo "== 4. 接続コマンドを入れる (~/ai/ws/bin)"
install -m 755 "$KIT/bin/desk" "$KIT/bin/desks-check" "$KIT/bin/accept-keys" "$KIT/bin/ws-claude" "$WS/bin/"
if [ ! -f "$WS/hosts.tsv" ]; then
  install -m 600 "$KIT/hosts.tsv.example" "$WS/hosts.tsv"
  echo "   宛先表の雛形を置いた: $WS/hosts.tsv  ← 100.x.x.x を本物に書き換える (Notion の手順書から)"
else
  echo "   宛先表は既にある: $WS/hosts.tsv"
fi
# PATH に通す (bash / zsh)
for rc in ~/.bashrc ~/.zshrc; do
  [ -f "$rc" ] || continue
  grep -q 'ai/ws/bin' "$rc" || printf '\n# WS 接続キット\nexport PATH="$HOME/ai/ws/bin:$PATH"\n' >> "$rc"
done

# 本社の表そのものは上書きしない。ここは将来WSで実行する配置処理。
install -m 755 "$KIT/bin/ws-windows-conf.py" "$KIT/bin/menu.sh" "$KIT/bin/studio.sh" "$HOME/ai/bin/"
install -m 644 "$KIT/builder/windows.conf.ws" "$KIT/builder/tmux.conf" "$HOME/ai/builder/"
echo "   WS窓の生成台本を配置した。READMEのpython3行でwindows.confを作る。"
mkdir -p "$WS/windows-terminal"
install -m 644 "$KIT/windows-terminal/profiles.json" "$WS/windows-terminal/profiles.json"
echo "   Terminal設定断片: $WS/windows-terminal/profiles.json。READMEの『Terminalの入口』でprofiles.list/F11を設定する。既定は変えず、入口は選んだ時だけ開く。"


echo "== 5. ssh の設定 (~/.ssh/config に Host 別名を足す。既存の行は触らない)"
CFG=~/.ssh/config; touch "$CFG"; chmod 600 "$CFG"
if ! grep -q '^# >>> ws-connect' "$CFG"; then
  cat >> "$CFG" <<'CFGEOF'
# >>> ws-connect (desk が使う共通設定。宛先は ~/ai/ws/hosts.tsv)
Host 100.* *.ts.net
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
  ConnectTimeout 8
  ServerAliveInterval 30
  ServerAliveCountMax 3
  StrictHostKeyChecking accept-new
# <<< ws-connect
CFGEOF
fi

echo "== 6. ssh の受け口 (他部署からこの PC へ入れるように)"
sudo ssh-keygen -A >/dev/null 2>&1 || true
if command -v systemctl >/dev/null && systemctl is-system-running >/dev/null 2>&1; then
  sudo systemctl enable --now ssh >/dev/null 2>&1 || sudo service ssh --full-restart >/dev/null 2>&1 || true
else
  sudo service ssh --full-restart >/dev/null 2>&1 || sudo service ssh start >/dev/null 2>&1 || true
fi
touch ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys
if pgrep -x sshd >/dev/null; then echo "   sshd 動いている"; else echo "   未確認: sshd が動いていない"; fi

echo
echo "================ ここから先は人の手 ================"
echo "A. 下の 1 行だけを本社 (SMCL01) へ渡す。本社側は honsha/register-ws-key.sh で 4 部署へ入れる。"
echo "   (鍵の中身を Notion や手順書に書かない)"
echo "-----"
cat ~/.ssh/id_ed25519.pub
echo "-----"
echo "B. $WS/hosts.tsv の 100.x.x.x を本物の宛先に書き換える。"
echo "C. 本社から 4 部署の公開鍵をもらったら:  accept-keys   (貼って Ctrl-D)"
echo "D. 確かめ:  desks-check     入る:  desk honsha | desk koujou | desk mini | desk book"
echo "E. 新しいシェルを開くか  source ~/.bashrc  で desk が使える。"
echo "F. この PC の机に Claude を入れる:  bash $KIT/install-ai.sh   (claude / codex を入れる。ログインは人の手)"
