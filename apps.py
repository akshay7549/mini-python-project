from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from models import db, User, Video
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///video_streaming.db'
app.config['UPLOAD_FOLDER'] = 'uploads/'

db.init_app(app)

db_initialized = False

@app.before_request
def initialize_db():
    global db_initialized
    if not db_initialized:
        with app.app_context():
            db.create_all()
        db_initialized = True


# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))

        # Create a new user and save to the database
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query the database for the user
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('home'))

        # Flash error message for invalid credentials
        flash('Invalid username or password. Please try again.', 'error')

    return render_template('login.html')


# Home Route
# Home Route
@app.route('/')
def home():
    videos = Video.query.all()
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None  # Get user if logged in
    return render_template('home.html', videos=videos, user=user)


# Upload Route
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        file = request.files['file']

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Adding video to the database
            new_video = Video(title=title, category=category, filename=filename, uploader_id=session['user_id'])
            db.session.add(new_video)
            db.session.commit()
            return redirect(url_for('home'))

    return render_template('upload.html')

# Video Streaming Route
@app.route('/video/<int:video_id>')
def video(video_id):
    video = Video.query.get(video_id)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)

    def generate():
        with open(file_path, 'rb') as video_file:
            while chunk := video_file.read(1024):
                yield chunk

    return Response(generate(), mimetype='video/mp4')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))


# Delete Video Route
@app.route('/delete_video/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    video = Video.query.get(video_id)
    if video:
        db.session.delete(video)
        db.session.commit()
        flash('Video deleted successfully!', 'success')
    else:
        flash('Video not found.', 'error')
    return redirect(url_for('home'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)
