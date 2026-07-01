# 母子手帳 ワクチン接種記録抽出 (MCHHB)

母子健康手帳の画像からワクチン接種記録を抽出し、**Excel / PDF** の接種記録表として出力する Web アプリです。

## パイプライン

```
画像アップロード
    ↓
Claude Vision API（OCR）
    ↓
Claude API（JSON 整形・推測禁止）
    ↓
フィールドクリーンアップ（隣ページノイズ除去など）
    ↓
Excel + PDF を ZIP でダウンロード
```

**使用 API:** [Anthropic Claude API](https://docs.anthropic.com/) のみ（`claude-sonnet-4-6` 推奨）

## 設計方針

- **推測しない** — 画像・OCR テキストにない情報は `null`
- **要確認フラグ** — 曖昧な項目は `needs_review: true`
- **列を混ぜない** — メーカー／ロット、医療機関、備考を別フィールドに分離
- ワクチン履歴は誤りが致命的なため、**空欄を許容**する
- **出力表は記録があるワクチンのみ** — 未接種のテンプレート行は省略
- **テンプレートにないワクチン**（RSV など）は行を追加して記録

## 出力

Web からダウンロードされる ZIP には次の 2 ファイルが含まれます。

| ファイル | 内容 |
|---|---|
| `vaccination_record.xlsx` | 接種記録表（Excel） |
| `vaccination_record.pdf` | 接種記録表（PDF・セル折り返し対応） |

## セットアップ

### 1. Python 環境

```bash
cd MCHHB
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Claude API キー

[Anthropic Console](https://console.anthropic.com/) で API キーを取得し、`.env` に設定します。

```env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6
```

> **注意:** `.env` は Git にコミットしないでください（`.gitignore` で除外済み）。

## 起動

```bash
source .venv/bin/activate
uvicorn app:app --reload --port 8000
```

ブラウザで http://localhost:8000 を開きます。

## 使い方（Web）

1. 母子手帳の「予防接種の記録」ページ画像をアップロード（複数枚可）
2. 「抽出してダウンロード」をクリック
3. `vaccination_record.zip`（Excel + PDF）がダウンロードされます
4. 内容を確認し、必要に応じて Excel で修正してください

## 使い方（CLI）

```bash
python main.py photo1.jpg photo2.jpg -o output/
# または
python main.py -d ./images/ -o output/ --name "山田 太郎"
```

`output/vaccination_record.xlsx` と `output/vaccination_record.pdf` が生成されます。

## プロジェクト構成

```
MCHHB/
  app.py                    # FastAPI Web アプリ
  main.py                   # CLI（Excel / PDF 出力）
  static/                   # フロントエンド
  templates/
  src/mchhb/
    claude_client.py        # Claude API 共通クライアント
    claude_vision.py        # Claude Vision OCR
    formatter.py            # Claude による JSON 整形
    pipeline.py             # パイプライン統合
    field_cleanup.py        # 隣ページノイズ除去
    table_rows.py           # 出力表の行フィルタ・追加
    excel_export.py         # Excel 出力
    pdf_export.py           # PDF 出力
    file_export.py          # ZIP 一括生成
    models.py               # Pydantic スキーマ
```

## 注意事項

- 手書き・画質・隣ページの文字混入によって精度が変わります
- **必ず出力ファイルを目視で最終確認**してください
- 個人情報を含む画像の取り扱いにご注意ください
- API キーは `.env` にのみ保存し、リポジトリに含めないでください

## ライセンス

Private project.
