
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from datetime import datetime
import os
from db import db
from models import User, Post, Chat, Notification, Like
from forms import RegistrationForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///misfits.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'iamdwip'

db.init_app(app)
migrate = Migrate(app, db)


login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):

            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data


        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, password=generate_password_hash(password))
        db.session.add(user)
        try:
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html', form=form)


@app.route('/home')
@login_required
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)


@app.route('/chat')
@login_required
def chat():
    chats = Chat.query.filter(
        (Chat.sender_id == current_user.id) | (Chat.receiver_id == current_user.id)
    ).all()

    users = User.query.filter(User.id != current_user.id).all()

    return render_template('chat.html', chats=chats, users=users)


@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    message_content = request.form['message']
    receiver_id = request.form['receiver_id']

    if receiver_id:
        new_chat = Chat(sender_id=current_user.id, receiver_id=receiver_id, message=message_content)
        db.session.add(new_chat)
        db.session.commit()
        
    return redirect(url_for('chat'))


@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash('User not found', 'danger')
        return redirect(url_for('home'))

    posts = Post.query.filter_by(user_id=user_id).all()
    can_edit = (user.id == current_user.id)
    return render_template('profile.html', user=user, posts=posts, can_edit=can_edit)


@app.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    user = User.query.get(user_id)
    if user is None or user.id != current_user.id:
        flash('You are not authorized to edit this profile.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', user_id=user.id))

    return render_template('edit_profile.html', user=user)


@app.route('/find_friend', methods=['GET'])
@login_required
def find_friend():
    search_term = request.args.get('search', '')
    search_results = []

    if search_term:
        search_results = User.query.filter(User.username.like(f'%{search_term}%')).all()

    return render_template('find_friend.html', results=search_results)




@app.route('/send_friend_request/<int:user_id>')
@login_required
def send_friend_request(user_id):
    friend = User.query.get(user_id)
    if friend:
        notification_content = f"{current_user.username} sent you a friend request."
        notification = Notification(content=notification_content, user_id=user_id, notification_type='friend_request')
        db.session.add(notification)
        db.session.commit()
        
        flash('Friend request sent!', 'success')
    else:
        flash('User not found!', 'danger')
    
    return redirect(url_for('find_friend'))


@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    notifications_with_posts = []
    for notification in notifications:
        post = Post.query.get(notification.post_id)
        notifications_with_posts.append((notification, post))

    return render_template('notifications.html', notifications=notifications_with_posts)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('change_password'))

        current_user.password = generate_password_hash(new_password)
        db.session.commit()

        flash('Your password has been updated successfully.', 'success')
        return redirect(url_for('settings')) 


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
            
        new_post = Post(content=content, image=image_filename, user_id=current_user.id)
        db.session.add(new_post)  
        db.session.commit()
        
        flash('Post created successfully!', 'success')  
        return redirect(url_for('home'))  
    
    return render_template('create_post.html') 


@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get(post_id)
    if post:
        existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
        if existing_like:
            return jsonify({"message": "Already liked this post"}), 400

        new_like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)

        notification = Notification(user_id=post.user_id, content=f"{current_user.username} liked your post.")
        db.session.add(notification)

        post.likes_count += 1
        db.session.commit()
        return jsonify({"message": "Post liked", "likes_count": post.likes_count}), 200
    return jsonify({"message": "Post not found"}), 404


@app.route('/unlike_post/<int:post_id>', methods=['POST'])
@login_required
def unlike_post(post_id):
    post = Post.query.get(post_id)
    if post:
        existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
        if not existing_like:
            return jsonify({"message": "You haven't liked this post yet"}), 400

        db.session.delete(existing_like)  
        post.likes_count -= 1

        db.session.commit()
        return jsonify({"message": "Post unliked", "likes_count": post.likes_count}), 200
    return jsonify({"message": "Post not found"}), 404


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
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')

        return redirect(url_for('settings'))  

    return render_template('settings.html', user=current_user) 



@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post and post.user_id == current_user.id:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully!', 'success')
    else:
        flash('You are not authorized to delete this post.', 'danger')
    
    return redirect(url_for('home'))


@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get(post_id)
    if post and post.user_id == current_user.id:
        if request.method == 'POST':
            post.content = request.form['content']
            db.session.commit()
            flash('Post updated successfully!', 'success')
            return redirect(url_for('home'))
        
        return render_template('edit_post.html', post=post)
    else:
        flash('You are not authorized to edit this post.', 'danger')
        return redirect(url_for('home'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the port from the environment variable, default to 5000
    app.run(host='0.0.0.0', port=port, debug=True)