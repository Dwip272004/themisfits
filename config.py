import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'iamdwip'
    DATABASE = os.path.join(BASE_DIR, 'misfits.db')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'