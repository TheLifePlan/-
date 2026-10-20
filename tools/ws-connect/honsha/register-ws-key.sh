#!/usr/bin/env bash
# register-ws-key.sh — 本社 (prod@Studio) で 01 が打つ。WS の公開鍵 1 行を 4 部署の authorized_keys に足す。
# Notion「Windows PC（WS）の手順書」節 3。秘密鍵は読まない。鍵の行は引数か標準入力で渡す。
#   使い方:  ./register-ws-key.sh "ssh-ed25519 AAAA... WS-xxxx"
#            echo "ssh-ed25519 ..." | ./register-ws-key.sh
# 宛先 (工場は同じ Studio の ai 利用者。ミニ・Book は Tailscale):
#   本社 = ここ (prod)  工場 = ai@127.0.0.1  ミニ = dev@<ミニの100.アドレス>  Book = zara@<Bookの100.アドレス>
# ミニ・Book のアドレスは環境変数で渡す (公開リポジトリなので書かない): MINI=dev@100.x.x.x BOOK=zara@100.x.x.x
set -eu
KEY="${1:-$(cat)}"
case "$KEY" in ssh-ed25519\ *|ssh-rsa\ *) ;; *) echo "公開鍵の行ではない" >&2; exit 1;; esac
MINI="${MINI:?MINI=dev@100.x.x.x を付けて実行}"
BOOK="${BOOK:?BOOK=zara@100.x.x.x を付けて実行}"
FACTORY="${FACTORY:-ai@127.0.0.1}"

add_local() {
  mkdir -p ~/.ssh; chmod 700 ~/.ssh; touch ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys
  if grep -qxF "$KEY" ~/.ssh/authorized_keys; then echo "本社: 既にある"; else printf '%s\n' "$KEY" >> ~/.ssh/authorized_keys; echo "本社: 足した"; fi
}
add_remote() { # $1=表示名 $2=宛先
  if ssh -o BatchMode=yes -o ConnectTimeout=8 "$2" "mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && (grep -qxF '$KEY' ~/.ssh/authorized_keys && echo 既にある || { printf '%s\n' '$KEY' >> ~/.ssh/authorized_keys && echo 足した; })" 2>/dev/null; then :; else echo "$1: 未確認 (ssh が届かない: $2)"; fi
}
add_local
printf '工場: '; add_remote 工場 "$FACTORY"
printf 'ミニ: '; add_remote ミニ "$MINI"
printf 'Book: '; add_remote Book "$BOOK"
echo "次: WS 側で  desks-check  を打って 4 行 ok を見る。本社からは  ssh -o BatchMode=yes <WSの利用者>@<WSの100.アドレス> echo win-ok"
