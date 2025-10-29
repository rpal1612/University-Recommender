"""
Configuration file for University Recommender
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-123456'
    
    # MongoDB
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb+srv://admin:admin@cluster0.lgez1ci.mongodb.net/?appName=Cluster0'
    MONGODB_DB_NAME = 'university_recommender'
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSV Data
    CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'csv', 'Real_University_Data.csv')
    
    # Scoring weights
    WEIGHTS = {
        'academic': 0.30,
        'prestige': 0.25,
        'field': 0.20,
        'affordability': 0.15,
        'language': 0.05,
        'preferences': 0.05
    }
    
    # Limits
    MAX_RESULTS = 15
    CACHE_TIMEOUT = 300  # 5 minutes
    
    # Collaborative Filtering
    MIN_COMMON_SEARCHES = 2  # Minimum common searches to consider users similar
    COLLABORATIVE_WEIGHT = 0.3  # 30% collaborative, 70% content-based
    
    # Validation ranges
    GRE_VERBAL_MIN = 130
    GRE_VERBAL_MAX = 170
    GRE_QUANT_MIN = 130
    GRE_QUANT_MAX = 170
    GRE_ANALYTICAL_MIN = 0.0
    GRE_ANALYTICAL_MAX = 6.0
    GPA_MIN = 0.0
    GPA_MAX = 4.0
    IELTS_MIN = 0.0
    IELTS_MAX = 9.0
    TOEFL_MIN = 0
    TOEFL_MAX = 120

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
