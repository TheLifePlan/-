# Cafe Komorebi - Sample Homepage

GitHub Pages で公開するためのサンプルカフェサイトです。

## 公開方法

1. このリポジトリの **Settings** を開く
2. 左メニューから **Pages** を選択
3. **Source** で `Deploy from a branch` を選び、`main` ブランチを指定して **Save**
4. 数分後、`https://<ユーザー名>.github.io/<リポジトリ名>/` でアクセスできます

## ファイル構成

- `index.html` — ページの中身（テキストや構造）
- `style.css` — 見た目（色・レイアウト・レスポンシブ）

## カスタマイズの目安

| 変えたいもの | 編集するファイル | 場所の目安 |
| --- | --- | --- |
| 店名・キャッチコピー | `index.html` | `.hero` セクション |
| メニュー項目・価格 | `index.html` | `.menu-grid` 内 |
| 営業時間・住所 | `index.html` | `.info-list` 内 |
| 色合い | `style.css` | 先頭の `:root` 変数 |
