#!/usr/bin/env bash
# WSの窓一覧。0/番号/WS記号で選ぶ。SM記号はWSに読み替える。
set -u
export TZ=Asia/Tokyo
TMUX_BIN=$(command -v tmux) || exit 1
while :; do
  printf '\033[2J\033[H[WS]\n'
  "$TMUX_BIN" -L win list-windows -t '=win' -F '#{window_index}  #{window_name}' || exit 1
  printf '\nF1–4 Codex / F5–8 Claude / F9–12 Grok\n移動先 > '
  IFS= read -r -t 30 choice || continue
  choice=$(printf '%s' "$choice" | tr '[:lower:]' '[:upper:]')
  choice=${choice/#SM/WS}
  if [[ "$choice" =~ ^[0-9]+$ ]]; then
    "$TMUX_BIN" -L win select-window -t "=win:$choice" 2>/dev/null || true
    continue
  fi
  [[ "$choice" =~ ^WS(MENU|(CL|CD|GR)[0-9]{2})$ ]] || continue
  matches=()
  while IFS='|' read -r index name; do
    [[ "${name%% *}" == "$choice" ]] && matches+=("$index")
  done < <("$TMUX_BIN" -L win list-windows -t '=win' -F '#{window_index}|#{window_name}')
  [[ ${#matches[@]} == 1 ]] && "$TMUX_BIN" -L win select-window -t "=win:${matches[0]}"
done
