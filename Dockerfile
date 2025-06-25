# ベースイメージとして軽量なPythonイメージを選択
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# requirements.txtをコピーしてライブラリをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY . .

# アプリケーションのポートを公開
EXPOSE 5000

# コンテナ起動時にFlaskアプリケーションを実行
# gunicornなどの本番用WSGIサーバーを使うのが推奨されるが、ここではシンプルにFlaskの開発サーバーを使用
CMD ["flask", "run", "--host=0.0.0.0"]
