from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
from werkzeug.utils import secure_filename
import database
from tweepy import Client
from tweepy.errors import TooManyRequests
import re

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# AWS Rekognition setup
rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
COLLECTION_ID = os.getenv("AWS_COLLECTION_ID")

# Twitter/X setup
twitter_client = Client(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))

# Upload folders
UPLOAD_FOLDER = 'static/uploads'
DATABASE_FOLDER = 'static/database'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATABASE_FOLDER'] = DATABASE_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize_name(name):
    """Sanitize name for Rekognition ExternalImageId."""
    return re.sub(r'[^a-zA-Z0-9_.\-:]', '_', name.strip())


def index_collection():
    """Ensure Rekognition collection exists."""
    existing_collections = rekognition.list_collections()["CollectionIds"]
    if COLLECTION_ID not in existing_collections:
        rekognition.create_collection(CollectionId=COLLECTION_ID)


def index_face(file_path, external_id):
    """Add face to Rekognition collection."""
    with open(file_path, 'rb') as f:
        rekognition.index_faces(
            CollectionId=COLLECTION_ID,
            Image={'Bytes': f.read()},
            ExternalImageId=external_id,
            DetectionAttributes=[]
        )


def search_face(file_path):
    with open(file_path, 'rb') as f:
        response = rekognition.search_faces_by_image(
            CollectionId=COLLECTION_ID,
            Image={'Bytes': f.read()},
            MaxFaces=5,
            FaceMatchThreshold=80
        )
    matches = []
    for match in response.get('FaceMatches', []):
        matches.append({
            "name": match['Face']['ExternalImageId'],
            "confidence": round(match['Similarity'], 2),
            "file_path": f"{match['Face']['ExternalImageId']}" 
        })
    return matches


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_missing', methods=['POST'])
def upload_missing():
    if 'file' not in request.files or request.files['file'].filename == '':
        return render_template('error.html', title="No file", message="No file uploaded.")

    name = request.form.get("name")
    sanitized_name = sanitize_name(name)
    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['DATABASE_FOLDER'], filename)
        file.save(file_path)

        # Index in Rekognition
        index_face(file_path, external_id=sanitized_name)

        # Save in local database
        database.add_missing_person(name, filename)
        return render_template('upload_success.html', name=name)

    return redirect(url_for('index'))


@app.route('/upload_found', methods=['POST'])
def upload_found():
    if 'file' not in request.files or request.files['file'].filename == '':
        return render_template('error.html', title="No file", message="No file uploaded.")

    file = request.files['file']
    filename = secure_filename(file.filename)
    found_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(found_image_path)

    matches = []

    # 1️⃣ Search database matches via Rekognition
    db_matches = search_face(found_image_path)
    for m in db_matches:
        db_entry = database.get_missing_person_by_name(m['name'])
        if db_entry:
            matches.append({
                "name": m['name'],
                "file_path": db_entry['filename'],
                "confidence": m['confidence'],
                "source": "Database"
            })

    
    try:
        tweets = twitter_client.search_recent_tweets(
            query="missing person OR lost person OR found child -is:retweet",
            max_results=10,
            tweet_fields=["attachments", "created_at", "text"],
            expansions=["attachments.media_keys"],
            media_fields=["url", "type"]
        )

        if tweets.data:
            media_dict = {}
            if tweets.includes and "media" in tweets.includes:
                for m in tweets.includes["media"]:
                    if m.type == "photo":
                        media_dict[m.media_key] = m.url

            for tweet in tweets.data:
                if hasattr(tweet, "attachments"):
                    for key in tweet.attachments.get("media_keys", []):
                        if key in media_dict:
                            matches.append({
                                "image_url": media_dict[key],
                                "name": "Unknown",
                                "confidence": None,
                                "source": "Social Media"
                            })

    except TooManyRequests:
        flash("Twitter API Limit Reached — showing database matches only.", "warning")
    except Exception as e:
        flash(f"Twitter API Error: {e}", "danger")

    return render_template('matches.html', matches=matches)


@app.route('/search_database', methods=['POST'])
def search_database():
    if 'file' not in request.files or request.files['file'].filename == '':
        return render_template('error.html', title="No file", message="No file uploaded.")

    file = request.files['file']
    filename = secure_filename(file.filename)
    found_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(found_image_path)

    matches = []
    db_matches = search_face(found_image_path)
    for m in db_matches:
        db_entry = database.get_missing_person_by_name(m['name'])
        if db_entry:
            matches.append({
                "name": m['name'],
                "file_path": db_entry['filename'],
                "confidence": m['confidence'],
                "source": "Database"
            })

    return render_template('matches.html', matches=matches)


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DATABASE_FOLDER, exist_ok=True)
    database.init_db()
    index_collection()
    app.run(debug=True)