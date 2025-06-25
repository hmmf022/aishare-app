import sqlite3
import os

DATA_DIR = 'data'
DB_PATH = os.path.join(DATA_DIR, 'aishare.db')

# --- データベースファイルの再生成 ---
print("--- Database Reset Script (v2: with Categories) ---")
os.makedirs(DATA_DIR, exist_ok=True)
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"[OK] Removed existing database file: {DB_PATH}")
print(f"Creating a new database file at: {DB_PATH}")

connection = sqlite3.connect(DB_PATH)
connection.execute("PRAGMA foreign_keys = ON")
cursor = connection.cursor()

# --- テーブルの作成 ---
print("Creating tables with new schema...")

# ★【新規】categoriesテーブル
cursor.execute('''
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
''')

# postsテーブル (変更なし)
cursor.execute('''
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_visible INTEGER DEFAULT 1 NOT NULL
)
''')

# ★【変更】tagsテーブルにcategory_idを追加
cursor.execute('''
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category_id INTEGER NOT NULL,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
)
''')

# 中間テーブルやその他は変更なし
cursor.execute('''
CREATE TABLE post_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL, tag_id INTEGER NOT NULL,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
)
''')
cursor.execute('''
CREATE TABLE likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL, user_uuid TEXT NOT NULL,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
    UNIQUE(post_id, user_uuid)
)
''')
cursor.execute('''
CREATE TABLE favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL, user_uuid TEXT NOT NULL,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
    UNIQUE(post_id, user_uuid)
)
''')

print("[OK] All tables created successfully.")

# --- ★【変更】カテゴリ構造化された初期データ ---
print("Inserting initial categorized data...")

categorized_tags = {
    "業務用途": ["調査・リサーチ", "業務効率化", "メール・文書作成", "議事録作成", "会議準備", "タスク管理", "マニュアル作成"],
    "学習・知識習得系": ["社内研修", "勉強・自己学習", "資格対策"],
    "開発・技術": ["コードレビュー", "技術調査", "API設計", "インフラ構成"],
    "クリエイティブ・発信": ["ネーミング案", "キャッチコピー", "SNS投稿案", "資料作成補助"],
    "コミュニケーション・サポート": ["Slack応答案", "顧客対応文案", "トラブル対応"],
    "プライベート活用": ["旅行計画", "健康・栄養", "子育て相談", "ライフハック"]
}

for category_name, tags in categorized_tags.items():
    cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
    category_id = cursor.lastrowid
    for tag_name in tags:
        cursor.execute("INSERT INTO tags (name, category_id) VALUES (?, ?)", (tag_name, category_id))

print("[OK] Initial data inserted.")
connection.commit()
connection.close()

print("\n---------------------------------")
print("Database has been successfully reset with the new categorized structure.")
print("You can now run the application.")
print("---------------------------------")
