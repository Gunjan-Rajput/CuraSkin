#  CuraSkin — AI-Based Skin Disease Detection System

CuraSkin is a desktop-based AI application that detects skin diseases using image processing and deep learning. The system is built using **Python, PyQt5, TensorFlow (CNN model), and MySQL (XAMPP)**. It provides a user-friendly interface for login/signup, real-time detection, image upload, and medical recommendations.

---

## Objective

To develop an intelligent system that can:

* Detect skin diseases using images
* Classify diseases as Minor or Major
* Provide skincare product recommendations
* Suggest dermatologists for serious conditions

---

##  Key Features

###  Authentication System

* User Signup & Login
* Secure password hashing (SHA-256)
* Forgot password via email (OTP/Token system)

###  AI Skin Detection

* CNN model (`skin_disease_model.h5`)
* Real-time webcam detection
* Image upload detection
* Confidence score display

###  Disease Classification

* Diseases detected:

  * Acne
  * Melasma
  * Pigmentation
  * Lentigines
  * Leprosy
  * Vitiligo
  * Normal Skin

* Severity:

  * Minor
  * Major

###  Recommendations

* Skincare product suggestions
* Dermatologist recommendations (for major diseases)

###  Extra Features

* Doctor consultation booking (date & time)
* Prediction history stored in MySQL
* GUI-based modern interface using PyQt5

---

##  Technologies Used

### 🔹 Programming

* Python

### 🔹 GUI

* PyQt5

### 🔹 Machine Learning

* TensorFlow / Keras
* CNN Model

### 🔹 Database

* MySQL (via XAMPP)

### 🔹 Other Libraries

* OpenCV
* NumPy
* smtplib (Email system)

---

##  Project Structure
```bash id="cmd101"
CuraSkin/
│
├── Dataset/
│   ├── Train/
│   ├── Test/
│   │   ├── Acne/
│   │   ├── Lentigines/
│   │   ├── Leprosy/
│   │   ├── Melasma/
│   │   ├── Normal_Skin/
│   │   ├── Other/
│   │   ├── Pigmentation/
│   │   └── Vitiligo/
│   └── Validation/
│
├── images/
├── static/
├── templates/
│
├── app.py
├── prediction.py
├── prediction2.py
│
├── Training.py
├── skin_disease_model.h5
│
├── class_indices.npy
├── class_mapping.json
│
├── jff_to_jpg.py
├── requirements.txt
│
├── confusion.png
├── Training_final.png
│
└── README.md
```
---

##  Setup Instructions

### 🔹 Step 1: Clone Repository

```bash id="cmd101"
git clone https://github.com/Gunjan-Rajput/CuraSkin.git
cd CuraSkin/SKIN_DISEASE_FLASK
```

---

### 🔹 Step 2: Install Dependencies

```bash id="cmd102"
pip install -r requirements.txt
```

---

### 🔹 Step 3: Start XAMPP

1. Open XAMPP Control Panel
2. Start:

   * Apache 
   * MySQL 

---

### 🔹 Step 4: Database Setup

1. Open browser → `http://localhost/phpmyadmin`
2. Create database:

```
curaskin_db
```

 Tables automatically create ho jayengi jab app run hoga (`init_database()` function)

---

### 🔹 Step 5: Run the Application

```bash id="cmd103"
python prediction2.py
```

---

##  How the System Works

1. User logs in / signs up
2. Image is captured via webcam OR uploaded
3. Image is processed using OpenCV
4. CNN model predicts disease
5. System shows:

   * Disease name
   * Confidence level
   * Severity (Minor/Major)
6. Based on result:

   * Products suggested (Minor)
   * Doctors suggested (Major)
7. Data saved in MySQL

---

##  Email System

* Used for password reset
* Token-based verification
* Implemented using SMTP (Gmail)

---

##  Database Tables

* `users` → stores user data
* `prediction_history` → stores predictions
* `consultations` → doctor booking records

---

##  Model Details

* Model: `skin_disease_model.h5`
* Input Size: 224x224
* Output: Disease class + confidence

---

##  Future Scope

*  Web version deployment
*  Mobile app
*  AI chatbot for skincare
*  Location-based doctor suggestions
*  Better dataset for higher accuracy

---

## License

This project is developed for academic purposes.

---

## Acknowledgement

Thanks to open-source libraries and tools used in this project.
