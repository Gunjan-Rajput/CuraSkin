import sys
import cv2
import numpy as np
import mysql.connector
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QStackedWidget, QMessageBox,
                             QFileDialog, QTextEdit, QFrame, QProgressBar)
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon, QPalette, QColor
from PyQt5.QtCore import QTimer, Qt, QSize
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

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
                prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
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
        reset_link = f"http://localhost:8000/reset-password?token={reset_token}"
        message = MIMEText(f"""
        Hello,

        You requested a password reset for your Curaskin account.

        Please click the following link to reset your password:
        {reset_link}

        If you didn't request this, please ignore this email.

        Best regards,
        Curaskin Team
        """)
        message['Subject'] = 'Curaskin - Password Reset'
        message['From'] = EMAIL_CONFIG['sender_email']
        message['To'] = recipient_email

        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(message)
        server.quit()
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
        # Demo mode - return random prediction
        demo_classes = ["Acne", "Eczema", "Psoriasis", "Melanoma", "Healthy Skin"]
        class_name = np.random.choice(demo_classes)
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


# Custom Styled Widgets
class StyledButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)


class StyledLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cccccc;
                border-radius: 5px;
                padding: 0 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)


# Login Widget
class LoginWidget(QWidget):
    def __init__(self, stacked_widget, main_app):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.main_app = main_app
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        # Title
        title = QLabel("Curaskin Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2E7D32; margin-bottom: 30px;")

        # Form
        self.username_input = StyledLineEdit("Username")
        self.password_input = StyledLineEdit("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Buttons
        login_btn = StyledButton("Login")
        login_btn.clicked.connect(self.handle_login)

        signup_btn = StyledButton("Don't have an account? Sign Up")
        signup_btn.clicked.connect(self.go_to_signup)

        forgot_btn = QPushButton("Forgot Password?")
        forgot_btn.setStyleSheet("color: #2196F3; border: none; background: transparent;")
        forgot_btn.clicked.connect(self.go_to_forgot_password)

        # Add to layout
        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_btn)
        layout.addWidget(signup_btn)
        layout.addWidget(forgot_btn)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #f5f5f5;")

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
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        # Title
        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2E7D32; margin-bottom: 30px;")

        # Form
        self.username_input = StyledLineEdit("Username")
        self.email_input = StyledLineEdit("Email")
        self.password_input = StyledLineEdit("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input = StyledLineEdit("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        # Password requirements
        requirements = QLabel(
            "Password must contain at least 8 characters, including uppercase, lowercase, number, and special character")
        requirements.setWordWrap(True)
        requirements.setStyleSheet("font-size: 12px; color: #666;")

        # Buttons
        signup_btn = StyledButton("Sign Up")
        signup_btn.clicked.connect(self.handle_signup)

        back_btn = StyledButton("Back to Login")
        back_btn.clicked.connect(self.go_to_login)

        # Add to layout
        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(requirements)
        layout.addWidget(signup_btn)
        layout.addWidget(back_btn)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #f5f5f5;")

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


# Forgot Password Widget
class ForgotPasswordWidget(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        # Title
        title = QLabel("Reset Password")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2E7D32; margin-bottom: 30px;")

        # Instructions
        instructions = QLabel("Enter your email address and we'll send you a link to reset your password.")
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 20px;")

        # Form
        self.email_input = StyledLineEdit("Email")

        # Buttons
        reset_btn = StyledButton("Send Reset Link")
        reset_btn.clicked.connect(self.handle_reset)

        back_btn = StyledButton("Back to Login")
        back_btn.clicked.connect(self.go_to_login)

        # Add to layout
        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addWidget(self.email_input)
        layout.addWidget(reset_btn)
        layout.addWidget(back_btn)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #f5f5f5;")

    def handle_reset(self):
        email = self.email_input.text()

        if not email:
            QMessageBox.warning(self, "Error", "Please enter your email")
            return

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Check if email exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()

            if result:
                user_id = result[0]
                reset_token = generate_reset_token()

                # Store reset token in database
                cursor.execute(
                    "UPDATE users SET reset_token = %s WHERE id = %s",
                    (reset_token, user_id)
                )

                conn.commit()
                cursor.close()
                conn.close()

                # Send reset email
                if send_reset_email(email, reset_token):
                    QMessageBox.information(self, "Success", "Password reset link sent to your email")
                    self.go_to_login()
                else:
                    QMessageBox.critical(self, "Error", "Failed to send reset email. Please try again later.")
            else:
                QMessageBox.warning(self, "Error", "Email not found in our system")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")

    def go_to_login(self):
        self.stacked_widget.setCurrentIndex(0)


# Main Application Widget
class CuraskinApp(QWidget):
    def __init__(self, stacked_widget, main_app):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.main_app = main_app
        self.current_image = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        header = QLabel("Curaskin - Skin Disease Detection")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E7D32; padding: 10px;")

        # Welcome message
        self.welcome_label = QLabel(f"Welcome, {self.main_app.current_username}!")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 16px; color: #555;")

        # Tab buttons
        tab_layout = QHBoxLayout()

        self.realtime_btn = QPushButton("Real-Time Detection")
        self.upload_btn = QPushButton("Upload Image")
        self.history_btn = QPushButton("Prediction History")
        self.logout_btn = QPushButton("Logout")

        for btn in [self.realtime_btn, self.upload_btn, self.history_btn, self.logout_btn]:
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E8F5E9;
                    color: #2E7D32;
                    border: 1px solid #C8E6C9;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #C8E6C9;
                }
                QPushButton:pressed {
                    background-color: #A5D6A7;
                }
            """)

        self.realtime_btn.clicked.connect(lambda: self.show_tab(0))
        self.upload_btn.clicked.connect(lambda: self.show_tab(1))
        self.history_btn.clicked.connect(lambda: self.show_tab(2))
        self.logout_btn.clicked.connect(self.handle_logout)

        tab_layout.addWidget(self.realtime_btn)
        tab_layout.addWidget(self.upload_btn)
        tab_layout.addWidget(self.history_btn)
        tab_layout.addWidget(self.logout_btn)

        # Content area
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

        # Add to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(self.welcome_label)
        main_layout.addLayout(tab_layout)
        main_layout.addWidget(self.content_stack)

        self.setLayout(main_layout)

        # Set initial tab
        self.show_tab(0)

    def create_realtime_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Camera feed
        self.camera_label = QLabel("Camera Feed")
        self.camera_label.setFixedSize(640, 480)
        self.camera_label.setStyleSheet("border: 2px solid #cccccc; background-color: #f0f0f0;")
        self.camera_label.setAlignment(Qt.AlignCenter)

        # Prediction display
        self.prediction_label = QLabel("Prediction: N/A")
        self.prediction_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        self.prediction_label.setAlignment(Qt.AlignCenter)

        # Confidence bar
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setFormat("Confidence: %p%")
        self.confidence_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)

        # Buttons
        button_layout = QHBoxLayout()

        self.start_btn = StyledButton("Start Camera")
        self.start_btn.clicked.connect(self.start_camera)

        self.stop_btn = StyledButton("Stop Camera")
        self.stop_btn.clicked.connect(self.stop_camera)
        self.stop_btn.setEnabled(False)

        self.capture_btn = StyledButton("Capture & Save")
        self.capture_btn.clicked.connect(self.capture_image)
        self.capture_btn.setEnabled(False)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.capture_btn)

        # Add to layout
        layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.prediction_label)
        layout.addWidget(self.confidence_bar)
        layout.addLayout(button_layout)

        widget.setLayout(layout)

        # Camera and Timer
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        return widget

    def create_upload_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Upload area
        self.upload_label = QLabel("No image selected")
        self.upload_label.setFixedSize(400, 400)
        self.upload_label.setStyleSheet("border: 2px dashed #cccccc; background-color: #f9f9f9;")
        self.upload_label.setAlignment(Qt.AlignCenter)

        # Upload button
        self.upload_image_btn = StyledButton("Browse Image")
        self.upload_image_btn.clicked.connect(self.browse_image)

        # Prediction display
        self.upload_prediction_label = QLabel("Prediction: N/A")
        self.upload_prediction_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        self.upload_prediction_label.setAlignment(Qt.AlignCenter)

        # Confidence bar
        self.upload_confidence_bar = QProgressBar()
        self.upload_confidence_bar.setRange(0, 100)
        self.upload_confidence_bar.setValue(0)
        self.upload_confidence_bar.setFormat("Confidence: %p%")
        self.upload_confidence_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)

        # Predict button
        self.predict_btn = StyledButton("Predict")
        self.predict_btn.clicked.connect(self.predict_uploaded_image)
        self.predict_btn.setEnabled(False)

        # Add to layout
        layout.addWidget(self.upload_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.upload_image_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.upload_prediction_label)
        layout.addWidget(self.upload_confidence_bar)
        layout.addWidget(self.predict_btn, alignment=Qt.AlignCenter)

        widget.setLayout(layout)
        return widget

    def create_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Title
        history_title = QLabel("Prediction History")
        history_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")

        # History display
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("border: 1px solid #cccccc; border-radius: 5px; padding: 10px;")

        # Refresh button
        refresh_btn = StyledButton("Refresh History")
        refresh_btn.clicked.connect(self.load_prediction_history)

        layout.addWidget(history_title)
        layout.addWidget(self.history_text)
        layout.addWidget(refresh_btn)

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
                        background-color: #4CAF50;
                        color: white;
                        border: 1px solid #45a049;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #E8F5E9;
                        color: #2E7D32;
                        border: 1px solid #C8E6C9;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #C8E6C9;
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
        self.camera_label.setText("Camera Feed")
        self.prediction_label.setText("Prediction: N/A")
        self.confidence_bar.setValue(0)

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                class_name, confidence = predict_image(frame)
                self.prediction_label.setText(f"Prediction: {class_name}")
                self.confidence_bar.setValue(int(confidence * 100))

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

                # Save prediction to database
                try:
                    conn = mysql.connector.connect(**DB_CONFIG)
                    cursor = conn.cursor()

                    cursor.execute(
                        "INSERT INTO prediction_history (user_id, image_path, prediction, confidence) VALUES (%s, %s, %s, %s)",
                        (self.main_app.current_user_id, "captured_image", class_name, float(confidence))
                    )

                    conn.commit()
                    cursor.close()
                    conn.close()

                    QMessageBox.information(self, "Success",
                                            f"Prediction saved: {class_name} ({confidence * 100:.2f}%)")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save prediction: {str(e)}")

    # Upload image methods
    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Skin Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )

        if file_path:
            self.current_image_path = file_path
            pixmap = QPixmap(file_path)
            self.upload_label.setPixmap(pixmap.scaled(
                self.upload_label.width(),
                self.upload_label.height(),
                Qt.KeepAspectRatio
            ))
            self.predict_btn.setEnabled(True)

    def predict_uploaded_image(self):
        if hasattr(self, 'current_image_path'):
            image = cv2.imread(self.current_image_path)
            if image is not None:
                class_name, confidence = predict_image(image)
                self.upload_prediction_label.setText(f"Prediction: {class_name}")
                self.upload_confidence_bar.setValue(int(confidence * 100))

                # Save prediction to database
                try:
                    conn = mysql.connector.connect(**DB_CONFIG)
                    cursor = conn.cursor()

                    cursor.execute(
                        "INSERT INTO prediction_history (user_id, image_path, prediction, confidence) VALUES (%s, %s, %s, %s)",
                        (self.main_app.current_user_id, self.current_image_path, class_name, float(confidence))
                    )

                    conn.commit()
                    cursor.close()
                    conn.close()

                    QMessageBox.information(self, "Success",
                                            f"Prediction saved: {class_name} ({confidence * 100:.2f}%)")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save prediction: {str(e)}")

    # History methods
    def load_prediction_history(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT image_path, prediction, confidence, prediction_time FROM prediction_history WHERE user_id = %s ORDER BY prediction_time DESC LIMIT 20",
                (self.main_app.current_user_id,)
            )

            history = cursor.fetchall()
            cursor.close()
            conn.close()

            if history:
                history_text = "<h3>Recent Predictions:</h3><ul>"
                for img_path, prediction, confidence, time in history:
                    history_text += f"<li><b>{prediction}</b> ({confidence * 100:.2f}%) - {time.strftime('%Y-%m-%d %H:%M')}</li>"
                history_text += "</ul>"
            else:
                history_text = "<p>No prediction history found.</p>"

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
        self.setWindowTitle("Curaskin - Skin Disease Detection")
        self.setGeometry(100, 100, 900, 700)

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

        # Application style
        self.setStyleSheet("""
            QWidget {
                font-family: Arial, sans-serif;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = CuraskinMainApp()
    window.show()

    sys.exit(app.exec_())