# 株式会社RISE 企業サイト（非公式・提案用デモ）

社長へのご提案用に制作したデモサイトです。**正式な公開サイトではありません。**
写真・施工実績・紹介文・理念などはすべてサンプルです。

## 確認方法

ビルド済みのHTMLがリポジトリ直下にあるので、`index.html` をブラウザで開けばそのまま表示できます。
ローカルサーバーで確認する場合：

```bash
npx http-server -c-1 .   # → http://localhost:8080
```

## ページ構成

| ファイル | 内容 |
| --- | --- |
| `index.html` | TOP（ファーストビュー／会社紹介／事業内容／施工実績／企業理念／採用予告／お問い合わせ） |
| `company.html` | 会社案内（代表メッセージ／企業理念／会社概要／アクセス） |
| `service.html` | 事業内容（5事業の詳細／ご依頼の流れ） |
| `works.html` | 施工実績（カテゴリー絞り込み付き・架空サンプル6件） |
| `contact.html` | お問い合わせ（電話／フォーム。デモのため送信・発信は無効） |

## ディレクトリ構成

```
src/
  parts/      共通パーツ（head・header・footer・CTA・実績カード等）※WPの parts/ に相当
  pages/      各ページ本文                                   ※WPの templates/ に相当
  data/company.json  会社情報（display:false の項目は出力されません）
assets/
  css/style.css  デザイントークン（:root）＋全スタイル
  js/main.js     アニメーション・メニュー・デモ用の無効化処理（ライブラリ不使用）
  img/           ロゴ（名刺から切り出し・背景透過）、photo/ に仮イメージ画像
tools/
  extract_logo.py     名刺画像からロゴを切り出すスクリプト
  generate_images.py  仮イメージ画像の生成スクリプト
build.mjs     src/ を組み立ててルートの *.html を出力
deploy/htaccess.sample  Basic認証の設定例
```

**編集の流れ：** `src/` 内を編集 → `node build.mjs` → ルートの `*.html` が更新されます（依存パッケージ不要）。
ルートの `*.html` を直接編集すると、次回ビルドで上書きされます。

## よく変更する箇所

- **会社情報**：`src/data/company.json`。設立・資本金・従業員数・許可番号は現在「確認中」です。
  個人の携帯番号・メールアドレスはデータとして保持していますが `display:false` のため表示されません。
- **紹介文・事業説明・理念**：`src/pages/*.html`（すべてサンプル文です）
- **施工実績の追加**：`src/parts/works-cards.html` の `<li class="work-card">` を複製して差し替え
- **写真**：`assets/img/photo/` の同名ファイルを実際の現場写真に差し替え（推奨サイズは現ファイルと同じ）。
  現在の画像は外部素材を使わずにプログラムで生成した**仮イメージ**です。本番では自社の現場写真か、
  購入したストックフォト（PIXTA、Adobe Stock など）への差し替えを推奨します。
- **色**：`assets/css/style.css` 冒頭の `:root`（`--c-orange: #FF7400` 等）

## デモとしての安全対策

- 全ページ上部に「非公式・提案用デモサイト」のバナーを固定表示し、フッターにも明記
- 施工実績はすべて「SAMPLE」「架空」と表示
- お問い合わせフォームは入力チェックのみ行い、送信しない（外部へのリクエストもなし）
- 電話番号は `tel:` リンクにせず、タップするとデモの案内を表示
- `<meta name="robots" content="noindex">` と `robots.txt` で検索エンジンにインデックスさせない

## デモURLのパスワード保護（提案）

| 方法 | 手順・特徴 | おすすめ度 |
| --- | --- | --- |
| **エックスサーバーのBasic認証** | サーバーパネル →「アクセス制限」でディレクトリにID/パスワードを設定（`deploy/htaccess.sample` 参照）。本番予定のサーバーで確認でき、追加費用なし | ◎ |
| Cloudflare Pages ＋ Cloudflare Access | 無料枠あり。特定のメールアドレスだけ閲覧できるワンタイムコード認証 | ○ |
| Netlify（パスワード保護） | サイト全体のパスワード保護は有料プラン | △ |

※GitHub Pages ではパスワード保護ができないため、デモの公開先には向きません。

## WordPress（ブロックテーマ）への移行方針

デザインが決まった段階で、エックスサーバー上のWordPress用のオリジナルブロックテーマとして作り直す予定です。

- `:root` のデザイントークン → `theme.json`（カラーパレット・フォント・余白）
- `src/parts/header.html` / `footer.html` → `parts/header.html` / `parts/footer.html`
- `src/pages/*.html` の各セクション → `patterns/`（ブロックパターン）として登録し、管理画面から文章を編集可能に
- 施工実績 → カスタム投稿タイプ「施工実績」＋タクソノミー（工事種別）＋クエリーループ
- お問い合わせ → Contact Form 7 等のプラグインに置き換え（reCAPTCHA 対応）
- `main.js` / `style.css` → `functions.php` から `wp_enqueue_*` で読み込み
- 会社情報（`company.json`）→ サイト設定やカスタムフィールドで管理

## 再生成スクリプト

```bash
python3 tools/extract_logo.py source/meishi-front.jpg source/meishi-back.jpg  # ロゴの再切り出し（名刺画像は個人情報を含むためリポジトリに含めていません）
python3 tools/generate_images.py                                               # 仮イメージ画像の再生成
node build.mjs                                                                 # HTMLの再ビルド
```
