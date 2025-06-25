import sqlite3

DB_PATH = 'data/aishare.db'
print(f"Connecting to database at {DB_PATH}...")

try:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # postsテーブルに is_visible カラムを追加
    # DEFAULT 1 とすることで、既存の投稿はすべて「表示」状態になる
    cursor.execute("ALTER TABLE posts ADD COLUMN is_visible INTEGER DEFAULT 1 NOT NULL")

    connection.commit()
    print("Successfully added 'is_visible' column to 'posts' table.")

except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column 'is_visible' already exists. No changes made.")
    else:
        print(f"An error occurred: {e}")
finally:
    if connection:
        connection.close()
