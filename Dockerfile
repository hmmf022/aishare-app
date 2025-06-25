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

# -w 4: 4つのワーカープロセスを起動（同時に4つのリクエストを処理できる）
# -b 0.0.0.0:5000: すべてのネットワークインターフェースの5000番ポートで待機
# app:app: app.py ファイルの中の app という名前のFlaskインスタンスを実行
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
