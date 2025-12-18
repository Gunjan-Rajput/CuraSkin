import sys
import cv2
import numpy as np
import mysql.connector
import hashlib
import secrets
import smtplib
import os
from email.mime.text import MIMEText
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QStackedWidget, QMessageBox,
                             QFileDialog, QTextEdit, QFrame, QProgressBar, QDialog,
                             QGridLayout, QScrollArea, QDateEdit, QTimeEdit, QSizePolicy)
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon, QPalette, QColor
from PyQt5.QtCore import QTimer, Qt, QSize, QDate, QTime
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt
import mysql.connector

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'curaskin_db'
}

# Email configuration (for password reset)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'theneerajjhaa@gmail.com',
    'sender_password': 'pkpzbfomjniddlvl'
}

# Disease classification based on your dataset
DISEASE_CLASSES = [
    'Acne', 'Lentigines', 'Leprosy', 'Melasma', 'Other',
    'Periorbital_hyperpigmentation', 'Postinflammatory_hyperpigmentation', 'Vitiligo'
]

# Classify diseases as Minor or Major
MINOR_DISEASES = ["Acne", "Melasma", "Periorbital_hyperpigmentation", "Postinflammatory_hyperpigmentation"]
MAJOR_DISEASES = ["Lentigines", "Leprosy", "Vitiligo", "Other"]

# Create images directory if it doesn't exist
if not os.path.exists('images'):
    os.makedirs('images')
    # Create subdirectories for products and doctors
    os.makedirs('images/products')
    os.makedirs('images/doctors')

# Skin care products data with image paths
SKIN_CARE_PRODUCTS = {
    "Acne": [
        {"name": "Neutrogena Oil-Free Acne Wash", "price": "$12.99", "image": "images/products/acne1.jpg",
         "description": "Salicylic acid acne treatment"},
        {"name": "La Roche-Posay Effaclar Duo", "price": "$29.99", "image": "images/products/acne2.jpg",
         "description": "Dual action acne treatment"},
        {"name": "CeraVe Acne Foaming Cream", "price": "$15.49", "image": "images/products/acne3.jpg",
         "description": "Benzoyl peroxide cleanser"}
    ],
    "Melasma": [
        {"name": "SkinCeuticals Discoloration Defense", "price": "$98.00", "image": "images/products/melasma1.jpg",
         "description": "Advanced dark spot corrector"},
        {"name": "Murad Rapid Age Spot Treatment", "price": "$65.00", "image": "images/products/melasma2.jpg",
         "description": "Hydroquinone-free formula"},
        {"name": "PCA Skin Pigment Gel", "price": "$112.00", "image": "images/products/melasma3.jpg",
         "description": "Professional strength brightening"}
    ],
    "Periorbital_hyperpigmentation": [
        {"name": "Kiehl's Dark Circle Perfector", "price": "$38.00", "image": "images/products/dark_circle1.jpg",
         "description": "Vitamin C eye treatment"},
        {"name": "Sunday Riley Auto Correct", "price": "$65.00", "image": "images/products/dark_circle2.jpg",
         "description": "Brightening eye cream"},
        {"name": "Drunk Elephant C-Tango", "price": "$64.00", "image": "images/products/dark_circle3.jpg",
         "description": "Vitamin C eye cream"}
    ],
    "Postinflammatory_hyperpigmentation": [
        {"name": "SkinMedica Lytera 2.0", "price": "$160.00", "image": "images/products/hyper1.jpg",
         "description": "Pigment correcting serum"},
        {"name": "Alastin Skincare A-Luminate", "price": "$95.00", "image": "images/products/hyper2.jpg",
         "description": "Brightening cream"},
        {"name": "EltaMD Even Tone", "price": "$49.00", "image": "images/products/hyper3.jpg",
         "description": "Tranexamic acid treatment"}
    ]
}

# Dermatologists data with image paths
DERMATOLOGISTS = {
    "Lentigines": [
        {"name": "Dr. Sarah Chen", "specialization": "Pigment Disorders Specialist", "hospital": "City Skin Center",
         "experience": "15 years", "image": "images/doctors/derm1.jpg"},
        {"name": "Dr. Michael Rodriguez", "specialization": "Laser Treatment Expert", "hospital": "University Medical",
         "experience": "12 years", "image": "images/doctors/derm2.jpg"},
        {"name": "Dr. Emily Watson", "specialization": "Photodamage Specialist", "hospital": "Memorial Hospital",
         "experience": "18 years", "image": "images/doctors/derm3.jpg"}
    ],
    "Leprosy": [
        {"name": "Dr. James Wilson", "specialization": "Infectious Skin Diseases",
         "hospital": "National Health Institute", "experience": "20 years", "image": "images/doctors/derm4.jpg"},
        {"name": "Dr. Lisa Thompson", "specialization": "Tropical Medicine", "hospital": "Global Health Center",
         "experience": "16 years", "image": "images/doctors/derm5.jpg"},
        {"name": "Dr. Robert Kim", "specialization": "Infectious Disease Control", "hospital": "Public Health Hospital",
         "experience": "14 years", "image": "images/doctors/derm6.jpg"}
    ],
    "Vitiligo": [
        {"name": "Dr. Amanda Lee", "specialization": "Autoimmune Skin Disorders", "hospital": "Skin Research Institute",
         "experience": "13 years", "image": "images/doctors/derm7.jpg"},
        {"name": "Dr. David Park", "specialization": "Depigmentation Expert", "hospital": "University Hospital",
         "experience": "17 years", "image": "images/doctors/derm8.jpg"},
        {"name": "Dr. Jennifer Martinez", "specialization": "Phototherapy Specialist", "hospital": "Dermatology Center",
         "experience": "15 years", "image": "images/doctors/derm9.jpg"}
    ],
    "Other": [
        {"name": "Dr. Kevin Brown", "specialization": "General Dermatology", "hospital": "Community Health Center",
         "experience": "12 years", "image": "images/doctors/derm10.jpg"},
        {"name": "Dr. Maria Garcia", "specialization": "Complex Skin Conditions", "hospital": "Regional Medical",
         "experience": "14 years", "image": "images/doctors/derm11.jpg"},
        {"name": "Dr. Thomas Clark", "specialization": "Diagnostic Dermatology", "hospital": "City General Hospital",
         "experience": "16 years", "image": "images/doctors/derm12.jpg"}
    ]
}

# Paths
MODEL_PATH = "skin_disease_model.h5"
CLASS_INDICES_PATH = "class_indices.npy"

# Load model and class indices (with error handling)
try:
    model = load_model(MODEL_PATH)
    class_indices = np.load(CLASS_INDICES_PATH, allow_pickle=True).item()
    class_labels = {v: k for k, v in class_indices.items()}
    MODEL_LOADED = True
except:
    print("Warning: Model files not found. Using demo mode.")
    MODEL_LOADED = False

IMG_SIZE = 224  # Model input size


# Initialize database
def init_database():
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()

        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                reset_token VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create prediction history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                image_path VARCHAR(255),
                prediction VARCHAR(100),
                confidence FLOAT,
                severity VARCHAR(20),
                prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully!")
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False


# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Generate reset token
def generate_reset_token():
    return secrets.token_urlsafe(32)


# Send password reset email
def send_reset_email(recipient_email, reset_token):
    try:
        message = MIMEText(f"""
        Hello,

        You requested a password reset for your Curaskin account.

        Your password reset token is:
        {reset_token}

        Please enter this token in the Curaskin application to reset your password.

        If you didn't request this, please ignore this email.

        Best regards,
        Curaskin Team
        """)
        message['Subject'] = 'Curaskin - Password Reset Token'
        message['From'] = EMAIL_CONFIG['sender_email']
        message['To'] = recipient_email

        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(message)
        server.quit()
        print(f"Reset email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


# Image processing functions
def preprocess_image(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (IMG_SIZE, IMG_SIZE))
    image = img_to_array(image) / 255.0
    image = np.expand_dims(image, axis=0)
    return image


def predict_image(image):
    if not MODEL_LOADED:
        # Demo mode - return random prediction from your disease classes
        class_name = np.random.choice(DISEASE_CLASSES)
        confidence = np.random.uniform(0.7, 0.95)
        return class_name, confidence

    processed = preprocess_image(image)
    prediction = model.predict(processed)
    class_idx = np.argmax(prediction)
    class_name = class_labels[class_idx]
    confidence = prediction[0][class_idx]
    return class_name, confidence


def convert_cv_to_qt(image):
    """Convert cv2 image to QPixmap for PyQt5 display"""
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
    return QPixmap.fromImage(qt_image)


def get_confidence_indicator(confidence):
    if confidence >= 0.8:
        return "🟢 High Confidence"
    elif confidence >= 0.5:
        return "🟡 Medium Confidence"
    else:
        return "🔴 Low Confidence"


def get_severity(disease):
    return "Minor" if disease in MINOR_DISEASES else "Major"


# Custom Styled Widgets
class GradientButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(45)
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd8, stop:1 #6a4590);
            }
        """)


class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(45)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 0 15px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background: #f8f9fa;
            }
        """)


class CardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)


# Password Reset Dialog
class ResetPasswordDialog(QDialog):
    def __init__(self, reset_token, parent=None):
        super().__init__(parent)
        self.reset_token = reset_token
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Reset Password")
        self.setFixedSize(450, 350)
        self.setModal(True)
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);")

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Card container
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(25, 25, 25, 25)

        # Title
        title = QLabel("Reset Your Password")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")

        # Token info
        token_label = QLabel(f"Reset Token: {self.reset_token}")
        token_label.setStyleSheet("""
            background: #f8f9fa; 
            padding: 12px; 
            border-radius: 8px; 
            font-family: monospace; 
            font-size: 13px;
            border: 1px solid #e9ecef;
        """)

        # Form
        self.new_password_input = ModernLineEdit("New Password")
        self.new_password_input.setEchoMode(QLineEdit.Password)

        self.confirm_password_input = ModernLineEdit("Confirm New Password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        # Buttons
        button_layout = QHBoxLayout()
        reset_btn = GradientButton("Reset Password")
        reset_btn.clicked.connect(self.handle_reset)

        cancel_btn = GradientButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c0392b, stop:1 #e74c3c);
            }
        """)

        button_layout.addWidget(reset_btn)
        button_layout.addWidget(cancel_btn)

        # Add to layout
        card_layout.addWidget(title)
        card_layout.addWidget(token_label)
        card_layout.addWidget(self.new_password_input)
        card_layout.addWidget(self.confirm_password_input)
        card_layout.addLayout(button_layout)

        layout.addWidget(card)
        self.setLayout(layout)

    def validate_password(self, password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Password must include uppercase, lowercase, number, and special character"

        return True, "Password is valid"

    def handle_reset(self):
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not new_password or not confirm_password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        is_valid, message = self.validate_password(new_password)
        if not is_valid:
            QMessageBox.warning(self, "Error", message)
            return

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Verify token and update password
            cursor.execute(
                "SELECT id FROM users WHERE reset_token = %s",
                (self.reset_token,)
            )
            result = cursor.fetchone()

            if result:
                user_id = result[0]
                password_hash = hash_password(new_password)

                # Update password and clear reset token
                cursor.execute(
                    "UPDATE users SET password_hash = %s, reset_token = NULL WHERE id = %s",
                    (password_hash, user_id)
                )

                conn.commit()
                cursor.close()
                conn.close()

                QMessageBox.information(self, "Success", "Password reset successfully!")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Invalid or expired reset token")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")


# Token Entry Dialog
class TokenEntryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Enter Reset Token")
        self.setFixedSize(450, 250)
        self.setModal(True)
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);")

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Card container
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(25, 25, 25, 25)

        # Title
        title = QLabel("Enter Password Reset Token")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")

        # Instructions
        instructions = QLabel("Please enter the reset token sent to your email:")
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #6c757d; font-size: 14px;")

        # Token input
        self.token_input = ModernLineEdit("Reset Token")

        # Buttons
        button_layout = QHBoxLayout()
        submit_btn = GradientButton("Submit")
        submit_btn.clicked.connect(self.handle_submit)

        cancel_btn = GradientButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c0392b, stop:1 #e74c3c);
            }
        """)

        button_layout.addWidget(submit_btn)
        button_layout.addWidget(cancel_btn)

        # Add to layout
        card_layout.addWidget(title)
        card_layout.addWidget(instructions)
        card_layout.addWidget(self.token_input)
        card_layout.addLayout(button_layout)

        layout.addWidget(card)
        self.setLayout(layout)

    def handle_submit(self):
        token = self.token_input.text().strip()

        if not token:
            QMessageBox.warning(self, "Error", "Please enter the reset token")
            return

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Verify token exists and is valid
            cursor.execute(
                "SELECT id FROM users WHERE reset_token = %s",
                (token,)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                # Open reset password dialog
                reset_dialog = ResetPasswordDialog(token, self)
                if reset_dialog.exec_() == QDialog.Accepted:
                    self.accept()
            else:
                QMessageBox.warning(self, "Error", "Invalid reset token")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")


# Login Widget
class LoginWidget(QWidget):
    def __init__(self, stacked_widget, main_app):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.main_app = main_app
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main container
        main_container = QWidget()
        main_container.setFixedSize(400, 600)
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 50, 40, 50)

        # Logo/Title
        title_container = QVBoxLayout()
        title = QLabel("Curaskin")
        title.setStyleSheet("""
            font-size: 42px; 
            font-weight: bold; 
            color: white;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 20px;
        """)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("AI-Powered Skin Health")
        subtitle.setStyleSheet("font-size: 16px; color: rgba(255,255,255,0.8);")
        subtitle.setAlignment(Qt.AlignCenter)

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        # Card for form
        card = CardWidget()
        card.setFixedHeight(350)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(25)
        card_layout.setContentsMargins(30, 30, 30, 30)

        form_title = QLabel("Welcome Back")
        form_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        form_title.setAlignment(Qt.AlignCenter)

        # Form
        self.username_input = ModernLineEdit("👤 Username")
        self.password_input = ModernLineEdit("🔒 Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Buttons
        login_btn = GradientButton("Login")
        login_btn.clicked.connect(self.handle_login)

        signup_btn = QPushButton("Don't have an account? Sign Up")
        signup_btn.setStyleSheet("""
            QPushButton {
                color: #667eea;
                border: none;
                background: transparent;
                font-size: 14px;
                padding: 8px;
            }
            QPushButton:hover {
                color: #764ba2;
                text-decoration: underline;
            }
        """)
        signup_btn.clicked.connect(self.go_to_signup)

        forgot_btn = QPushButton("Forgot Password?")
        forgot_btn.setStyleSheet("""
            QPushButton {
                color: #6c757d;
                border: none;
                background: transparent;
                font-size: 13px;
                padding: 5px;
            }
            QPushButton:hover {
                color: #495057;
                text-decoration: underline;
            }
        """)
        forgot_btn.clicked.connect(self.go_to_forgot_password)

        # Add to card layout
        card_layout.addWidget(form_title)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(login_btn)
        card_layout.addWidget(signup_btn)
        card_layout.addWidget(forgot_btn)

        # Add to main layout
        main_layout.addLayout(title_container)
        main_layout.addWidget(card)
        main_layout.addStretch()

        layout.addWidget(main_container)
        self.setLayout(layout)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()

            if result and result[1] == hash_password(password):
                self.main_app.current_user_id = result[0]
                self.main_app.current_username = username
                self.stacked_widget.setCurrentIndex(2)  # Go to main app
            else:
                QMessageBox.warning(self, "Error", "Invalid username or password")

            cursor.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")

    def go_to_signup(self):
        self.stacked_widget.setCurrentIndex(1)

    def go_to_forgot_password(self):
        self.stacked_widget.setCurrentIndex(3)


# Signup Widget
class SignupWidget(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main container
        main_container = QWidget()
        main_container.setFixedSize(450, 700)
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Logo/Title
        title_container = QVBoxLayout()
        title = QLabel("Join Curaskin")
        title.setStyleSheet("""
            font-size: 36px; 
            font-weight: bold; 
            color: white;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 20px;
        """)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Start your skin health journey")
        subtitle.setStyleSheet("font-size: 16px; color: rgba(255,255,255,0.8);")
        subtitle.setAlignment(Qt.AlignCenter)

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        # Card for form
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(30, 30, 30, 30)

        form_title = QLabel("Create Account")
        form_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        form_title.setAlignment(Qt.AlignCenter)

        # Form
        self.username_input = ModernLineEdit("👤 Username")
        self.email_input = ModernLineEdit("📧 Email")
        self.password_input = ModernLineEdit("🔒 Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input = ModernLineEdit("✓ Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        # Password requirements
        requirements = QLabel(
            "🔐 Password must contain: 8+ characters, uppercase, lowercase, number, and special character")
        requirements.setWordWrap(True)
        requirements.setStyleSheet(
            "font-size: 12px; color: #6c757d; background: #f8f9fa; padding: 10px; border-radius: 8px;")

        # Buttons
        signup_btn = GradientButton("Create Account")
        signup_btn.clicked.connect(self.handle_signup)

        back_btn = QPushButton("← Back to Login")
        back_btn.setStyleSheet("""
            QPushButton {
                color: #667eea;
                border: none;
                background: transparent;
                font-size: 14px;
                padding: 8px;
            }
            QPushButton:hover {
                color: #764ba2;
                text-decoration: underline;
            }
        """)
        back_btn.clicked.connect(self.go_to_login)

        # Add to card layout
        card_layout.addWidget(form_title)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.confirm_password_input)
        card_layout.addWidget(requirements)
        card_layout.addWidget(signup_btn)
        card_layout.addWidget(back_btn)

        # Add to main layout
        main_layout.addLayout(title_container)
        main_layout.addWidget(card)
        main_layout.addStretch()

        layout.addWidget(main_container)
        self.setLayout(layout)

    def validate_password(self, password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Password must include uppercase, lowercase, number, and special character"

        return True, "Password is valid"

    def handle_signup(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not all([username, email, password, confirm_password]):
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        is_valid, message = self.validate_password(password)
        if not is_valid:
            QMessageBox.warning(self, "Error", message)
            return

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Check if username or email already exists
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone():
                QMessageBox.warning(self, "Error", "Username or email already exists")
                return

            # Insert new user
            password_hash = hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )

            conn.commit()
            cursor.close()
            conn.close()

            QMessageBox.information(self, "Success", "Account created successfully!")
            self.go_to_login()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")

    def go_to_login(self):
        self.stacked_widget.setCurrentIndex(0)


class ForgotPasswordWidget(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);"
        )


        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # ---------------- Main Container (fixed size) ----------------
        main_container = QWidget()
        main_container.setFixedSize(450, 550)  # keep original width & height
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 50, 40, 50)

        # Title
        title = QLabel("Reset Password")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: white;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 20px;
        """)
        main_layout.addWidget(title)

        # ---------------- Card for Form ----------------
        card = CardWidget()
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)  # height expands inside fixed container
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(20, 20, 20, 20)

        # Form title
        form_title = QLabel("Recover Account")
        form_title.setAlignment(Qt.AlignCenter)
        form_title.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;"
        )

        # Instructions
        instructions = QLabel(
            "Enter your email and we'll send you a reset token:"
        )
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        instructions.setStyleSheet(
            "font-size: 14px; color: #6c757d; margin-bottom: 20px;"
        )

        # Email input
        self.email_input = ModernLineEdit("📧 Email Address")

        # Buttons
        reset_btn = GradientButton("Send Reset Token")
        reset_btn.clicked.connect(self.handle_reset)

        token_btn = GradientButton("I Have a Token")
        token_btn.clicked.connect(self.enter_token)

        back_btn = QPushButton("← Back to Login")
        back_btn.setStyleSheet("""
            QPushButton {
                color: #667eea;
                border: none;
                background: transparent;
                font-size: 14px;
                padding: 8px;
            }
            QPushButton:hover {
                color: #764ba2;
                text-decoration: underline;
            }
        """)
        back_btn.clicked.connect(self.go_to_login)

        # Buttons layout
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addWidget(reset_btn)
        buttons_layout.addWidget(token_btn)
        buttons_layout.addWidget(back_btn)

        # Add widgets to card
        card_layout.addWidget(form_title)
        card_layout.addWidget(instructions)
        card_layout.addWidget(self.email_input)
        card_layout.addStretch()  # push buttons to bottom
        card_layout.addLayout(buttons_layout)

        # Add card to main layout
        main_layout.addWidget(card)
        main_layout.addStretch()

        layout.addWidget(main_container)
        self.setLayout(layout)

    # ---------------- Event Handlers ----------------
    def handle_reset(self):
        email = self.email_input.text()
        if not email:
            QMessageBox.warning(self, "Error", "Please enter your email")
            return

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()

            if result:
                user_id = result[0]
                reset_token = generate_reset_token()

                cursor.execute(
                    "UPDATE users SET reset_token = %s WHERE id = %s",
                    (reset_token, user_id)
                )
                conn.commit()
                cursor.close()
                conn.close()

                if send_reset_email(email, reset_token):
                    QMessageBox.information(
                        self, "Success", "Password reset token sent to your email!"
                    )
                    self.enter_token()
                else:
                    QMessageBox.critical(
                        self, "Error", "Failed to send reset email. Please try again later."
                    )
            else:
                QMessageBox.warning(
                    self, "Error", "Email not found in our system"
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")

    def enter_token(self):
        token_dialog = TokenEntryDialog(self)
        if token_dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Password reset successfully!")
            self.go_to_login()

    def go_to_login(self):
        self.stacked_widget.setCurrentIndex(0)

class RecommendationCard(QFrame):
    def __init__(self, item_data, is_product=True, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.is_product = is_product
        self.consult_dialog = None  # Keep reference
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #667eea;
                background: #f8f9fa;
            }
        """)

        self.setFixedSize(280, 400 if self.is_product else 380)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Image
        image_label = QLabel()
        image_label.setFixedSize(150, 150)
        image_label.setAlignment(Qt.AlignCenter)
        image_path = self.item_data.get("image", "")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                image_label.setStyleSheet("background: #e9ecef; border-radius: 8px; border: 2px dashed #dee2e6;")
                image_label.setText("🛍️" if self.is_product else "👨‍⚕️")
        else:
            image_label.setStyleSheet("background: #e9ecef; border-radius: 8px; border: 2px dashed #dee2e6;")
            image_label.setText("🛍️" if self.is_product else "👨‍⚕️")
        layout.addWidget(image_label, alignment=Qt.AlignCenter)
        layout.addSpacing(25)

        # Name
        name_label = QLabel(self.item_data.get("name", ""))
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        # Product or Doctor details
        if self.is_product:
            price_label = QLabel(f"💵 {self.item_data.get('price','')}")
            price_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
            price_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(price_label)

            desc_label = QLabel(self.item_data.get("description", ""))
            desc_label.setStyleSheet("font-size: 12px; color: #6c757d;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        else:
            spec_label = QLabel(f"🎯 {self.item_data.get('specialization','')}")
            spec_label.setStyleSheet("font-size: 13px; color: #667eea;")
            spec_label.setWordWrap(True)
            layout.addWidget(spec_label)

            hosp_label = QLabel(f"🏥 {self.item_data.get('hospital','')}")
            hosp_label.setStyleSheet("font-size: 12px; color: #6c757d;")
            hosp_label.setWordWrap(True)
            layout.addWidget(hosp_label)

            exp_label = QLabel(f"⏳ {self.item_data.get('experience','')}")
            exp_label.setStyleSheet("font-size: 12px; color: #6c757d;")
            layout.addWidget(exp_label)

        # Action button
        action_btn = GradientButton("Buy Now" if self.is_product else "Book Consultation")
        action_btn.setFixedHeight(35)
        layout.addWidget(action_btn)

        if not self.is_product:
            action_btn.clicked.connect(self.open_consultation_dialog)

        layout.addStretch()
        self.setLayout(layout)

    def open_consultation_dialog(self):
        # Keep reference to avoid garbage collection
        self.consult_dialog = ConsultationDialog(self.item_data.get("name", ""), self)
        self.consult_dialog.show()  # Non-blocking
class ConsultationDialog(QDialog):
    def __init__(self, doctor_name, parent=None):
        super().__init__(parent)
        self.doctor_name = doctor_name
        self.setWindowTitle("Book Consultation")
        self.setFixedSize(360, 320)
        self.setStyleSheet("background-color: #e6f0fa;")  # light blue background
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Card frame
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 15px;
                border: 1px solid #cfd8dc;
            }
        """)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # Header
        lbl = QLabel(f"Book consultation with Dr. {self.doctor_name}")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #34495e;")
        card_layout.addWidget(lbl)

        # Date picker
        date_label = QLabel("Select Date:")
        date_label.setStyleSheet("font-size: 13px; color: #2c3e50;")
        card_layout.addWidget(date_label)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet("""
            QDateEdit {
                padding: 5px; 
                border-radius: 5px; 
                border: 1px solid #a0bcd5; 
                background: #f5f8fb;
            }
            QDateEdit::drop-down { width: 20px; }
        """)
        card_layout.addWidget(self.date_edit)

        # Time picker
        time_label = QLabel("Select Time:")
        time_label.setStyleSheet("font-size: 13px; color: #2c3e50;")
        card_layout.addWidget(time_label)
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setStyleSheet("""
            QTimeEdit {
                padding: 5px; 
                border-radius: 5px; 
                border: 1px solid #a0bcd5; 
                background: #f5f8fb;
            }
            QTimeEdit::drop-down { width: 20px; }
        """)
        card_layout.addWidget(self.time_edit)

        # Submit button
        submit_btn = QPushButton("Confirm Booking")
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                color: white; 
                font-weight: bold; 
                border-radius: 8px; 
                padding: 8px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a6bd8, stop:1 #653da3);
            }
        """)
        submit_btn.clicked.connect(self.handle_submit)
        card_layout.addWidget(submit_btn)

        card.setLayout(card_layout)
        main_layout.addWidget(card)
        self.setLayout(main_layout)

    def handle_submit(self):
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        selected_time = self.time_edit.time().toString("HH:mm:ss")

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO consultations (doctor_name, consultation_date, consultation_time)
                VALUES (%s, %s, %s)
            """, (self.doctor_name, selected_date, selected_time))
            conn.commit()
            cursor.close()
            conn.close()

            QMessageBox.information(self, "Success", f"Consultation booked on {selected_date} at {selected_time}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to book consultation: {str(e)}")

# Results Display Widget
class ResultsWidget(QWidget):
    def __init__(self, disease, confidence, parent=None):
        super().__init__(parent)
        self.disease = disease
        self.confidence = confidence
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Results card
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(25, 25, 25, 25)

        # Header
        header = QLabel("Analysis Results")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        header.setAlignment(Qt.AlignCenter)

        # Disease info
        disease_label = QLabel(f"Detected Condition: {self.disease}")
        disease_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e;")

        severity = get_severity(self.disease)
        severity_color = "#27ae60" if severity == "Minor" else "#e74c3c"
        severity_label = QLabel(f"Severity: {severity}")
        severity_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {severity_color}; padding: 8px; background: {severity_color}20; border-radius: 8px;")

        confidence_percent = self.confidence * 100
        confidence_label = QLabel(f"Confidence: {confidence_percent:.1f}%")
        confidence_label.setStyleSheet("font-size: 16px; color: #2c3e50;")

        confidence_indicator = QLabel(get_confidence_indicator(self.confidence))
        confidence_indicator.setStyleSheet(
            "font-size: 16px; font-weight: bold; padding: 8px; background: #f8f9fa; border-radius: 8px;")

        card_layout.addWidget(header)
        card_layout.addWidget(disease_label)
        card_layout.addWidget(severity_label)
        card_layout.addWidget(confidence_label)
        card_layout.addWidget(confidence_indicator)

        # Recommendations
        if severity == "Minor":
            rec_title = QLabel("💊 Recommended Products")
            products = SKIN_CARE_PRODUCTS.get(self.disease, [])
            rec_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; margin-top: 20px;")
            card_layout.addWidget(rec_title)

            if products:
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setFixedHeight(400)
                scroll.setStyleSheet("border: none; background: transparent;")

                container_widget = QWidget()
                container_layout = QHBoxLayout(container_widget)
                container_layout.setSpacing(15)
                container_layout.setContentsMargins(10, 10, 10, 10)

                for product in products:
                    card_item = RecommendationCard(product, is_product=True)
                    container_layout.addWidget(card_item)

                container_layout.addStretch()  # <-- prevents overlapping
                scroll.setWidget(container_widget)
                card_layout.addWidget(scroll)
            else:
                no_products = QLabel(f"No specific products available for {self.disease}.")
                no_products.setStyleSheet("color: #6c757d; font-style: italic; padding: 20px;")
                card_layout.addWidget(no_products)
        else:
            rec_title = QLabel("👨‍⚕️ Recommended Specialists")
            doctors = DERMATOLOGISTS.get(self.disease, [])
            rec_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; margin-top: 20px;")
            card_layout.addWidget(rec_title)

            if doctors:
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setFixedHeight(400)
                scroll.setStyleSheet("border: none; background: transparent;")

                container_widget = QWidget()
                container_layout = QHBoxLayout(container_widget)
                container_layout.setSpacing(15)
                container_layout.setContentsMargins(10, 10, 10, 10)

                for doctor in doctors:
                    card_item = RecommendationCard(doctor, is_product=False)
                    container_layout.addWidget(card_item)

                container_layout.addStretch()  # <-- prevents overlapping
                scroll.setWidget(container_widget)
                card_layout.addWidget(scroll)
            else:
                no_doctors = QLabel(f"Consult a general dermatologist for {self.disease}.")
                no_doctors.setStyleSheet("color: #6c757d; font-style: italic; padding: 20px;")
                card_layout.addWidget(no_doctors)

        layout.addWidget(card)
        self.setLayout(layout)

# Main Application Widget
class CuraskinApp(QWidget):
    def __init__(self, stacked_widget, main_app):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.main_app = main_app
        self.current_image = None
        self.results_widget = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header with gradient
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 10, 30, 10)

        # Logo and title
        title_section = QHBoxLayout()
        logo = QLabel("🔬")
        logo.setStyleSheet("font-size: 24px;")
        title = QLabel("Curaskin")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")

        title_section.addWidget(logo)
        title_section.addWidget(title)
        title_section.addStretch()

        # Welcome and logout
        user_section = QHBoxLayout()
        welcome = QLabel(f"Welcome, {self.main_app.current_username}!")
        welcome.setStyleSheet("font-size: 14px; color: white;")

        logout_btn = QPushButton("Logout")
        logout_btn.setFixedSize(80, 35)
        logout_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
            }
        """)
        logout_btn.clicked.connect(self.handle_logout)

        user_section.addWidget(welcome)
        user_section.addSpacing(10)
        user_section.addWidget(logout_btn)

        header_layout.addLayout(title_section)
        header_layout.addLayout(user_section)

        # Main content
        content_widget = QWidget()
        content_widget.setStyleSheet("background: #f8f9fa;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Tab buttons
        tab_container = QWidget()
        tab_container.setFixedHeight(60)
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        self.realtime_btn = QPushButton("🎥 Real-Time Detection")
        self.upload_btn = QPushButton("📁 Upload Image")
        self.history_btn = QPushButton("📊 Prediction History")

        for btn in [self.realtime_btn, self.upload_btn, self.history_btn]:
            btn.setFixedHeight(45)
            btn.setStyleSheet("""
                QPushButton {
                    background: white;
                    color: #6c757d;
                    border: 2px solid #e9ecef;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    border-color: #667eea;
                    color: #667eea;
                }
            """)

        self.realtime_btn.clicked.connect(lambda: self.show_tab(0))
        self.upload_btn.clicked.connect(lambda: self.show_tab(1))
        self.history_btn.clicked.connect(lambda: self.show_tab(2))

        tab_layout.addWidget(self.realtime_btn)
        tab_layout.addWidget(self.upload_btn)
        tab_layout.addWidget(self.history_btn)
        tab_layout.addStretch()

        # Content area with scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.content_stack = QStackedWidget()

        # Real-time detection tab
        self.realtime_tab = self.create_realtime_tab()
        self.content_stack.addWidget(self.realtime_tab)

        # Upload image tab
        self.upload_tab = self.create_upload_tab()
        self.content_stack.addWidget(self.upload_tab)

        # History tab
        self.history_tab = self.create_history_tab()
        self.content_stack.addWidget(self.history_tab)

        scroll.setWidget(self.content_stack)

        content_layout.addWidget(tab_container)
        content_layout.addWidget(scroll)

        main_layout.addWidget(header)
        main_layout.addWidget(content_widget)

        self.setLayout(main_layout)
        self.show_tab(0)

    def create_realtime_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Camera section
        camera_card = CardWidget()
        camera_layout = QVBoxLayout(camera_card)
        camera_layout.setSpacing(20)
        camera_layout.setContentsMargins(25, 25, 25, 25)

        section_title = QLabel("Real-Time Skin Analysis")
        section_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")

        # Camera feed
        self.camera_label = QLabel("🎥 Camera Feed Will Appear Here")
        self.camera_label.setFixedSize(640, 480)
        self.camera_label.setStyleSheet("""
            border: 3px dashed #dee2e6;
            border-radius: 12px;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 16px;
        """)
        self.camera_label.setAlignment(Qt.AlignCenter)

        # Prediction display
        self.prediction_label = QLabel("Prediction: Waiting for analysis...")
        self.prediction_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #2c3e50; padding: 15px; background: white; border-radius: 10px; border: 2px solid #e9ecef;")
        self.prediction_label.setAlignment(Qt.AlignCenter)

        # Confidence bar
        confidence_container = QVBoxLayout()
        confidence_text = QLabel("Confidence Level:")
        confidence_text.setStyleSheet("font-size: 14px; color: #6c757d; font-weight: bold;")

        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setFormat(" %p%")
        self.confidence_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 10px;
                text-align: center;
                height: 25px;
                background: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
            }
        """)

        confidence_container.addWidget(confidence_text)
        confidence_container.addWidget(self.confidence_bar)

        # Buttons
        button_layout = QHBoxLayout()
        self.start_btn = GradientButton("▶ Start Camera")
        self.start_btn.clicked.connect(self.start_camera)

        self.stop_btn = GradientButton("⏹ Stop Camera")
        self.stop_btn.clicked.connect(self.stop_camera)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c0392b, stop:1 #e74c3c);
            }
        """)

        self.capture_btn = GradientButton("📸 Capture & Analyze")
        self.capture_btn.clicked.connect(self.capture_image)
        self.capture_btn.setEnabled(False)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.capture_btn)

        camera_layout.addWidget(section_title)
        camera_layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)
        camera_layout.addLayout(confidence_container)
        camera_layout.addWidget(self.prediction_label)
        camera_layout.addLayout(button_layout)

        # Results area
        self.realtime_results_container = QVBoxLayout()

        layout.addWidget(camera_card)
        layout.addLayout(self.realtime_results_container)
        layout.addStretch()

        # Camera and Timer
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        widget.setLayout(layout)
        return widget

    def create_upload_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # Upload section
        upload_card = CardWidget()
        upload_layout = QVBoxLayout(upload_card)
        upload_layout.setSpacing(20)
        upload_layout.setContentsMargins(25, 25, 25, 25)

        section_title = QLabel("Upload Skin Image")
        section_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")

        # Upload area - FIXED: Now properly displays uploaded images
        self.upload_display_label = QLabel()
        self.upload_display_label.setFixedSize(400, 300)
        self.upload_display_label.setStyleSheet("""
            border: 3px dashed #dee2e6;
            border-radius: 12px;
            background: #f8f9fa;
        """)
        self.upload_display_label.setAlignment(Qt.AlignCenter)
        self.upload_display_label.setText("📁 Drag & drop or click to browse\n\nSupported formats: PNG, JPG, JPEG")

        # Upload button
        self.upload_image_btn = GradientButton("Browse Image")
        self.upload_image_btn.clicked.connect(self.browse_image)

        upload_layout.addWidget(section_title)
        upload_layout.addWidget(self.upload_display_label, alignment=Qt.AlignCenter)
        upload_layout.addWidget(self.upload_image_btn, alignment=Qt.AlignCenter)

        # Prediction display for upload
        self.upload_prediction_label = QLabel("Prediction: No image analyzed yet")
        self.upload_prediction_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #2c3e50; padding: 15px; background: white; border-radius: 10px; border: 2px solid #e9ecef;")
        self.upload_prediction_label.setAlignment(Qt.AlignCenter)

        # Confidence bar for upload
        upload_confidence_container = QVBoxLayout()
        upload_confidence_text = QLabel("Confidence Level:")
        upload_confidence_text.setStyleSheet("font-size: 14px; color: #6c757d; font-weight: bold;")

        self.upload_confidence_bar = QProgressBar()
        self.upload_confidence_bar.setRange(0, 100)
        self.upload_confidence_bar.setValue(0)
        self.upload_confidence_bar.setFormat(" %p%")
        self.upload_confidence_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 10px;
                text-align: center;
                height: 25px;
                background: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
            }
        """)

        upload_confidence_container.addWidget(upload_confidence_text)
        upload_confidence_container.addWidget(self.upload_confidence_bar)

        # Predict button
        self.predict_btn = GradientButton("🔍 Analyze Image")
        self.predict_btn.clicked.connect(self.predict_uploaded_image)
        self.predict_btn.setEnabled(False)

        upload_layout.addWidget(self.upload_prediction_label)
        upload_layout.addLayout(upload_confidence_container)
        upload_layout.addWidget(self.predict_btn, alignment=Qt.AlignCenter)

        # Results area for upload
        self.upload_results_container = QVBoxLayout()

        layout.addWidget(upload_card)
        layout.addLayout(self.upload_results_container)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        history_card = CardWidget()
        history_layout = QVBoxLayout(history_card)
        history_layout.setSpacing(20)
        history_layout.setContentsMargins(25, 25, 25, 25)

        section_title = QLabel("Prediction History")
        section_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")

        # History display
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 15px;
                background: white;
                font-size: 14px;
            }
        """)

        # Refresh button
        refresh_btn = GradientButton("🔄 Refresh History")
        refresh_btn.clicked.connect(self.load_prediction_history)

        history_layout.addWidget(section_title)
        history_layout.addWidget(self.history_text)
        history_layout.addWidget(refresh_btn, alignment=Qt.AlignCenter)

        layout.addWidget(history_card)
        widget.setLayout(layout)
        return widget

    def show_tab(self, index):
        self.content_stack.setCurrentIndex(index)

        # Update button styles to show active tab
        buttons = [self.realtime_btn, self.upload_btn, self.history_btn]
        for i, btn in enumerate(buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                        color: white;
                        border: 2px solid #667eea;
                        border-radius: 10px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: white;
                        color: #6c757d;
                        border: 2px solid #e9ecef;
                        border-radius: 10px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        border-color: #667eea;
                        color: #667eea;
                    }
                """)

        # Load history if history tab is selected
        if index == 2:
            self.load_prediction_history()

    def handle_logout(self):
        self.stop_camera()
        self.main_app.current_user_id = None
        self.main_app.current_username = None
        self.stacked_widget.setCurrentIndex(0)

    # Real-time camera methods
    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.warning(self, "Error", "Cannot access camera")
            return

        self.timer.start(30)  # Update every 30 ms
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.capture_btn.setEnabled(True)

    def stop_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None

        self.camera_label.clear()
        self.camera_label.setText("🎥 Camera Feed Will Appear Here")
        self.prediction_label.setText("Prediction: Waiting for analysis...")
        self.confidence_bar.setValue(0)

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                class_name, confidence = predict_image(frame)
                confidence_percent = confidence * 100

                self.prediction_label.setText(f"Prediction: {class_name}")
                self.confidence_bar.setValue(int(confidence_percent))

                pixmap = convert_cv_to_qt(frame)
                self.camera_label.setPixmap(pixmap.scaled(
                    self.camera_label.width(),
                    self.camera_label.height(),
                    Qt.KeepAspectRatio
                ))

    def capture_image(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                class_name, confidence = predict_image(frame)
                self.show_results(class_name, confidence, "realtime")

    # Upload image methods - FIXED: Now properly displays images
    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Skin Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )

        if file_path:
            self.current_image_path = file_path
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Display the image
                self.upload_display_label.setPixmap(pixmap.scaled(
                    self.upload_display_label.width() - 10,
                    self.upload_display_label.height() - 10,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))
                self.upload_display_label.setText("")  # Clear the text
                self.predict_btn.setEnabled(True)
            else:
                QMessageBox.warning(self, "Error", "Failed to load the image")

    def predict_uploaded_image(self):
        if hasattr(self, 'current_image_path'):
            image = cv2.imread(self.current_image_path)
            if image is not None:
                class_name, confidence = predict_image(image)
                self.show_results(class_name, confidence, "upload")

    def show_results(self, class_name, confidence, tab_type):
        # Update prediction display
        confidence_percent = confidence * 100
        confidence_indicator = get_confidence_indicator(confidence)

        if tab_type == "realtime":
            self.prediction_label.setText(f"Prediction: {class_name} | {confidence_indicator}")
            self.confidence_bar.setValue(int(confidence_percent))
            results_container = self.realtime_results_container
        else:
            self.upload_prediction_label.setText(f"Prediction: {class_name} | {confidence_indicator}")
            self.upload_confidence_bar.setValue(int(confidence_percent))
            results_container = self.upload_results_container

        # Clear previous results
        for i in reversed(range(results_container.count())):
            widget = results_container.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Create and add results widget
        results_widget = ResultsWidget(class_name, confidence)
        results_container.addWidget(results_widget)

        # Save prediction to database
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            severity = get_severity(class_name)
            image_path = "captured_image" if tab_type == "realtime" else self.current_image_path

            cursor.execute(
                "INSERT INTO prediction_history (user_id, image_path, prediction, confidence, severity) VALUES (%s, %s, %s, %s, %s)",
                (self.main_app.current_user_id, image_path, class_name, float(confidence), severity)
            )

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Failed to save prediction: {str(e)}")

    # History methods
    def load_prediction_history(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT image_path, prediction, confidence, severity, prediction_time FROM prediction_history WHERE user_id = %s ORDER BY prediction_time DESC LIMIT 20",
                (self.main_app.current_user_id,)
            )

            history = cursor.fetchall()
            cursor.close()
            conn.close()

            if history:
                history_text = """
                <div style="font-family: Arial, sans-serif;">
                    <h3 style="color: #2c3e50; margin-bottom: 20px;">📊 Recent Predictions</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #667eea; color: white;">
                                <th style="padding: 12px; text-align: left;">Condition</th>
                                <th style="padding: 12px; text-align: center;">Confidence</th>
                                <th style="padding: 12px; text-align: center;">Severity</th>
                                <th style="padding: 12px; text-align: right;">Date</th>
                            </tr>
                        </thead>
                        <tbody>
                """

                for img_path, prediction, confidence, severity, time in history:
                    confidence_percent = confidence * 100
                    confidence_display = get_confidence_indicator(confidence)
                    severity_color = "#27ae60" if severity == "Minor" else "#e74c3c"

                    history_text += f"""
                    <tr style="border-bottom: 1px solid #e9ecef;">
                        <td style="padding: 12px; font-weight: bold;">{prediction}</td>
                        <td style="padding: 12px; text-align: center;">
                            <span style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-family: monospace;">
                                {confidence_percent:.1f}% {confidence_display}
                            </span>
                        </td>
                        <td style="padding: 12px; text-align: center;">
                            <span style="color: {severity_color}; font-weight: bold;">{severity}</span>
                        </td>
                        <td style="padding: 12px; text-align: right; color: #6c757d;">
                            {time.strftime('%Y-%m-%d %H:%M')}
                        </td>
                    </tr>
                    """

                history_text += """
                        </tbody>
                    </table>
                </div>
                """
            else:
                history_text = """
                <div style="text-align: center; padding: 40px; color: #6c757d;">
                    <h3>No prediction history found</h3>
                    <p>Start analyzing images to see your history here!</p>
                </div>
                """

            self.history_text.setHtml(history_text)
        except Exception as e:
            self.history_text.setText(f"Error loading history: {str(e)}")


# Main Application
class CuraskinMainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user_id = None
        self.current_username = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Curaskin - AI Skin Disease Detection")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize database
        if not init_database():
            QMessageBox.critical(self, "Error", "Failed to initialize database. The application may not work properly.")

        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()

        # Create screens
        self.login_screen = LoginWidget(self.stacked_widget, self)
        self.signup_screen = SignupWidget(self.stacked_widget)
        self.main_app_screen = CuraskinApp(self.stacked_widget, self)
        self.forgot_password_screen = ForgotPasswordWidget(self.stacked_widget)

        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.login_screen)
        self.stacked_widget.addWidget(self.signup_screen)
        self.stacked_widget.addWidget(self.main_app_screen)
        self.stacked_widget.addWidget(self.forgot_password_screen)

        # Set initial screen
        self.stacked_widget.setCurrentIndex(0)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = CuraskinMainApp()
    window.show()

    sys.exit(app.exec_())