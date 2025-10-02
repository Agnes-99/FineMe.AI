import os
import cv2
import numpy as np
from flask import Flask, render_template, request, url_for

app = Flask(__name__)

# Set uploads folder inside static
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
if face_cascade.empty():
    raise Exception("Failed to load Haar Cascade xml file")


@app.route("/", methods=["GET", "POST"])
def index():
    processed_image = None
    face_count = 0
    confidence = 0
    original_image = None

    if request.method == "POST":
        if "file" not in request.files:
            return "No file uploaded", 400

        file = request.files["file"]
        if file.filename == "":
            return "Empty file name", 400

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)
        original_image = url_for('static', filename=f"uploads/{file.filename}")

        # Read the image
        img = cv2.imread(filepath)
        if img is None:
            return "Failed to load image", 400

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        face_count = len(faces)

        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Simple confidence: average face area
        if face_count > 0:
            confidences = [w*h for (x, y, w, h) in faces]
            confidence = int(sum(confidences) / len(confidences) / (img.shape[0] * img.shape[1]) * 100)

        # Save result
        result_filename = "result_" + file.filename
        output_path = os.path.join(app.config["UPLOAD_FOLDER"], result_filename)
        cv2.imwrite(output_path, img)

        processed_image = url_for('static', filename=f"uploads/{result_filename}")

    return render_template(
        "index.html",
        processed_image=processed_image,
        face_count=face_count,
        confidence=confidence,
        original_image=original_image
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
