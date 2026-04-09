import os


class Config:
    # MongoDB connection string (change in .env for production)
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/women_safety_db")
    JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-dev-key")
    JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8MB upload limit
