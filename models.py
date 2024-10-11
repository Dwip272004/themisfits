from db import db
from flask_login import UserMixin
from datetime import datetime


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.String(200))
    profile_pic = db.Column(db.String(200))

    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True)
    sent_chats = db.relationship('Chat', foreign_keys='Chat.sender_id', backref='sender', lazy=True)
    received_chats = db.relationship('Chat', foreign_keys='Chat.receiver_id', backref='receiver', lazy=True)
    notifications = db.relationship('Notification', backref='notifier', lazy=True)
    likes = db.relationship('Like', backref='liker', lazy=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    likes_count = db.Column(db.Integer, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    likes = db.relationship('Like', backref='liked_post', lazy=True)


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notification_type = db.Column(db.String(50))

    post = db.relationship('Post', backref='post_notifications', lazy=True)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

<<<<<<< HEAD
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='_user_post_uc'),)
=======
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='_user_post_uc'),)
>>>>>>> ce476617c14f7e08fc958afd74510ff9685b921a
