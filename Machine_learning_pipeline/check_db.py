# check_db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import MLFeatures
import os

# Update this to match your actual database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/crop_data.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Count total records
total = db.query(MLFeatures).count()
print(f"Total records in ml_features table: {total}")

# Show first 5 records
print("\nFirst 5 records:")
for record in db.query(MLFeatures).limit(5).all():
    print(f"  {record.area} | {record.year} | {record.crop_type} | Yield: {record.crop_yield}")

# Check for unique areas and crops
from sqlalchemy import func, distinct
unique_areas = db.query(func.count(distinct(MLFeatures.area))).scalar()
unique_crops = db.query(func.count(distinct(MLFeatures.crop_type))).scalar()

print(f"\nUnique areas/countries: {unique_areas}")
print(f"Unique crop types: {unique_crops}")

db.close()