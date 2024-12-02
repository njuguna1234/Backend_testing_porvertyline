from flask import Flask, request, jsonify
from flask_login import LoginManager, login_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Post, Comment, Appointment
from flask_migrate import Migrate
import os
from datetime import datetime
from functools import wraps
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///therapist_app.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin_user():
    admin_username = "admin_therapist"
    admin_email = "admin@therapist.com"
    admin_password = "secureAdminPass123!"

    try:
        admin_user = User(
            username=admin_username,
            email=admin_email,
            is_therapist=True
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully.")
    except IntegrityError:
        db.session.rollback()
        print("Admin user already exists.")

def therapist_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_therapist:
            return jsonify({'message': 'Therapist access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user = User(username=data['username'], email=data['email'], is_therapist=data.get('is_therapist', False))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        login_user(user)
        return jsonify({'message': 'Logged in successfully', 'is_therapist': user.is_therapist}), 200
    return jsonify({'message': 'Invalid username or password'}), 401

# Post routes (for therapists only)
@app.route('/post', methods=['POST'])
@login_required
@therapist_required
def create_post():
    data = request.form
    media_file = request.files.get('media')
    
    post = Post(
        therapist_id=current_user.id,
        title=data['title'],
        content=data['content'],
        media_type=data.get('media_type', 'text')
    )

    if media_file and post.media_type in ['image', 'video']:
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{media_file.filename}"
        media_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        post.media_url = filename

    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Post created successfully', 'post_id': post.id}), 201

@app.route('/posts', methods=['GET'])
def get_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify([{
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'media_type': post.media_type,
        'media_url': post.media_url,
        'created_at': post.created_at,
        'therapist_id': post.therapist_id
    } for post in posts]), 200

# Comment routes (for all users)
@app.route('/comment', methods=['POST'])
@login_required
def add_comment():
    data = request.json
    comment = Comment(user_id=current_user.id, post_id=data['post_id'], content=data['content'])
    db.session.add(comment)
    db.session.commit()
    return jsonify({'message': 'Comment added successfully', 'comment_id': comment.id}), 201

@app.route('/comments/<int:post_id>', methods=['GET'])
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()
    return jsonify([{
        'id': comment.id,
        'user_id': comment.user_id,
        'content': comment.content,
        'created_at': comment.created_at
    } for comment in comments]), 200

# Appointment routes
@app.route('/appointment', methods=['POST'])
@login_required
def book_appointment():
    data = request.json
    appointment = Appointment(
        user_id=current_user.id,
        therapist_id=data['therapist_id'],
        date=datetime.fromisoformat(data['date']),
        duration=data.get('duration', 60),
        notes=data.get('notes', '')
    )
    db.session.add(appointment)
    db.session.commit()
    return jsonify({'message': 'Appointment booked successfully', 'appointment_id': appointment.id}), 201

@app.route('/appointments', methods=['GET'])
@login_required
def get_appointments():
    if current_user.is_therapist:
        appointments = Appointment.query.filter_by(therapist_id=current_user.id).all()
    else:
        appointments = Appointment.query.filter_by(user_id=current_user.id).all()
    
    return jsonify([{
        'id': appointment.id,
        'user_id': appointment.user_id,
        'therapist_id': appointment.therapist_id,
        'date': appointment.date,
        'duration': appointment.duration,
        'status': appointment.status,
        'notes': appointment.notes
    } for appointment in appointments]), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    app.run(debug=True)

