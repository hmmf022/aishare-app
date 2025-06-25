import sqlite3

# データベースファイルは data/ フォルダに作成
DB_PATH = 'data/aishare.db'

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# postsテーブル
cursor.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# tagsテーブル
cursor.execute('''
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
''')

# post_tags 中間テーブル
cursor.execute('''
CREATE TABLE IF NOT EXISTS post_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    tag_id INTEGER,
    FOREIGN KEY(post_id) REFERENCES posts(id),
    FOREIGN KEY(tag_id) REFERENCES tags(id)
)
''')

# likesテーブル
cursor.execute('''
CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    user_uuid TEXT NOT NULL,
    FOREIGN KEY(post_id) REFERENCES posts(id),
    UNIQUE(post_id, user_uuid)
)
''')

# favoritesテーブル
cursor.execute('''
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    user_uuid TEXT NOT NULL,
    FOREIGN KEY(post_id) REFERENCES posts(id),
    UNIQUE(post_id, user_uuid)
)
''')

# タグの初期データを投入
initial_tags = ["アイデア出し", "要約", "翻訳", "コード生成", "デバッグ", "文章校正"]
for tag_name in initial_tags:
    cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))

connection.commit()
connection.close()

print("Database initialized successfully.")
