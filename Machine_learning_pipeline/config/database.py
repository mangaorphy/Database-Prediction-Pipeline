"""Database configuration and connection utilities."""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# MySQL Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "agriculture_db")

# MongoDB Configuration
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "agriculture_db")
MONGO_USERNAME = os.getenv("MONGO_USERNAME", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")


def get_mysql_connection():
    """Get raw MySQL connection for bulk operations."""
    import pymysql
    return pymysql.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4'
    )


# MongoDB Connection
def get_mongodb_client():
    """Get MongoDB client."""
    # Check if using MongoDB Atlas connection string
    mongo_uri = os.getenv("MONGO_URI", "")
    
    if mongo_uri:
        # Use full connection string (for MongoDB Atlas)
        return MongoClient(mongo_uri)
    elif MONGO_USERNAME and MONGO_PASSWORD:
        # Local MongoDB with authentication
        mongo_url = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
        return MongoClient(mongo_url)
    else:
        # Local MongoDB without authentication
        mongo_url = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
        return MongoClient(mongo_url)


def get_mongodb():
    """Get MongoDB database instance."""
    client = get_mongodb_client()
    return client[MONGO_DATABASE]
