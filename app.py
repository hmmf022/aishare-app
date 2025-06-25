import sqlite3
import uuid
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, jsonify, g
from collections import defaultdict

app = Flask(__name__)
DATABASE = 'data/aishare.db'

# ... (get_db, close_connection, manage_user_uuid, set_user_uuid_cookie, get_user_uuid は変更なし) ...
def get_db():
    db = getattr(g, '_database', None)
    if db is None: db = g._database = sqlite3.connect(DATABASE); db.row_factory = sqlite3.Row
    return db
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()
@app.before_request
def manage_user_uuid():
    if 'user_uuid' not in request.cookies: g.user_uuid_to_set = str(uuid.uuid4())
    else: g.user_uuid_to_set = None
@app.after_request
def set_user_uuid_cookie(response):
    if hasattr(g, 'user_uuid_to_set') and g.user_uuid_to_set: response.set_cookie('user_uuid', g.user_uuid_to_set, max_age=365*24*60*60)
    return response
def get_user_uuid(): return request.cookies.get('user_uuid', g.user_uuid_to_set)

# ★【新規】カテゴリ化されたタグを取得するヘルパー関数
def get_categorized_tags():
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT c.id as category_id, c.name as category_name, t.id as tag_id, t.name as tag_name
        FROM categories c
        JOIN tags t ON c.id = t.category_id
        ORDER BY c.id, t.id
    """
    rows = cursor.execute(query).fetchall()

    # データをカテゴリごとにグループ化
    categorized = defaultdict(list)
    for row in rows:
        categorized[row['category_name']].append({'id': row['tag_id'], 'name': row['tag_name']})

    # 整形してリストとして返す
    return [{'category_name': name, 'tags': tags} for name, tags in categorized.items()]

# --- ルート定義 ---

@app.route('/')
def index():
    # ... (この関数のロジックは長いので、下でまとめて示します) ...
    # （※基本的にはテンプレートに渡すall_tagsをcategorized_tagsに変えるだけ）
    db = get_db()
    cursor = db.cursor()
    user_uuid = get_user_uuid()

    search_keyword = request.args.get('q', '')
    selected_date = request.args.get('date', '')
    selected_tag = request.args.get('tag', '')
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')

    if sort_by not in ['created_at', 'likes_count']: sort_by = 'created_at'
    if order.lower() not in ['asc', 'desc']: order = 'desc'

    params = [user_uuid, user_uuid]
    base_query = """
        WITH PostWithTags AS (...)
        SELECT ...
    """

    # base_queryのWITH句とSELECT句は省略せずに記述
    full_base_query = f"""
        WITH PostWithTags AS (
            SELECT p.id, GROUP_CONCAT(t.name) as tags
            FROM posts p
            LEFT JOIN post_tags pt ON p.id = pt.post_id
            LEFT JOIN tags t ON pt.tag_id = t.id
            GROUP BY p.id
        )
        SELECT
            p.id, p.url, p.title, p.created_at, p.is_visible, pwt.tags,
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id) AS likes_count,
            (SELECT COUNT(*) FROM favorites WHERE post_id = p.id AND user_uuid = ?) > 0 AS is_favorited,
            (SELECT COUNT(*) FROM likes WHERE post_id = p.id AND user_uuid = ?) > 0 AS is_liked
        FROM posts p
        LEFT JOIN PostWithTags pwt ON p.id = pwt.id
    """

    where_clauses = ["p.is_visible = 1"]
    if search_keyword:
        where_clauses.append("(p.title LIKE ? OR (pwt.tags IS NOT NULL AND pwt.tags LIKE ?))")
        params.extend([f'%{search_keyword}%', f'%{search_keyword}%'])
    if selected_date:
        where_clauses.append("DATE(p.created_at) = ?")
        params.append(selected_date)
    if selected_tag:
        where_clauses.append("(pwt.tags IS NOT NULL AND pwt.tags LIKE ?)")
        params.append(f'%{selected_tag}%')

    full_query = full_base_query + " WHERE " + " AND ".join(where_clauses) + f" ORDER BY {sort_by} {order}"

    posts = cursor.execute(full_query, tuple(params)).fetchall()

    return render_template('index.html',
                           posts=posts,
                           categorized_tags=get_categorized_tags(), # ★変更
                           search_keyword=search_keyword, selected_date=selected_date,
                           selected_tag=selected_tag, current_sort=sort_by, current_order=order)


@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        # ... (POST処理のロジックは変更なし) ...
        db = get_db()
        cursor = db.cursor()
        url = request.form.get('url')
        tag_ids = request.form.getlist('tags')
        if url and tag_ids:
            title = None
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                res = requests.get(url, timeout=5, headers=headers)
                res.raise_for_status()
                soup = BeautifulSoup(res.content, 'html.parser')
                if soup.title and soup.title.string: title = soup.title.string.strip()
            except requests.exceptions.RequestException as e:
                print(f"[Info] Could not fetch title for '{url}'. Reason: {e}. Using URL as fallback title.")
            if title is None: title = url
            try:
                cursor.execute("INSERT OR IGNORE INTO posts (url, title) VALUES (?, ?)", (url, title))
                post_id = cursor.lastrowid if cursor.rowcount > 0 else cursor.execute("SELECT id FROM posts WHERE url = ?", (url,)).fetchone()['id']
                for tag_id in tag_ids:
                    cursor.execute("INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)", (post_id, int(tag_id)))
                db.commit()
            except sqlite3.Error as e:
                db.rollback()
                print(f"Database error on post submission: {e}")
            return redirect(url_for('index'))
    # ★GETリクエストの場合、カテゴリ化されたタグを渡す
    return render_template('new.html', categorized_tags=get_categorized_tags())

# ... (like, favorite, favorites, admin, toggle_visibility, delete_post, edit_title は変更なし) ...
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
        WHERE f.user_uuid = ? AND p.is_visible = 1
        GROUP BY p.id ORDER BY f.id DESC
    """
    posts = cursor.execute(query, (user_uuid, user_uuid)).fetchall()
    return render_template('favorites.html', posts=posts)
@app.route('/admin')
def admin():
    db = get_db()
    cursor = db.cursor()
    posts = cursor.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    return render_template('admin.html', posts=posts)
@app.route('/admin/toggle_visibility/<int:post_id>', methods=['POST'])
def toggle_visibility(post_id):
    db = get_db()
    cursor = db.cursor()
    current_status = cursor.execute("SELECT is_visible FROM posts WHERE id = ?", (post_id,)).fetchone()
    if current_status:
        new_status = 0 if current_status['is_visible'] == 1 else 1
        cursor.execute("UPDATE posts SET is_visible = ? WHERE id = ?", (new_status, post_id))
        db.commit()
    return redirect(url_for('admin'))
@app.route('/admin/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM post_tags WHERE post_id = ?", (post_id,))
        cursor.execute("DELETE FROM likes WHERE post_id = ?", (post_id,))
        cursor.execute("DELETE FROM favorites WHERE post_id = ?", (post_id,))
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        db.commit()
    except sqlite3.Error as e: db.rollback(); print(f"Failed to delete post: {e}")
    return redirect(url_for('admin'))
@app.route('/admin/edit_title/<int:post_id>', methods=['POST'])
def edit_title(post_id):
    if not request.is_json: return jsonify({"success": False, "error": "Invalid request: JSON required"}), 400
    data = request.get_json()
    new_title = data.get('title')
    if not new_title: return jsonify({"success": False, "error": "New title cannot be empty"}), 400
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE posts SET title = ? WHERE id = ?", (new_title, post_id))
        db.commit()
        if cursor.rowcount == 1: return jsonify({"success": True, "new_title": new_title})
        else: return jsonify({"success": False, "error": "Post not found or no change made"}), 404
    except sqlite3.Error as e: return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
