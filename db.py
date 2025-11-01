# use sqlite3 to create a database
import sqlite3
import logging

logger = logging.getLogger(__name__)

def init_db(db_name="app.db"):
    logger.info("Initializing database")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            link TEXT,
            name TEXT
        )
    ''')

    # Create posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            link TEXT,
            user_id TEXT,
            name TEXT,
            content TEXT,
            timestamp TEXT
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized with users and posts tables.")

def add_user(id, link, name=""):
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (id, link, name) VALUES (?, ?, ?)''', (id, link, name))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        logger.warning("User already exists")
        pass

def get_user(id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM users WHERE id = ?''', (id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_name(id, name=""):
    if not name:
        return
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE users SET name = ? WHERE id = ?''', (name, id))
    conn.commit()
    conn.close()

def add_post(id, link, user_id, name, content, timestamp):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO posts (id, link, user_id, name, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)''', (id, link, user_id, name, content, timestamp))
    conn.commit()
    conn.close()

def get_post(id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM posts WHERE id = ?''', (id,))
    post = cursor.fetchone()
    conn.close()
    return post

def get_posts_by_user(user_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM posts WHERE user_id = ?''', (user_id,))
    posts = cursor.fetchall()
    conn.close()
    return posts

def get_all_posts():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM posts''')
    posts = cursor.fetchall()
    conn.close()
    return posts

def get_all_users():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM users''')
    users = cursor.fetchall()
    conn.close()
    return users
