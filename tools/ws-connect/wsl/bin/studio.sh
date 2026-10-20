#!/usr/bin/env bash
# WS専用。既存winセッションを壊さず、windows.confの番号どおりに一度だけ作る。
set -euo pipefail
CONF=${WS_WINDOWS_CONF:-$HOME/ai/builder/windows.conf}
SOCKET=${WS_TMUX_SOCKET:-win}
CONFIG=${WS_TMUX_CONFIG:-$HOME/ai/builder/tmux.conf}
T=(tmux -L "$SOCKET" -f "$CONFIG")
[[ -f "$CONF" ]] || { echo 'windows.confを先に生成してください。' >&2; exit 1; }
# 全行を先に検査する。ここではフォルダ/窓をまだ作らない。
expected=$(python3 - "$CONF" <<'PYCONF'
from pathlib import Path
import sys
rows, seen = [], set()
home = Path.home().resolve()
for raw in Path(sys.argv[1]).read_text().splitlines():
    if not raw or raw.startswith('#'):
        continue
    parts = raw.split('|', 3)
    if len(parts) != 4:
        raise SystemExit('窓の表が不正です。')
    number, name, folder, command = parts
    if not number.isascii() or not number.isdigit() or int(number) in seen or not all(parts[1:]):
        raise SystemExit('窓の表が不正です。')
    if not Path(folder).is_absolute():
        raise SystemExit('フォルダはHOME以下の絶対パスにしてください。')
    if not Path(folder).resolve().is_relative_to(home):
        raise SystemExit('フォルダはHOME内だけにしてください。')
    seen.add(int(number)); rows.append((int(number), name))
if not rows:
    raise SystemExit('窓の表が空です。')
for number, name in sorted(rows):
    print(str(number) + '|' + name)
PYCONF
)
if "${T[@]}" has-session -t '=win' 2>/dev/null; then
  actual=$("${T[@]}" list-windows -t '=win' -F '#{window_index}|#{window_name}' | sort -t '|' -k1,1n)
  [[ "$actual" == "$expected" ]] || { echo '未変更・表と不一致（既存winセッション）。' >&2; exit 1; }
else
  mkdir -p "$HOME/ai/flags"
  first=''
  while IFS='|' read -r number name dir command; do
    [[ -z "$number" || "$number" == \#* ]] && continue
    [[ "$number" =~ ^[0-9]+$ && -n "$name" && -n "$dir" && -n "$command" ]] || { echo '窓の表が不正です。' >&2; exit 1; }
    # 表から作るフォルダはWSのHOME内だけ。外向きsymlinkも拒否する。
    python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); h=pathlib.Path.home().resolve(); r=p.resolve(); r.relative_to(h); p.mkdir(parents=True,exist_ok=True)' "$dir"
    # CLI/helperが未設置でも窓はshellとして残す。コマンドはevalせずtmuxの1引数。
    escaped=${command//\'/\'\\\'\'}
    launch="bash -c '$escaped'; rc=\$?; if [ \"\$rc\" -ne 0 ]; then printf '%s\\n' 'WS window $number CLI/helper unconfirmed' >> \"\$HOME/ai/flags/ws-cli-unconfirmed.txt\"; fi; exec bash -l"
    if [[ -z "$first" ]]; then
      "${T[@]}" new-session -d -s win -n "$name" -c "$dir" "$launch"
      current=$("${T[@]}" list-windows -t '=win' -F '#{window_index}')
      [[ "$current" == "$number" ]] || "${T[@]}" move-window -s "win:$current" -t "win:$number"
      first=$number
    else
      "${T[@]}" new-window -d -t "win:$number" -n "$name" -c "$dir" "$launch"
    fi
  done < "$CONF"
  [[ -n "$first" ]] || { echo '窓の表が空です。' >&2; exit 1; }
  "${T[@]}" select-window -t "win:$first"
fi
[[ "${1:-}" == --create-only ]] && exit 0
exec "${T[@]}" attach-session -t '=win'
