import sqlite3
from datetime import datetime
from flask_login import UserMixin


class DB:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


class User(UserMixin):
    def __init__(self, id, username, email, password, bio=None, profile_pic=None):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.bio = bio
        self.profile_pic = profile_pic

    @classmethod
    def get_user_by_email(cls, email, db):
        db.cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user_data = db.cursor.fetchone()
        if user_data:
            return cls(*user_data)
        return None

    @classmethod
    def create_user(cls, username, email, password, db):
        existing_user = cls.get_user_by_email(email, db)
        if existing_user:
            raise ValueError("Email already exists")
        
        db.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                          (username, email, password))
        db.commit()
        return cls.get_user_by_email(email, db)
    @classmethod
    def update_user(cls, user_id, username, email, password, db):
        existing_user = cls.get_user_by_id(user_id, db)
        if existing_user:
            existing_user.username = username
            existing_user.email = email
            existing_user.password = password
            db.cursor.execute("UPDATE users SET username = ?, email = ?, password = ? WHERE id = ?",
                              (existing_user.username, existing_user.email, existing_user.password, existing_user.id))
            db.commit()
            return existing_user
        return None
    @classmethod
    def get_user_by_id(cls, user_id, db):
        db.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = db.cursor.fetchone()
        if user_data:
            return cls(*user_data)
        return None

class Post:
    def __init__(self, id, content, image=None, likes_count=0, user_id=None):
        self.id = id
        self.content = content
        self.image = image
        self.likes_count = likes_count
        self.user_id = user_id

    @classmethod
    def create_post(cls, content, image, user_id, db):
        db.cursor.execute("INSERT INTO posts (content, image, user_id) VALUES (?, ?, ?)",
                          (content, image, user_id))
        db.commit()
        return cls.get_post_by_id(db.cursor.lastrowid, db)

    @classmethod
    def get_post_by_id(cls, post_id, db):
        db.cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        post_data = db.cursor.fetchone()
        if post_data:
            return cls(*post_data)
        return None


class Chat:
    def __init__(self, id, sender_id, receiver_id, message, created_at=None):
        self.id = id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message = message
        self.created_at = created_at or datetime.utcnow()

    @classmethod
    def send_chat(cls, sender_id, receiver_id, message, db):
        db.cursor.execute("INSERT INTO chats (sender_id, receiver_id, message) VALUES (?, ?, ?)",
                          (sender_id, receiver_id, message))
        db.commit()
        return cls.get_chat_by_id(db.cursor.lastrowid, db)

    @classmethod
    def get_chat_by_id(cls, chat_id, db):
        db.cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
        chat_data = db.cursor.fetchone()
        if chat_data:
            return cls(*chat_data)
        return None


class Notification:
    def __init__(self, id, content, user_id, post_id=None, created_at=None, notification_type=None):
        self.id = id
        self.content = content
        self.user_id = user_id
        self.post_id = post_id
        self.created_at = created_at or datetime.utcnow()
        self.notification_type = notification_type

    @classmethod
    def create_notification(cls, content, user_id, post_id, notification_type, db):
        db.cursor.execute("INSERT INTO notifications (content, user_id, post_id, notification_type) VALUES (?, ?, ?, ?)",
                          (content, user_id, post_id, notification_type))
        db.commit()
        return cls.get_notification_by_id(db.cursor.lastrowid, db)

    @classmethod
    def get_notification_by_id(cls, notification_id, db):
        db.cursor.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,))
        notification_data = db.cursor.fetchone()
        if notification_data:
            return cls(*notification_data)
        return None


class Like:
    def __init__(self, id, user_id, post_id):
        self.id = id
        self.user_id = user_id
        self.post_id = post_id

    @classmethod
    def like_post(cls, user_id, post_id, db):
        existing_like = cls.get_like_by_user_and_post(user_id, post_id, db)
        if existing_like:
            raise ValueError("Already liked")
        
        db.cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)",
                          (user_id, post_id))
        db.commit()
        return cls.get_like_by_user_and_post(user_id, post_id, db)

    @classmethod
    def get_like_by_user_and_post(cls, user_id, post_id, db):
        db.cursor.execute("SELECT * FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        like_data = db.cursor.fetchone()
        if like_data:
            return cls(*like_data)
        return None


def create_tables(db_path):
    db = DB(db_path)
    db.cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bio TEXT,
            profile_pic TEXT
        );
        
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            image TEXT,
            likes_count INTEGER DEFAULT 0,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        );
        
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            post_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            notification_type TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (post_id) REFERENCES posts (id)
        );
        
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            UNIQUE (user_id, post_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (post_id) REFERENCES posts (id)
        );
        """)
    db.commit()
    db.close()

