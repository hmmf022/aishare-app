import sqlite3
import os

# データベースファイルが保存されるディレクトリ
DATA_DIR = 'data'
# データベースファイルのパス
DB_PATH = os.path.join(DATA_DIR, 'aishare.db')

# --- データベースファイルの再生成 ---
print("--- Database Reset Script ---")

# dataディレクトリがなければ作成
os.makedirs(DATA_DIR, exist_ok=True)

# 既存のデータベースファイルがあれば削除
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"[OK] Removed existing database file: {DB_PATH}")

print(f"Creating a new database file at: {DB_PATH}")

# データベースに接続（ファイルがなければ新規作成される）
connection = sqlite3.connect(DB_PATH)
# 外部キー制約を有効にする
connection.execute("PRAGMA foreign_keys = ON")
cursor = connection.cursor()

# --- テーブルの作成 ---
print("Creating tables...")

# postsテーブル (is_visible列を最初から含める)
cursor.execute('''
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_visible INTEGER DEFAULT 1 NOT NULL
)
''')

# tagsテーブル
cursor.execute('''
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
''')

# post_tags 中間テーブル (ON DELETE CASCADE を追加)
cursor.execute('''
CREATE TABLE post_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
)
''')

# likesテーブル (ON DELETE CASCADE を追加)
cursor.execute('''
CREATE TABLE likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_uuid TEXT NOT NULL,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
    UNIQUE(post_id, user_uuid)
)
''')

# favoritesテーブル (ON DELETE CASCADE を追加)
cursor.execute('''
CREATE TABLE favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_uuid TEXT NOT NULL,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
    UNIQUE(post_id, user_uuid)
)
''')

print("[OK] All tables created successfully.")

# --- 初期データの投入 ---
print("Inserting initial data...")

initial_tags = ["質問", "アイデア出し", "要約", "翻訳", "コード生成", "デバッグ", "文章校正", "家事・育児", "その他"]
for tag_name in initial_tags:
    cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))

print(f"[OK] Inserted {len(initial_tags)} initial tags.")

# 変更をコミットして接続を閉じる
connection.commit()
connection.close()

print("\n---------------------------------")
print("Database has been successfully reset and initialized.")
print("All previous data has been erased.")
print("You can now run the application.")
print("---------------------------------")
