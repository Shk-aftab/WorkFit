import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    BASE_DIR = os.path.abspath(os.getcwd())  # Get the absolute path of the current working directory
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'workout_tracker.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    VIDEO_SOURCE = 0  # Default webcam
