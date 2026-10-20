#!/usr/bin/env bash
# Helperだけを更新する。apt/鍵作成/公開鍵表示/AI起動/tmux変更は行わない。
set -euo pipefail
KIT=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$HOME/ai/ws/bin"
install -m 755 "$KIT/bin/refresh-hq-helpers" "$HOME/ai/ws/bin/refresh-hq-helpers"
exec python3 "$HOME/ai/ws/bin/refresh-hq-helpers" "$@"
