from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import sqlite3
from models import User, Post, Chat, Notification, Like, DB
from config import Config
from forms import RegistrationForm, LoginForm, ChangePasswordForm, EditProfileForm


app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = 'iamdwip'
app.config['DATABASE'] = 'misfits.db'


# Create tables if they don't exist
def create_tables():
    db = DB(app.config['DATABASE'])
    db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            bio TEXT,
            profile_pic TEXT
        )
    ''')

    db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            image_filename TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            message_content TEXT NOT NULL,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    ''')

    db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            user_id INTEGER,
            post_id INTEGER,
            type TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')

    db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            post_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')

    db.commit()
    db.close()


create_tables()


login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.get_user_by_email(user_id, DB(app.config['DATABASE']))


# Rest of your routes and functions...
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.get_user_by_email(user_id, DB(app.config['DATABASE']))


class DB:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = DB(app.config['DATABASE'])
        user = User.get_user_by_email(email, db)
        db.close()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html',form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        db = DB(app.config['DATABASE'])
        existing_user = User.get_user_by_email(email, db)
        if existing_user:
            flash('Email already registered. Please use a different email.', 'danger')
            return redirect(url_for('register'))
        User.create_user(username, email, generate_password_hash(password), db)
        db.close()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)


@app.route('/home')
@login_required
def home():
    db = DB(app.config['DATABASE'])
    posts = Post.get_all_posts(db)
    db.close()
    return render_template('home.html', posts=posts)


@app.route('/chat')
@login_required
def chat():
    db = DB(app.config['DATABASE'])
    chats = Chat.get_chats(current_user.id, db)
    users = User.get_all_users(db)
    db.close()
    return render_template('chat.html', chats=chats, users=users)


@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    message_content = request.form['message']
    receiver_id = request.form['receiver_id']
    db = DB(app.config['DATABASE'])
    Chat.send_chat(current_user.id, receiver_id, message_content, db)
    db.close()
    return redirect(url_for('chat'))


@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    db = DB(app.config['DATABASE'])
    user = User.get_user_by_id(user_id, db)
    db.close()
    if user is None:
        flash('User not found', 'danger')
        return redirect(url_for('home'))
    posts = Post.get_posts_by_user(user_id, db)
    db.close()
    can_edit = (user.id == current_user.id)
    return render_template('profile.html', user=user, posts=posts, can_edit=can_edit)


@app.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    form = EditProfileForm()
    db = DB(app.config['DATABASE'])
    user = User.get_user_by_id(user_id, db)
    db.close()
    if user is None or user.id != current_user.id:
        flash('You are not authorized to edit this profile.', 'danger')
        return redirect(url_for('home'))
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        db = DB(app.config['DATABASE'])
        User.update_user(user, db)
        db.close()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', user_id=user.id))
    return render_template('edit_profile.html', user=user,form = form)


@app.route('/find_friend', methods=['GET'])
@login_required
def find_friend():
    search_term = request.args.get('search', '')
    db = DB(app.config['DATABASE'])
    search_results = User.search_users(search_term, db)
    db.close()
    return render_template('find_friend.html', results=search_results)


@app.route('/send_friend_request/<int:user_id>')
@login_required
def send_friend_request(user_id):
    db = DB(app.config['DATABASE'])
    friend = User.get_user_by_id(user_id, db)
    db.close()
    if friend:
        notification_content = f"{current_user.username} sent you a friend request."
        db = DB(app.config['DATABASE'])
        Notification.create_notification(notification_content, user_id, 'friend_request', db)
        db.close()
        flash('Friend request sent!', 'success')
    else:
        flash('User not found!', 'danger')
    return redirect(url_for('find_friend'))


@app.route('/notifications')
@login_required
def notifications():
    db = DB(app.config['DATABASE'])
    notifications = Notification.get_notifications(current_user.id, db)
    notifications_with_posts = []
    for notification in notifications:
        post = Post.get_post(notification.post_id, db)
        notifications_with_posts.append((notification, post))
    db.close()
    return render_template('notifications.html', notifications=notifications_with_posts)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        db = DB(app.config['DATABASE'])
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('change_password'))
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('change_password'))
        current_user.password = generate_password_hash(new_password)
        User.update_user(current_user, db)
        db.close()
        flash('Your password has been updated successfully.', 'success')
        return redirect(url_for('settings'))
    return render_template('change_password.html',form=form)


@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        content = request.form['content']
        image = request.files.get('image')
        image_filename = None
        if image:
            image_filename = image.filename
            image_path = os.path.join('static/uploads', image_filename)
            image.save(image_path)
        db = DB(app.config['DATABASE'])
        Post.create_post(content, image_filename, current_user.id, db)
        db.close()
        flash('Post created successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html')


@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    db = DB(app.config['DATABASE'])
    post = Post.get_post(post_id, db)
    existing_like = Like.get_like(current_user.id, post_id, db)
    if existing_like:
        return jsonify({"message": "Already liked this post"}), 400
    Like.create_like(current_user.id, post_id, db)
    notification = Notification.create_notification(f"{current_user.username} liked your post.", post.user_id, 'like', db)
    post.likes_count += 1
    db.commit()
    db.close()
    return jsonify({"message": "Post liked", "likes_count": post.likes_count}), 200


@app.route('/unlike_post/<int:post_id>', methods=['POST'])
@login_required
def unlike_post(post_id):
    db = DB(app.config['DATABASE'])
    post = Post.get_post(post_id, db)
    existing_like = Like.get_like(current_user.id, post_id, db)
    if not existing_like:
        return jsonify({"message": "You haven't liked this post yet"}), 400
    Like.delete_like(current_user.id, post_id, db)
    post.likes_count -= 1
    db.commit()
    db.close()
    return jsonify({"message": "Post unliked", "likes_count": post.likes_count}), 200


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        new_bio = request.form.get('bio', '')
        current_user.bio = new_bio
        new_profile_pic = request.files.get('profile_pic')
        if new_profile_pic:
            profile_pic_path = f'static/uploads/profile_pics/{new_profile_pic.filename}'
            new_profile_pic.save(profile_pic_path)
            current_user.profile_pic = new_profile_pic.filename
        db = DB(app.config['DATABASE'])
        User.update_user(current_user, db)
        db.close()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)