from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///misfits.db'  # Update with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'iamdwip'  # Set a secret key for sessions

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# Setup Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login page if not logged in

# Import models (ensure this import is after db is initialized)
from models import User, Post, Chat, Notification, Like

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)  # Use Flask-Login's login_user function
            return redirect(url_for('home'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

# Registration route
from forms import RegistrationForm

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.', 'danger')
            return redirect(url_for('register'))
        
        # Create a new user instance
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


# Home route after login
@app.route('/home')
@login_required  # Protect the home route
def home():
    posts = Post.query.all()  # Fetch all posts
    return render_template('home.html', posts=posts)

# Chat route

@app.route('/chat')
@login_required
def chat():
    # Fetch all chats related to the current user
    chats = Chat.query.filter(
        (Chat.sender_id == current_user.id) | (Chat.receiver_id == current_user.id)
    ).all()

    # Fetch all users except the current user for selection in the chat
    users = User.query.filter(User.id != current_user.id).all()

    return render_template('chat.html', chats=chats, users=users)


@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    message_content = request.form['message']
    receiver_id = request.form['receiver_id']  # Get receiver_id from the form

    if receiver_id:
        new_chat = Chat(sender_id=current_user.id, receiver_id=receiver_id, message=message_content)
        db.session.add(new_chat)
        db.session.commit()
        
    return redirect(url_for('chat'))


# User profile route
# User profile route
@app.route('/profile/<int:user_id>')
@login_required  # Protect the profile route
def profile(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash('User not found', 'danger')
        return redirect(url_for('home'))

    posts = Post.query.filter_by(user_id=user_id).all()  # Fetch user's posts
    can_edit = (user.id == current_user.id)  # Check if the current user can edit their own profile
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
        # Handle password update if needed
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', user_id=user.id))

    return render_template('edit_profile.html', user=user)



# Find friends route
@app.route('/find_friend', methods=['GET'])
@login_required
def find_friend():
    search_term = request.args.get('search', '')
    search_results = []

    if search_term:
        search_results = User.query.filter(User.username.like(f'%{search_term}%')).all()

    return render_template('find_friend.html', results=search_results)

# Send friend requests
@app.route('/send_friend_request/<int:user_id>')
@login_required
def send_friend_request(user_id):
    friend = User.query.get(user_id)
    if friend:
        # Create a notification for the friend
        notification_content = f"{current_user.username} sent you a friend request."
        notification = Notification(content=notification_content, user_id=user_id, notification_type='friend_request')
        db.session.add(notification)
        db.session.commit()
        
        flash('Friend request sent!', 'success')
    else:
        flash('User not found!', 'danger')
    
    return redirect(url_for('find_friend'))

# Notification route
@app.route('/notifications')
@login_required
def notifications():
    # Assuming you want to get notifications for the current user
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # You might want to join with Post to get post details
    notifications_with_posts = []
    for notification in notifications:
        post = Post.query.get(notification.post_id)
        notifications_with_posts.append((notification, post))

    return render_template('notifications.html', notifications=notifications_with_posts)

# Logout route

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))  # Redirect to the login page or home page

#change password
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Verify current password
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('change_password'))

        # Check if new password and confirm password match
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('change_password'))

        # Update password
        current_user.password = generate_password_hash(new_password)
        db.session.commit()

        flash('Your password has been updated successfully.', 'success')
        return redirect(url_for('settings'))  # Redirect to settings or another page

    return render_template('change_password.html')

# Create post route
@app.route('/create_post', methods=['GET', 'POST'])
@login_required  # Protect the create post route
def create_post():
    if request.method == 'POST':
        content = request.form['content']  # Get the post content from the form
        
        # Handle image upload
        image = request.files.get('image')  # Get the uploaded image
        image_filename = None
        
        if image:
            # Save the image to a designated folder
            image_filename = image.filename
            image_path = os.path.join('static/uploads', image_filename)
            image.save(image_path)  # Save the image
            
        # Create a new Post instance
        new_post = Post(content=content, image=image_filename, user_id=current_user.id)
        db.session.add(new_post)  # Add the post to the session
        db.session.commit()  # Commit the session to save the post in the database
        
        flash('Post created successfully!', 'success')  # Flash success message
        return redirect(url_for('home'))  # Redirect to home after creating the post
    
    return render_template('create_post.html')  # Render the create post page
# Route to like a post
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

        # Adjust this line according to your Notification model
        notification = Notification(user_id=post.user_id, content=f"{current_user.username} liked your post.")
        db.session.add(notification)

        post.likes_count += 1
        db.session.commit()
        return jsonify({"message": "Post liked", "likes_count": post.likes_count}), 200
    return jsonify({"message": "Post not found"}), 404


# Route to unlike a post
@app.route('/unlike_post/<int:post_id>', methods=['POST'])
@login_required
def unlike_post(post_id):
    post = Post.query.get(post_id)
    if post:
        existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
        if not existing_like:
            return jsonify({"message": "You haven't liked this post yet"}), 400

        db.session.delete(existing_like)  # Remove the like from the database

        # Decrement the likes count
        post.likes_count -= 1

        db.session.commit()
        return jsonify({"message": "Post unliked", "likes_count": post.likes_count}), 200
    return jsonify({"message": "Post not found"}), 404


# Settings route
# Settings route
@app.route('/settings', methods=['GET', 'POST'])
@login_required  # Ensure that only logged-in users can access this route
def settings():
    if request.method == 'POST':
        # Handle bio update
        new_bio = request.form.get('bio', '')  # Get the updated bio from the form
        current_user.bio = new_bio  # Update the user's bio

        # Handle profile picture upload if applicable
        new_profile_pic = request.files.get('profile_pic')  # Example for profile picture upload
        if new_profile_pic:
            profile_pic_path = f'static/uploads/profile_pics/{new_profile_pic.filename}'
            new_profile_pic.save(profile_pic_path)
            current_user.profile_pic = new_profile_pic.filename
        
        # Commit the changes to the database
        db.session.commit()
        flash('Profile updated successfully!', 'success')

        return redirect(url_for('settings'))  # Redirect back to the settings page after updating

    return render_template('settings.html', user=current_user)  # Render the settings page with the current user info


#deleting the post

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    
    if post and post.user_id == current_user.id:  # Ensure user owns the post
        # Delete likes associated with the post
        Like.query.filter_by(post_id=post_id).delete()
        
        # Delete the post
        db.session.delete(post)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Post deleted successfully.'})
    
    return jsonify({'success': False, 'message': 'Post not found or permission denied.'}), 404


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
