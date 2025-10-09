from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, redirect, url_for, flash
import face_recognition
from werkzeug.utils import secure_filename
from tweepy import Client
from tweepy.errors import TooManyRequests
import pickle
import database

# Load secrets from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

UPLOAD_FOLDER = 'static/uploads'
DATABASE_FOLDER = 'static/database'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATABASE_FOLDER'] = DATABASE_FOLDER

twitter_client = Client(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_face_encodings(image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    return encodings[0] if encodings else None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_missing', methods=['POST'])
def upload_missing():
    if 'file' not in request.files or request.files['file'].filename == '':
        return render_template('error.html', title="No file", message="No file uploaded.")

    name = request.form.get("name")
    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['DATABASE_FOLDER'], filename)
        file.save(file_path)

        encoding = get_face_encodings(file_path)
        if encoding is not None:
            database.add_missing_person(name, filename, pickle.dumps(encoding))
            return render_template('upload_success.html', name=name)
        else:
            os.remove(file_path)
            return render_template('error.html', title="No Face Detected", message="No face detected in uploaded image.")

    return redirect(url_for('index'))


@app.route('/upload_found', methods=['POST'])
def upload_found():
    if 'file' not in request.files or request.files['file'].filename == '':
        return render_template('error.html', title="No file", message="No file uploaded.")

    file = request.files['file']
    filename = secure_filename(file.filename)
    found_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(found_image_path)

    found_encoding = get_face_encodings(found_image_path)
    if found_encoding is None:
        return render_template('error.html', title="No Face Found", message="No face detected in the uploaded image.")

    matches = []
    for name, file_path, enc_blob in database.load_missing_people():
        db_encoding = pickle.loads(enc_blob)
        results = face_recognition.compare_faces([db_encoding], found_encoding)
        face_dist = face_recognition.face_distance([db_encoding], found_encoding)
        confidence = round((1 - face_dist[0]) * 100, 2)
        if results[0]:
            matches.append({
                "name": name,
                "file_path": file_path,
                "confidence": confidence
            })

    if matches:
        return render_template('matches.html', matches=matches)
    else:
        try:
            tweets = twitter_client.search_recent_tweets(
                query="missing person faces OR photos",
                max_results=10,
                tweet_fields=["attachments"]
            )
            tweet_images = []
            if tweets.data:
                for tweet in tweets.data:
                    tweet_images.append({
                        "image_url": f"https://twitter.com/user/status/{tweet.id}",
                        "name": "Unknown",
                        "confidence": None
                    })
            return render_template('matches.html', matches=tweet_images)
        except TooManyRequests:
            return render_template('error.html', title="Twitter API Limit Reached", message="Twitter is temporarily limiting searches.")


@app.route('/search_database', methods=['POST'])
def search_database():
    if 'file' not in request.files or request.files['file'].filename == '':
        return render_template('error.html', title="No file", message="No file uploaded.")

    file = request.files['file']
    filename = secure_filename(file.filename)
    found_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(found_image_path)

    found_encoding = get_face_encodings(found_image_path)
    if found_encoding is None:
        return render_template('error.html', title="No Face Found", message="No face detected in the uploaded image.")

    matches = []
    for name, file_path, enc_blob in database.load_missing_people():
        db_encoding = pickle.loads(enc_blob)
        results = face_recognition.compare_faces([db_encoding], found_encoding)
        face_dist = face_recognition.face_distance([db_encoding], found_encoding)
        confidence = round((1 - face_dist[0]) * 100, 2)
        if results[0]:
            matches.append({
                "name": name,
                "file_path": file_path,
                "confidence": confidence
            })

    return render_template('matches.html', matches=matches)


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DATABASE_FOLDER, exist_ok=True)
    database.init_db()
    app.run(debug=True)