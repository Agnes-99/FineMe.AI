# Find.AI – AI-Powered Missing Person Search

SCREENSHOTS PROVIDED!

**Find.AI** is an AI-powered web application designed to help families and authorities locate missing people faster. By uploading a photo of a missing person, the system scans both a secure database and Twitter public posts using AWS Rekognition and the Twitter API v2 to find potential matches, all in one place.

---

## 🚀 Features

- **Add Missing Person**  
  Upload a photo and save the person’s information to a secure database.

- **Database Search**  
  Compare a photo against locally stored missing persons and return matches with confidence scores.

- **Twitter Scan**  
  Automatically scan public posts on Twitter for potential matches.

- **Combined Search**  
  Search both the database and Twitter at the same time and display results in a single view.

- **Progress Tracking & Confidence Scores**  
  Real-time progress bar and similarity scores for each match.

---

## 🖼 Screenshots

### 1. Homepage & Upload
![Homepage](static/database/App_screenshots/IMG_5868.jpeg)  

### 2. Add Missing Person
![Add Missing Person](static/database/App_screenshots/IMG_5869.jpeg)  

### 3. Search Results
![Database Search](static/database/App_screenshots/IMG_5870.jpeg)  

---

## ⚙️ Technology Stack

- **Frontend:** HTML, CSS, JavaScript  
- **Backend:** Python Flask  
- **AI/ML:** AWS Rekognition (Face Detection & Matching)  
- **Social Media API:** Twitter API v2  
- **Database:** SQLite (local storage for missing persons)

---

## 🔧 Installation & Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/find-ai.git
cd find-ai