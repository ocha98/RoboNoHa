## これは何？
Azure FunctionsのTimer Triggerで動作させるコード。

## 技術要素
- Azure Funcions: コードの定期実行
- Cloudflare R2: モデルの保存場所

## 必要環境変数

- AWS_ACCESS_KEY_ID: S3のアクセスキー
- AWS_SECRET_ACCESS_KEY: S3のアクセスシークレット
- AWS_ENDPOINT_URL: S3のエンドポイントURL
- AWS_DEFAULT_REGION: S3のリージョン
- S3_BUCKET: markovifyのモデルが保存されいるバケット名
- CHAIN_FILE_KEY: markovifyのモデルファイルのキー
- BLUESKY_SESSION: Blueskyのセッションキー

Cloudflare R2はAWS S3と互換性があります。そのため、実際にはAWS S3ではなくCloudflare R2を使用しています。

Blueskyのセッションキーは`localtools/bluesky.py`に取得のコードがあります。
