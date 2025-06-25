import sqlite3
import uuid
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, g

app = Flask(__name__)

# データベースパス
DATABASE = 'data/aishare.db'

# データベース接続
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # カラム名でアクセスできるようにする
    return db

# リクエスト終了時にデータベース接続を閉じる
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# 匿名ユーザーIDをCookieで管理
@app.before_request
def manage_user_uuid():
    if 'user_uuid' not in request.cookies:
        # このレスポンスでCookieを設定するため、gに保存しておく
        g.user_uuid_to_set = str(uuid.uuid4())
    else:
        g.user_uuid_to_set = None

@app.after_request
def set_user_uuid_cookie(response):
    if hasattr(g, 'user_uuid_to_set') and g.user_uuid_to_set:
        response.set_cookie('user_uuid', g.user_uuid_to_set, max_age=365*24*60*60) # 1年間有効
    return response

def get_user_uuid():
    return request.cookies.get('user_uuid', g.user_uuid_to_set)

# F-01: 事例投稿機能 / F-02: 一覧表示機能 / F-03: 検索機能
@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    cursor = db.cursor()
    user_uuid = get_user_uuid()

    # (F-01) 投稿処理
    if request.method == 'POST':
        url = request.form.get('url')
        tag_ids = request.form.getlist('tags')
        if url and tag_ids:
            try:
                # P-01: タイムアウト設定
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(url, timeout=5, headers=headers)
                res.raise_for_status()
                # S-01: タイトル取得
                soup = BeautifulSoup(res.content, 'html.parser')
                title = soup.title.string.strip() if soup.title else "タイトルなし"

                # DBに保存
                cursor.execute("INSERT OR IGNORE INTO posts (url, title) VALUES (?, ?)", (url, title))
                # 既に存在する場合はIDを取得、新規の場合はlastrowidを取得
                if cursor.rowcount > 0:
                    post_id = cursor.lastrowid
                else:
                    post_id = cursor.execute("SELECT id FROM posts WHERE url = ?", (url,)).fetchone()['id']

                for tag_id in tag_ids:
                    cursor.execute("INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)", (post_id, int(tag_id)))
                db.commit()

            except requests.exceptions.RequestException as e:
                print(f"Error fetching URL: {e}") # 本来はエラーページなどを表示
            except sqlite3.Error as e:
                print(f"Database error: {e}")

            return redirect(url_for('index'))

    # (F-02 & F-03) 一覧表示 & 検索 (★修正箇所)
    search_keyword = request.args.get('q', '')

    # WITH句を使って、先にタグを集約したテーブルを作成してから検索する
    query = """
        WITH PostWithTags AS (
            SELECT
                p.id,
                GROUP_CONCAT(t.name) as tags
            FROM posts p
            LEFT JOIN post_tags pt ON p.id = pt.post_id
            LEFT JOIN tags t ON pt.tag_id = t.id
            GROUP BY p.id
        )
        SELECT
            p.id, p.url, p.title, p.created_at,
            pwt.tags,
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id) AS likes_count,
            (SELECT COUNT(*) FROM favorites WHERE post_id = p.id AND user_uuid = ?) > 0 AS is_favorited,
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id AND user_uuid = ?) > 0 AS is_liked
        FROM posts p
        JOIN PostWithTags pwt ON p.id = pwt.id
        WHERE p.title LIKE ? OR pwt.tags LIKE ?
        ORDER BY p.created_at DESC
    """

    posts = cursor.execute(query, (user_uuid, user_uuid, f'%{search_keyword}%', f'%{search_keyword}%')).fetchall()

    tags = cursor.execute("SELECT * FROM tags").fetchall()

    return render_template('index.html', posts=posts, tags=tags, search_keyword=search_keyword)

# F-04: いいね機能
@app.route('/like/<int:post_id>', methods=['POST'])
def like(post_id):
    user_uuid = get_user_uuid()
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO likes (post_id, user_uuid) VALUES (?, ?)", (post_id, user_uuid))
        db.commit()
        liked = True
    except sqlite3.IntegrityError: # 重複いいねの場合
        cursor.execute("DELETE FROM likes WHERE post_id = ? AND user_uuid = ?", (post_id, user_uuid))
        db.commit()
        liked = False

    likes_count = cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,)).fetchone()[0]
    return jsonify({'success': True, 'liked': liked, 'count': likes_count})

# F-05: お気に入り機能
@app.route('/favorite/<int:post_id>', methods=['POST'])
def favorite(post_id):
    user_uuid = get_user_uuid()
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO favorites (post_id, user_uuid) VALUES (?, ?)", (post_id, user_uuid))
        db.commit()
        favorited = True
    except sqlite3.IntegrityError: # 重複お気に入りの場合
        cursor.execute("DELETE FROM favorites WHERE post_id = ? AND user_uuid = ?", (post_id, user_uuid))
        db.commit()
        favorited = False
    return jsonify({'success': True, 'favorited': favorited})

# F-06: お気に入り一覧機能
@app.route('/favorites')
def favorites():
    user_uuid = get_user_uuid()
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT
            p.id, p.url, p.title, p.created_at,
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id) AS likes_count,
            1 AS is_favorited, -- お気に入り一覧なので常にtrue
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id AND user_uuid = ?) > 0 AS is_liked,
            GROUP_CONCAT(t.name) as tags
        FROM posts p
        JOIN post_tags pt ON p.id = pt.post_id
        JOIN tags t ON pt.tag_id = t.id
        JOIN favorites f ON p.id = f.post_id
        WHERE f.user_uuid = ?
        GROUP BY p.id
        ORDER BY f.id DESC -- お気に入りに追加した順
    """
    posts = cursor.execute(query, (user_uuid, user_uuid)).fetchall()
    return render_template('favorites.html', posts=posts)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
