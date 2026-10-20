#!/usr/bin/env bash
# install-ai.sh — WS (Windows PC) の WSL2 Ubuntu に、机の道具 (claude / codex / grok) を入れる。
# Notion「Windows PC（WS）の手順書」節 1 の 4 (「Ubuntu の中で claude、codex、grok を入れて、3 つともログイン」) の、入れる所まで。
# ログイン (ブラウザで許可を押す) は人の手。この台本は鍵・トークンを読まない・書かない。
# 何度打っても同じ結果になる。無い物は「未確認」と書いて先へ進む (止めない)。
set -u
FLAGS="$HOME/ai/flags"; mkdir -p "$FLAGS" "$HOME/.local/bin"
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) export PATH="$HOME/.local/bin:$PATH";; esac
ok()   { echo "   済: $*"; }
todo() { echo "   未確認: $*"; }

echo "== 0. 土台 (curl / git / wslu)"
if command -v apt-get >/dev/null; then
  sudo apt-get update -qq
  # wslu = wslview。ログインのとき Ubuntu から Windows のブラウザを開くのに使う。無くても URL を手で貼れば進む。
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq curl git ca-certificates wslu >/dev/null 2>&1 \
    || sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq curl git ca-certificates >/dev/null
fi
if command -v wslview >/dev/null && [ -z "${BROWSER:-}" ]; then
  for rc in ~/.bashrc ~/.zshrc; do
    [ -f "$rc" ] || continue
    grep -q 'export BROWSER=wslview' "$rc" || printf '\n# WSL: ログインのブラウザを Windows 側で開く\nexport BROWSER=wslview\n' >> "$rc"
  done
  export BROWSER=wslview
fi

echo "== 1. Claude Code (claude)"
if command -v claude >/dev/null; then
  ok "既にある: $(claude --version 2>/dev/null | head -1)"
else
  # 公式の入れ方 (Node 不要)。~/.local/bin/claude に入る。
  if curl -fsSL https://claude.ai/install.sh | bash >/dev/null 2>&1 && command -v claude >/dev/null; then
    ok "入れた: $(claude --version 2>/dev/null | head -1)"
  else
    todo "claude の公式インストーラが通らなかった。Node を入れた後に  npm install -g @anthropic-ai/claude-code  で再挑戦する"
    echo "claude: install.sh 失敗 $(date +%F)" >> "$FLAGS/ws-claude-unconfirmed.txt"
  fi
fi

echo "== 2. Node.js (codex に要る。無ければ LTS を入れる)"
need_node=1
if command -v node >/dev/null; then
  major=$(node -v | sed 's/^v//; s/\..*//')
  if [ "${major:-0}" -ge 20 ]; then ok "既にある: $(node -v)"; need_node=0; else echo "   古い: $(node -v) → 入れ替える"; fi
fi
if [ "$need_node" = 1 ]; then
  if curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - >/dev/null 2>&1 \
     && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nodejs >/dev/null 2>&1; then
    ok "入れた: $(node -v)"
  else
    todo "Node が入らなかった。codex は後回し"
    echo "node: nodesource 失敗 $(date +%F)" >> "$FLAGS/ws-codex-unconfirmed.txt"
  fi
fi
# npm -g を sudo なしで使えるように (~/.npm-global)
if command -v npm >/dev/null; then
  mkdir -p "$HOME/.npm-global"
  npm config set prefix "$HOME/.npm-global" >/dev/null 2>&1 || true
  case ":$PATH:" in *":$HOME/.npm-global/bin:"*) ;; *) export PATH="$HOME/.npm-global/bin:$PATH";; esac
  for rc in ~/.bashrc ~/.zshrc; do
    [ -f "$rc" ] || continue
    grep -q 'npm-global/bin' "$rc" || printf '\n# npm -g の置き場 (sudo 不要)\nexport PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"\n' >> "$rc"
  done
fi
# claude がまだ無ければ npm で再挑戦
if ! command -v claude >/dev/null && command -v npm >/dev/null; then
  npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 && command -v claude >/dev/null && ok "claude を npm で入れた: $(claude --version 2>/dev/null | head -1)"
fi

echo "== 3. Codex CLI (codex)"
if command -v codex >/dev/null; then
  ok "既にある: $(codex --version 2>/dev/null | head -1)"
elif command -v npm >/dev/null; then
  if npm install -g @openai/codex >/dev/null 2>&1 && command -v codex >/dev/null; then
    ok "入れた: $(codex --version 2>/dev/null | head -1)"
  else
    todo "codex が入らなかった (npm install -g @openai/codex)"
    echo "codex: npm 失敗 $(date +%F)" >> "$FLAGS/ws-codex-unconfirmed.txt"
  fi
else
  todo "npm が無いので codex は入れていない"
fi

echo "== 4. Grok CLI (grok)"
case ":$PATH:" in *":$HOME/.grok/bin:"*) ;; *) export PATH="$HOME/.grok/bin:$PATH";; esac
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
  touch "$rc"
  grep -Fqx 'export PATH="$HOME/.grok/bin:$PATH"' "$rc" || printf '\n# Grok CLI\nexport PATH="$HOME/.grok/bin:$PATH"\n' >> "$rc"
done
if command -v grok >/dev/null; then
  rm -f "$FLAGS/ws-grok-unconfirmed.txt"
  ok "既にある: $(command -v grok)"
elif (set -o pipefail; curl -fsSL https://x.ai/cli/install.sh | bash >/dev/null 2>&1) \
    && command -v grok >/dev/null; then
  rm -f "$FLAGS/ws-grok-unconfirmed.txt"
  ok "入れた: $(command -v grok)"
else
  todo "grok の公式インストーラが通らなかった。GRの11窓は未確認"
  echo "未確認: grok install失敗 $(date +%F)" > "$FLAGS/ws-grok-unconfirmed.txt"
fi

echo
echo "================ 入っている物 ================"
for c in claude codex grok node tmux; do
  if command -v "$c" >/dev/null; then printf '   %-7s %s\n' "$c" "$(command -v "$c")"; else printf '   %-7s %s\n' "$c" "(無い)"; fi
done
echo
echo "================ ここから先は人の手 (ログイン) ================"
echo "A. 新しいシェルを開くか  source ~/.bashrc  を打つ (PATH を読み直す)。"
echo "B. claude と打つ → 「Claude account with subscription」を選ぶ → ブラウザが開いたら claude.ai のアカウントで許可。"
echo "   ブラウザが開かない時は、画面に出た URL を Windows のブラウザに貼る。"
echo "C. codex と打つ → Sign in with ChatGPT → 同じくブラウザで許可。"
echo "D. grok と打つ → ブラウザで本人が許可する（ログインは自動で行わない）。"
echo "E. 済んだら  ws-claude  で WSCL01 Claudeコマンダー の窓が立つ (Windows Terminal の「Claude (WSCL01)」タブも同じ)。"
echo "F. 本社の file (CLAUDE.md・ZARA-KIJUN.md など) の scp と windows.conf は手順書 節 2 のとおり別に打つ。"
