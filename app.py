import sqlite3
import uuid
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, jsonify, g

app = Flask(__name__)
DATABASE = 'data/aishare.db'

# --- データベース接続 ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- ユーザーID管理 ---
@app.before_request
def manage_user_uuid():
    if 'user_uuid' not in request.cookies:
        g.user_uuid_to_set = str(uuid.uuid4())
    else:
        g.user_uuid_to_set = None

@app.after_request
def set_user_uuid_cookie(response):
    if hasattr(g, 'user_uuid_to_set') and g.user_uuid_to_set:
        response.set_cookie('user_uuid', g.user_uuid_to_set, max_age=365*24*60*60)
    return response

def get_user_uuid():
    return request.cookies.get('user_uuid', g.user_uuid_to_set)

# --- ルート定義 ---

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    user_uuid = get_user_uuid()

    search_keyword = request.args.get('q', '')
    selected_tag = request.args.get('tag', '')
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')

    if sort_by not in ['created_at', 'likes_count']:
        sort_by = 'created_at'
    if order.lower() not in ['asc', 'desc']:
        order = 'desc'

    params = [user_uuid, user_uuid]
    base_query = f"""
        WITH PostWithTags AS (
            SELECT p.id, GROUP_CONCAT(t.name) as tags
            FROM posts p
            LEFT JOIN post_tags pt ON p.id = pt.post_id
            LEFT JOIN tags t ON pt.tag_id = t.id
            GROUP BY p.id
        )
        SELECT
            p.id, p.url, p.title, p.created_at, pwt.tags,
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id) AS likes_count,
            (SELECT COUNT(*) FROM favorites WHERE post_id = p.id AND user_uuid = ?) > 0 AS is_favorited,
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id AND user_uuid = ?) > 0 AS is_liked
        FROM posts p
        LEFT JOIN PostWithTags pwt ON p.id = pwt.id
    """
    where_clauses = []
    if search_keyword:
        where_clauses.append("(p.title LIKE ? OR (pwt.tags IS NOT NULL AND pwt.tags LIKE ?))")
        params.extend([f'%{search_keyword}%', f'%{search_keyword}%'])
    if selected_tag:
        where_clauses.append("(pwt.tags IS NOT NULL AND pwt.tags LIKE ?)")
        params.append(f'%{selected_tag}%')

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)
    base_query += f" ORDER BY {sort_by} {order}"

    posts = cursor.execute(base_query, tuple(params)).fetchall()
    all_tags = cursor.execute("SELECT * FROM tags ORDER BY name").fetchall()

    return render_template('index.html',
                           posts=posts, all_tags=all_tags,
                           search_keyword=search_keyword, current_sort=sort_by,
                           current_order=order, selected_tag=selected_tag)

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        url = request.form.get('url')
        tag_ids = request.form.getlist('tags')
        if url and tag_ids:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(url, timeout=5, headers=headers)
                res.raise_for_status()
                soup = BeautifulSoup(res.content, 'html.parser')
                title = soup.title.string.strip() if soup.title else "タイトルなし"

                cursor.execute("INSERT OR IGNORE INTO posts (url, title) VALUES (?, ?)", (url, title))
                post_id = cursor.lastrowid if cursor.rowcount > 0 else cursor.execute("SELECT id FROM posts WHERE url = ?", (url,)).fetchone()['id']

                for tag_id in tag_ids:
                    cursor.execute("INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)", (post_id, int(tag_id)))
                db.commit()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching URL: {e}")
            except sqlite3.Error as e:
                print(f"Database error: {e}")
            return redirect(url_for('index'))

    tags = cursor.execute("SELECT * FROM tags").fetchall()
    return render_template('new.html', tags=tags)

@app.route('/like/<int:post_id>', methods=['POST'])
def like(post_id):
    user_uuid = get_user_uuid()
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO likes (post_id, user_uuid) VALUES (?, ?)", (post_id, user_uuid))
        db.commit()
        liked = True
    except sqlite3.IntegrityError:
        cursor.execute("DELETE FROM likes WHERE post_id = ? AND user_uuid = ?", (post_id, user_uuid))
        db.commit()
        liked = False
    likes_count = cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,)).fetchone()[0]
    return jsonify({'success': True, 'liked': liked, 'count': likes_count})

@app.route('/favorite/<int:post_id>', methods=['POST'])
def favorite(post_id):
    user_uuid = get_user_uuid()
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO favorites (post_id, user_uuid) VALUES (?, ?)", (post_id, user_uuid))
        db.commit()
        favorited = True
    except sqlite3.IntegrityError:
        cursor.execute("DELETE FROM favorites WHERE post_id = ? AND user_uuid = ?", (post_id, user_uuid))
        db.commit()
        favorited = False
    return jsonify({'success': True, 'favorited': favorited})

@app.route('/favorites')
def favorites():
    user_uuid = get_user_uuid()
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT
            p.id, p.url, p.title, p.created_at,
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id) AS likes_count,
            1 AS is_favorited,
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id AND user_uuid = ?) > 0 AS is_liked,
            GROUP_CONCAT(t.name) as tags
        FROM posts p
        JOIN post_tags pt ON p.id = pt.post_id
        JOIN tags t ON pt.tag_id = t.id
        JOIN favorites f ON p.id = f.post_id
        WHERE f.user_uuid = ?
        GROUP BY p.id ORDER BY f.id DESC
    """
    posts = cursor.execute(query, (user_uuid, user_uuid)).fetchall()
    return render_template('favorites.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
