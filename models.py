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
        db.cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
        user_data = db.cursor.fetchone()
        if user_data:
            return cls(*user_data)
        return None

    @classmethod
    def create_user(cls, username, email, password, db):
        db.cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = db.cursor.fetchone()
        if existing_user:
            raise ValueError("Email already exists")
        
        db.cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                          (username, email, password))
        db.commit()


class Post:
    def __init__(self, id, content, image=None, likes_count=0, user_id=None):
        self.id = id
        self.content = content
        self.image = image
        self.likes_count = likes_count
        self.user_id = user_id

    @classmethod
    def create_post(cls, content, image, user_id, db):
        db.cursor.execute("INSERT INTO post (content, image, user_id) VALUES (?, ?, ?)",
                          (content, image, user_id))
        db.commit()


class Chat:
    def __init__(self, id, sender_id, receiver_id, message, created_at=None):
        self.id = id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message = message
        self.created_at = created_at or datetime.utcnow()

    @classmethod
    def send_chat(cls, sender_id, receiver_id, message, db):
        db.cursor.execute("INSERT INTO chat (sender_id, receiver_id, message) VALUES (?, ?, ?)",
                          (sender_id, receiver_id, message))
        db.commit()


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
        db.cursor.execute("INSERT INTO notification (content, user_id, post_id, notification_type) VALUES (?, ?, ?, ?)",
                          (content, user_id, post_id, notification_type))
        db.commit()


class Like:
    def __init__(self, id, user_id, post_id):
        self.id = id
        self.user_id = user_id
        self.post_id = post_id

    @classmethod
    def like_post(cls, user_id, post_id, db):
        db.cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (?, ?)",
                          (user_id, post_id))
        db.commit()


# Create tables
def create_tables(db_path):
    db = DB(db_path)
    db.cursor.executescript("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bio TEXT,
            profile_pic TEXT
        );
        
        CREATE TABLE IF NOT EXISTS post (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            image TEXT,
            likes_count INTEGER DEFAULT 0,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );
        
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES user (id),
            FOREIGN KEY (receiver_id) REFERENCES user (id)
        );
        
        CREATE TABLE IF NOT EXISTS notification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            post_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            notification_type TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (post_id) REFERENCES post (id)
        );
        
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            UNIQUE (user_id, post_id),
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (post_id) REFERENCES post (id)
        );
        """)
    db.commit()
    db.close()


# Example usage
db_path = 'misfits.db'
create_tables(db_path)

db = DB(db_path)

# Create user
user = User.create_user('john_doe', 'john@example.com', 'password123', db)

# Create post
post = Post.create_post('Hello, world!', None, 1, db)

# Send chat
chat = Chat.send_chat(1, 2, 'Hello!', db)

# Create notification
notification = Notification.create_notification('New like!', 1, 1, 'like', db)

# Like post
like = Like.like_post(1, 1, db)

db.close()
