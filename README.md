# 母子手帳 ワクチン接種記録抽出 (MCHHB) — MVP

母子健康手帳の画像からワクチン接種記録を抽出し、ユーザーが確認・修正できる Web アプリです。

## パイプライン

```
画像アップロード
    ↓
Google Document AI（OCR）
    ↓
OpenAI（JSON 整形・推測禁止）
    ↓
画面上で確認・修正 → JSON ダウンロード
```

## 設計方針

- **推測しない** — OCR テキストにない情報は `null`
- **要確認フラグ** — 曖昧な項目は `needs_review: true`
- ワクチン履歴は誤りが致命的なため、空欄を許容する

## 出力 JSON 例

```json
{
  "child_name": null,
  "vaccinations": [
    {
      "vaccine_name": "小児用肺炎球菌",
      "dose_number": "1回目",
      "date": "2024-06-10",
      "lot_number": null,
      "clinic": null,
      "confidence": "medium",
      "needs_review": true
    }
  ]
}
```

## セットアップ

### 1. Python 環境

```bash
cd MCHHB
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. OpenAI API キー

`.env` に `OPENAI_API_KEY` を設定。

### 3. Google Document AI

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. Document AI API を有効化
3. **Document OCR** プロセッサを作成（日本語手書き対応が必要なら適宜チューニング）
4. サービスアカウントを作成し JSON キーをダウンロード
5. `.env` に以下を設定:
   - `GCP_PROJECT_ID`
   - `GCP_LOCATION`（例: `us` または `asia-northeast1`）
   - `DOCUMENT_AI_PROCESSOR_ID`
   - `GOOGLE_APPLICATION_CREDENTIALS`（JSON キーのパス）

## 起動

```bash
source .venv/bin/activate
uvicorn app:app --reload --port 8000
```

ブラウザで http://localhost:8000 を開く。

## 使い方

1. 母子手帳の「予防接種の記録」ページ画像をアップロード（複数枚可）
2. 「抽出を開始」をクリック
3. 結果テーブルで内容を確認・修正
   - 黄色の行 = 要確認（`needs_review: true`）
   - 不明な項目は空欄のまま
4. 「JSON をダウンロード」で確定データを保存

## プロジェクト構成

```
MCHHB/
  app.py                  # FastAPI Web アプリ
  static/                 # フロントエンド
  src/mchhb/
    ocr.py                # Google Document AI OCR
    formatter.py          # OpenAI JSON 整形
    pipeline.py           # パイプライン統合
    models.py             # Pydantic スキーマ
  main.py                 # CLI（旧版・Excel 出力）
```

## 注意事項

- 手書き・画質によって OCR 精度が変わります
- **必ずユーザーが最終確認**してください
- 個人情報を含む画像の取り扱いにご注意ください
