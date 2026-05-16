# Ninja Dash

iPhone のブラウザ（Safari）で遊べるシンプルなアクションゲーム。
HTML5 Canvas + JavaScript で作っています。インストール不要、URLを開くだけで遊べます。

## 遊び方

- 画面の左右をタップ／ドラッグしてニンジャを動かす
- 落ちてくる **岩**（赤）を避ける
- **星**（黄）を集めるとスコア +10
- 時間が経つほどスピードアップ。ハイスコアはブラウザに保存されます

## ローカルで動かす

ダブルクリックで `index.html` を開くだけでも動きますが、簡易サーバーを立てるのが確実です。

```bash
python3 -m http.server 8000
# → http://localhost:8000 をブラウザで開く
```

スマホで動作確認するときは、PCとスマホを同じWi-Fiにつないで
`http://<PCのローカルIP>:8000` をスマホのブラウザで開きます。

## iPhoneでの公開（GitHub Pages）

1. GitHubの **Settings → Pages** を開く
2. **Source** で `Deploy from a branch` を選び、ブランチを指定して **Save**
3. 数分後、`https://<ユーザー名>.github.io/<リポジトリ名>/` でアクセスできる
4. iPhoneのSafariでそのURLを開き、「ホーム画面に追加」するとアプリ風に遊べる

## ファイル構成

- `index.html` — ページ構造とUI（タイトル画面・ゲームオーバー画面など）
- `style.css`  — 見た目（HUD・オーバーレイ・ボタン）
- `game.js`    — ゲームのロジック（プレイヤー・敵・スコア・描画）

## カスタマイズの目安

| 変えたいもの | 編集するファイル | 場所 |
| --- | --- | --- |
| 難易度（スピード上昇カーブ） | `game.js` | `state.speed` の計算式 |
| 岩・星の出現頻度 | `game.js` | `spawnTimer` / `starTimer` の更新箇所 |
| プレイヤーの見た目 | `game.js` | `drawPlayer` 関数 |
| 色合い・フォント | `style.css` | 全体 |
| タイトル文言 | `index.html` | `#title` 内 |
