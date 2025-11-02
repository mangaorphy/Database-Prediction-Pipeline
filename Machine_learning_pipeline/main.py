"""
FastAPI application for CRUD operations on agricultural database.

Endpoints for managing Rainfall, Temperature, Pesticides, and Crop Yield data.
Supports both MySQL (primary) and MongoDB (secondary) databases.
"""
import os
import json
import math
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv 
from models import Base, Rainfall, Temperature, Pesticides, CropYield, MLFeatures

import sys
import io

# Force UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add logging configuration and logger
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# Import models and schemas from separate files
from models import Base, Rainfall, Temperature, Pesticides, CropYield
from schemas import (
    RainfallCreate, RainfallUpdate, RainfallResponse,
    TemperatureCreate, TemperatureUpdate, TemperatureResponse,
    PesticidesCreate, PesticidesUpdate, PesticidesResponse,
    CropYieldCreate, CropYieldUpdate, CropYieldResponse,
    MLFeaturesCreate, MLFeaturesUpdate, MLFeaturesResponse
)

# Import training utilities from separate module
from train import (
    TrainRequest as TrainRequestModel,
    TrainResponse as TrainResponseModel,
    PredictRequest as PredictRequestModel,
    PredictResponse as PredictResponseModel,
    train_model,
    predict as predict_from_bundle,      # <-- correct alias
)

# Load environment variables
load_dotenv()

# =====================
# MYSQL CONFIGURATION
# =====================
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Rwanda1!")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "agriculture_db")

# Create MySQL connection string
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

# Create MySQL engine and session
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# =====================
# MONGODB CONFIGURATION (MongoDB Atlas)
# =====================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "agriculture_db")

# Create MongoDB client (supports both local and Atlas)
try:
    # Connect to MongoDB with proper timeout settings
    mongo_client = MongoClient(
        MONGO_URI, 
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    
    # Test connection with ping
    mongo_client.admin.command('ping')
    
    # Get database (works for both local and Atlas)
    mongo_db = mongo_client[MONGO_DATABASE]
    
    # Verify collections exist
    collections = mongo_db.list_collection_names()
    MONGODB_AVAILABLE = True
    
    print(f"✓ MongoDB Atlas connected successfully!")
    print(f"  Database: {MONGO_DATABASE}")
    print(f"  Collections: {', '.join(collections) if collections else 'No collections yet'}")
    
except Exception as e:
    mongo_client = None
    mongo_db = None
    MONGODB_AVAILABLE = False
    print(f"⚠ MongoDB not available: {e}")
    print(f"  Continuing with MySQL only...")

# =====================
# HELPER FUNCTIONS
# =====================

class NaNSafeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles NaN and Infinity values."""
    def encode(self, obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return 'null'
        return super().encode(obj)
    
    def iterencode(self, obj, _one_shot=False):
        """Encode while handling NaN values."""
        for chunk in super().iterencode(self._clean_data(obj), _one_shot):
            yield chunk
    
    def _clean_data(self, obj):
        """Recursively clean NaN and Inf values."""
        if isinstance(obj, dict):
            return {k: self._clean_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_data(item) for item in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
        return obj


def clean_nan_values(obj):
    """Replace NaN/Infinity values with None for JSON serialization."""
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj


def serialize_mongo_doc(doc):
    """Convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_mongo_doc(d) for d in doc]
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return clean_nan_values(doc)


# =====================
# FASTAPI APP SETUP
# =====================

# Custom JSON response class
class SafeJSONResponse(JSONResponse):
    """JSON response that handles NaN and Infinity values."""
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=NaNSafeJSONEncoder,
        ).encode("utf-8")


app = FastAPI(
    title="Agricultural Database API",
    description="CRUD API for managing agricultural data (Rainfall, Temperature, Pesticides, Crop Yield)",
    version="1.0.0",
    default_response_class=SafeJSONResponse,  # Use custom response class
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# DEPENDENCY
# =====================

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================
# HEALTH CHECK ENDPOINT
# =====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Check API health and database connections."""
    health_status = {
        "status": "healthy",
        "mysql": "disconnected",
        "mongodb": "disconnected"
    }
    
    # Check MySQL
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["mysql"] = "connected"
    except Exception as e:
        health_status["mysql"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check MongoDB
    if MONGODB_AVAILABLE and mongo_client:
        try:
            mongo_client.admin.command('ping')
            health_status["mongodb"] = "connected"
        except Exception as e:
            health_status["mongodb"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    else:
        health_status["mongodb"] = "not configured"
    
    # If MySQL is down, API is unhealthy
    if health_status["mysql"] != "connected":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


# =====================
# RAINFALL ENDPOINTS
# =====================

@app.post("/rainfall", response_model=RainfallResponse, tags=["Rainfall"], status_code=201)
async def create_rainfall(rainfall: RainfallCreate, db: Session = Depends(get_db)):
    """
    Create a new rainfall record.

    **Request Body:**
    - area: Area name (required)
    - year: Year (required)
    - average_rain_fall_mm_per_year: Rainfall in mm/year (optional)
    """
    db_rainfall = Rainfall(**rainfall.dict())
    db.add(db_rainfall)
    try:
        db.commit()
        db.refresh(db_rainfall)
        return db_rainfall
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create rainfall record: {str(e)}")


@app.get("/rainfall", response_model=List[RainfallResponse], tags=["Rainfall"])
async def read_rainfall(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    area: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve rainfall records with optional filtering.

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Number of records to return (default: 10, max: 100)
    - area: Filter by area name (optional)
    - year: Filter by year (optional)
    """
    query = db.query(Rainfall)
    
    if area:
        query = query.filter(Rainfall.area.ilike(f"%{area}%"))
    if year:
        query = query.filter(Rainfall.year == year)
    
    return query.offset(skip).limit(limit).all()


@app.get("/rainfall/{rainfall_id}", response_model=RainfallResponse, tags=["Rainfall"])
async def read_rainfall_by_id(rainfall_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific rainfall record by ID."""
    db_rainfall = db.query(Rainfall).filter(Rainfall.id == rainfall_id).first()
    if not db_rainfall:
        raise HTTPException(status_code=404, detail="Rainfall record not found")
    return db_rainfall


@app.put("/rainfall/{rainfall_id}", response_model=RainfallResponse, tags=["Rainfall"])
async def update_rainfall(
    rainfall_id: int,
    rainfall_update: RainfallUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing rainfall record.

    **Path Parameters:**
    - rainfall_id: ID of the rainfall record to update

    **Request Body:**
    - area: Area name (optional)
    - year: Year (optional)
    - average_rain_fall_mm_per_year: Rainfall in mm/year (optional)
    """
    db_rainfall = db.query(Rainfall).filter(Rainfall.id == rainfall_id).first()
    if not db_rainfall:
        raise HTTPException(status_code=404, detail="Rainfall record not found")
    
    update_data = rainfall_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rainfall, key, value)
    
    try:
        db.commit()
        db.refresh(db_rainfall)
        return db_rainfall
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update rainfall record: {str(e)}")


@app.delete("/rainfall/{rainfall_id}", tags=["Rainfall"], status_code=204)
async def delete_rainfall(rainfall_id: int, db: Session = Depends(get_db)):
    """Delete a rainfall record by ID."""
    db_rainfall = db.query(Rainfall).filter(Rainfall.id == rainfall_id).first()
    if not db_rainfall:
        raise HTTPException(status_code=404, detail="Rainfall record not found")
    
    try:
        db.delete(db_rainfall)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete rainfall record: {str(e)}")


# =====================
# TEMPERATURE ENDPOINTS
# =====================

@app.post("/temperature", response_model=TemperatureResponse, tags=["Temperature"], status_code=201)
async def create_temperature(temperature: TemperatureCreate, db: Session = Depends(get_db)):
    """
    Create a new temperature record.

    **Request Body:**
    - year: Year (required)
    - country: Country name (required)
    - avg_temp: Average temperature in Celsius (optional)
    """
    db_temperature = Temperature(**temperature.dict())
    db.add(db_temperature)
    try:
        db.commit()
        db.refresh(db_temperature)
        return db_temperature
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create temperature record: {str(e)}")


@app.get("/temperature", response_model=List[TemperatureResponse], tags=["Temperature"])
async def read_temperature(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    country: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve temperature records with optional filtering.

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Number of records to return (default: 10, max: 100)
    - country: Filter by country name (optional)
    - year: Filter by year (optional)
    """
    query = db.query(Temperature)
    
    if country:
        query = query.filter(Temperature.country.ilike(f"%{country}%"))
    if year:
        query = query.filter(Temperature.year == year)
    
    return query.offset(skip).limit(limit).all()


@app.get("/temperature/{temperature_id}", response_model=TemperatureResponse, tags=["Temperature"])
async def read_temperature_by_id(temperature_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific temperature record by ID."""
    db_temperature = db.query(Temperature).filter(Temperature.id == temperature_id).first()
    if not db_temperature:
        raise HTTPException(status_code=404, detail="Temperature record not found")
    return db_temperature


@app.put("/temperature/{temperature_id}", response_model=TemperatureResponse, tags=["Temperature"])
async def update_temperature(
    temperature_id: int,
    temperature_update: TemperatureUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing temperature record.

    **Path Parameters:**
    - temperature_id: ID of the temperature record to update

    **Request Body:**
    - year: Year (optional)
    - country: Country name (optional)
    - avg_temp: Average temperature (optional)
    """
    db_temperature = db.query(Temperature).filter(Temperature.id == temperature_id).first()
    if not db_temperature:
        raise HTTPException(status_code=404, detail="Temperature record not found")
    
    update_data = temperature_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_temperature, key, value)
    
    try:
        db.commit()
        db.refresh(db_temperature)
        return db_temperature
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update temperature record: {str(e)}")


@app.delete("/temperature/{temperature_id}", tags=["Temperature"], status_code=204)
async def delete_temperature(temperature_id: int, db: Session = Depends(get_db)):
    """Delete a temperature record by ID."""
    db_temperature = db.query(Temperature).filter(Temperature.id == temperature_id).first()
    if not db_temperature:
        raise HTTPException(status_code=404, detail="Temperature record not found")
    
    try:
        db.delete(db_temperature)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete temperature record: {str(e)}")


# =====================
# PESTICIDES ENDPOINTS
# =====================

@app.post("/pesticides", response_model=PesticidesResponse, tags=["Pesticides"], status_code=201)
async def create_pesticides(pesticides: PesticidesCreate, db: Session = Depends(get_db)):
    """
    Create a new pesticides record.

    **Request Body:**
    - area: Area name (required)
    - year: Year (required)
    - domain: Domain (optional)
    - element: Element (optional)
    - item: Item name (optional)
    - unit: Unit of measurement (optional)
    - value: Pesticide value (optional)
    """
    db_pesticides = Pesticides(**pesticides.dict())
    db.add(db_pesticides)
    try:
        db.commit()
        db.refresh(db_pesticides)
        return db_pesticides
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create pesticides record: {str(e)}")


@app.get("/pesticides", response_model=List[PesticidesResponse], tags=["Pesticides"])
async def read_pesticides(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    area: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    item: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve pesticides records with optional filtering.

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Number of records to return (default: 10, max: 100)
    - area: Filter by area name (optional)
    - year: Filter by year (optional)
    - item: Filter by item name (optional)
    """
    query = db.query(Pesticides)
    
    if area:
        query = query.filter(Pesticides.area.ilike(f"%{area}%"))
    if year:
        query = query.filter(Pesticides.year == year)
    if item:
        query = query.filter(Pesticides.item.ilike(f"%{item}%"))
    
    return query.offset(skip).limit(limit).all()


@app.get("/pesticides/{pesticides_id}", response_model=PesticidesResponse, tags=["Pesticides"])
async def read_pesticides_by_id(pesticides_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific pesticides record by ID."""
    db_pesticides = db.query(Pesticides).filter(Pesticides.id == pesticides_id).first()
    if not db_pesticides:
        raise HTTPException(status_code=404, detail="Pesticides record not found")
    return db_pesticides


@app.put("/pesticides/{pesticides_id}", response_model=PesticidesResponse, tags=["Pesticides"])
async def update_pesticides(
    pesticides_id: int,
    pesticides_update: PesticidesUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing pesticides record.

    **Path Parameters:**
    - pesticides_id: ID of the pesticides record to update

    **Request Body:**
    All fields are optional for partial updates
    """
    db_pesticides = db.query(Pesticides).filter(Pesticides.id == pesticides_id).first()
    if not db_pesticides:
        raise HTTPException(status_code=404, detail="Pesticides record not found")
    
    update_data = pesticides_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_pesticides, key, value)
    
    try:
        db.commit()
        db.refresh(db_pesticides)
        return db_pesticides
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update pesticides record: {str(e)}")


@app.delete("/pesticides/{pesticides_id}", tags=["Pesticides"], status_code=204)
async def delete_pesticides(pesticides_id: int, db: Session = Depends(get_db)):
    """Delete a pesticides record by ID."""
    db_pesticides = db.query(Pesticides).filter(Pesticides.id == pesticides_id).first()
    if not db_pesticides:
        raise HTTPException(status_code=404, detail="Pesticides record not found")
    
    try:
        db.delete(db_pesticides)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete pesticides record: {str(e)}")


# =====================
# CROP YIELD ENDPOINTS
# =====================

@app.post("/crop-yield", response_model=CropYieldResponse, tags=["Crop Yield"], status_code=201)
async def create_crop_yield(crop_yield: CropYieldCreate, db: Session = Depends(get_db)):
    """
    Create a new crop yield record.

    **Request Body:**
    - area: Area name (required)
    - item: Crop/Item name (required)
    - year: Year (required)
    - Other fields are optional
    """
    db_crop_yield = CropYield(**crop_yield.dict())
    db.add(db_crop_yield)
    try:
        db.commit()
        db.refresh(db_crop_yield)
        return db_crop_yield
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create crop yield record: {str(e)}")


@app.get("/crop-yield", response_model=List[CropYieldResponse], tags=["Crop Yield"])
async def read_crop_yield(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    area: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    item: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve crop yield records with optional filtering.

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Number of records to return (default: 10, max: 100)
    - area: Filter by area name (optional)
    - year: Filter by year (optional)
    - item: Filter by crop/item name (optional)
    """
    query = db.query(CropYield)
    
    if area:
        query = query.filter(CropYield.area.ilike(f"%{area}%"))
    if year:
        query = query.filter(CropYield.year == year)
    if item:
        query = query.filter(CropYield.item.ilike(f"%{item}%"))
    
    return query.offset(skip).limit(limit).all()


@app.get("/crop-yield/{crop_yield_id}", response_model=CropYieldResponse, tags=["Crop Yield"])
async def read_crop_yield_by_id(crop_yield_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific crop yield record by ID."""
    db_crop_yield = db.query(CropYield).filter(CropYield.id == crop_yield_id).first()
    if not db_crop_yield:
        raise HTTPException(status_code=404, detail="Crop yield record not found")
    return db_crop_yield


@app.put("/crop-yield/{crop_yield_id}", response_model=CropYieldResponse, tags=["Crop Yield"])
async def update_crop_yield(
    crop_yield_id: int,
    crop_yield_update: CropYieldUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing crop yield record.

    **Path Parameters:**
    - crop_yield_id: ID of the crop yield record to update

    **Request Body:**
    All fields are optional for partial updates
    """
    db_crop_yield = db.query(CropYield).filter(CropYield.id == crop_yield_id).first()
    if not db_crop_yield:
        raise HTTPException(status_code=404, detail="Crop yield record not found")
    
    update_data = crop_yield_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_crop_yield, key, value)
    
    try:
        db.commit()
        db.refresh(db_crop_yield)
        return db_crop_yield
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update crop yield record: {str(e)}")


@app.delete("/crop-yield/{crop_yield_id}", tags=["Crop Yield"], status_code=204)
async def delete_crop_yield(crop_yield_id: int, db: Session = Depends(get_db)):
    """Delete a crop yield record by ID."""
    db_crop_yield = db.query(CropYield).filter(CropYield.id == crop_yield_id).first()
    if not db_crop_yield:
        raise HTTPException(status_code=404, detail="Crop yield record not found")
    
    try:
        db.delete(db_crop_yield)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete crop yield record: {str(e)}")


# =====================
# MONGODB QUERY ENDPOINTS (Aggregations & Analytics)
# =====================

@app.get("/mongodb/rainfall", tags=["MongoDB Analytics"])
async def query_mongodb_rainfall(
    area: Optional[str] = Query(None, description="Filter by area"),
    year: Optional[int] = Query(None, description="Filter by year"),
    limit: int = Query(10, ge=1, le=100, description="Limit results")
):
    """Query rainfall data from MongoDB with filters."""
    if not MONGODB_AVAILABLE:
        raise HTTPException(status_code=503, detail="MongoDB is not available")
    
    try:
        query = {}
        if area:
            query['area'] = {'$regex': area, '$options': 'i'}
        if year:
            query['year'] = year
        
        results = list(mongo_db.rainfall.find(query).limit(limit))
        return {"count": len(results), "data": serialize_mongo_doc(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB query failed: {str(e)}")


@app.get("/mongodb/temperature", tags=["MongoDB Analytics"])
async def query_mongodb_temperature(
    country: Optional[str] = Query(None, description="Filter by country"),
    year: Optional[int] = Query(None, description="Filter by year"),
    limit: int = Query(10, ge=1, le=100, description="Limit results")
):
    """Query temperature data from MongoDB with filters."""
    if not MONGODB_AVAILABLE:
        raise HTTPException(status_code=503, detail="MongoDB is not available")
    
    try:
        query = {}
        if country:
            query['country'] = {'$regex': country, '$options': 'i'}
        if year:
            query['year'] = year
        
        results = list(mongo_db.temperature.find(query).limit(limit))
        return {"count": len(results), "data": serialize_mongo_doc(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB query failed: {str(e)}")


@app.get("/mongodb/aggregate/rainfall-by-area", tags=["MongoDB Analytics"])
async def aggregate_rainfall_by_area(limit: int = Query(10, ge=1, le=100)):
    """Get average rainfall grouped by area using MongoDB aggregation."""
    if not MONGODB_AVAILABLE:
        raise HTTPException(status_code=503, detail="MongoDB is not available")
    
    try:
        pipeline = [
            {
                '$group': {
                    '_id': '$area',
                    'avg_rainfall': {'$avg': '$average_rain_fall_mm_per_year'},
                    'min_rainfall': {'$min': '$average_rain_fall_mm_per_year'},
                    'max_rainfall': {'$max': '$average_rain_fall_mm_per_year'},
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'avg_rainfall': -1}},
            {'$limit': limit}
        ]
        
        results = list(mongo_db.rainfall.aggregate(pipeline))
        return {"count": len(results), "data": serialize_mongo_doc(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB aggregation failed: {str(e)}")


@app.get("/mongodb/aggregate/temperature-by-country", tags=["MongoDB Analytics"])
async def aggregate_temperature_by_country(limit: int = Query(10, ge=1, le=100)):
    """Get average temperature grouped by country using MongoDB aggregation."""
    if not MONGODB_AVAILABLE:
        raise HTTPException(status_code=503, detail="MongoDB is not available")
    
    try:
        pipeline = [
            {
                '$group': {
                    '_id': '$country',
                    'avg_temp': {'$avg': '$avg_temp'},
                    'min_temp': {'$min': '$avg_temp'},
                    'max_temp': {'$max': '$avg_temp'},
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'avg_temp': -1}},
            {'$limit': limit}
        ]
        
        results = list(mongo_db.temperature.aggregate(pipeline))
        return {"count": len(results), "data": serialize_mongo_doc(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB aggregation failed: {str(e)}")


@app.get("/mongodb/aggregate/crop-yield-by-item", tags=["MongoDB Analytics"])
async def aggregate_crop_yield_by_item(
    area: Optional[str] = Query(None, description="Filter by area"),
    limit: int = Query(10, ge=1, le=100)
):
    """Get average crop yield grouped by crop item using MongoDB aggregation."""
    if not MONGODB_AVAILABLE:
        raise HTTPException(status_code=503, detail="MongoDB is not available")
    
    try:
        match_stage = {}
        if area:
            match_stage['area'] = {'$regex': area, '$options': 'i'}
        
        pipeline = [
            {'$match': match_stage} if match_stage else {'$match': {}},
            {
                '$group': {
                    '_id': '$item',
                    'avg_yield': {'$avg': '$value'},
                    'min_yield': {'$min': '$value'},
                    'max_yield': {'$max': '$value'},
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'avg_yield': -1}},
            {'$limit': limit}
        ]
        
        results = list(mongo_db.crop_yield.aggregate(pipeline))
        return {"count": len(results), "data": serialize_mongo_doc(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB aggregation failed: {str(e)}")


# =====================
# ML FEATURES ENDPOINTS
# =====================

@app.post("/ml-features", response_model=MLFeaturesResponse, tags=["ML Features"], status_code=201)
async def create_ml_features(record: MLFeaturesCreate, db: Session = Depends(get_db)):
    """Create a new ML features record."""
    db_record = MLFeatures(**record.dict())
    db.add(db_record)
    try:
        db.commit()
        db.refresh(db_record)
        return db_record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create ML features record: {str(e)}")


@app.get("/ml-features", response_model=List[MLFeaturesResponse], tags=["ML Features"])
async def read_ml_features(
    skip: int = Query(0, ge=0),
    limit: int = Query(10000, le=100000),
    db: Session = Depends(get_db)
):
    """List ML features with pagination."""
    try:
        # Get total count first
        total = db.query(MLFeatures).count()
        print(total)
        
        # Fetch paginated results
        query = db.query(MLFeatures)
        results = query.offset(skip).limit(limit).all()
        
        if not results and skip == 0:
            raise HTTPException(status_code=404, detail="No ML features found")
            
        # Log pagination info
        logger.info(f"Fetched ml_features: skip={skip}, limit={limit}, returned={len(results)}, total={total}")
        print([r.__dict__ for r in results])
        return results
        
    except Exception as e:
        logger.exception("Error fetching ml_features")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    finally:
        db.close()


@app.get("/ml-features/{record_id}", response_model=MLFeaturesResponse, tags=["ML Features"])
async def read_ml_features_by_id(record_id: int, db: Session = Depends(get_db)):
    db_record = db.query(MLFeatures).filter(MLFeatures.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="ML features record not found")
    return db_record


@app.put("/ml-features/{record_id}", response_model=MLFeaturesResponse, tags=["ML Features"])
async def update_ml_features(record_id: int, record_update: MLFeaturesUpdate, db: Session = Depends(get_db)):
    db_record = db.query(MLFeatures).filter(MLFeatures.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="ML features record not found")
    update_data = record_update.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(db_record, k, v)
    try:
        db.commit()
        db.refresh(db_record)
        return db_record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update ML features record: {str(e)}")


@app.delete("/ml-features/{record_id}", tags=["ML Features"], status_code=204)
async def delete_ml_features(record_id: int, db: Session = Depends(get_db)):
    db_record = db.query(MLFeatures).filter(MLFeatures.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="ML features record not found")
    try:
        db.delete(db_record)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete ML features record: {str(e)}")


# =====================
# ML TRAIN / PREDICT
# =====================

# Use train.py implementations for training/prediction endpoints.
@app.post("/ml/train", response_model=TrainResponseModel, tags=["Machine Learning"])
async def train_model_endpoint(payload: TrainRequestModel, db: Session = Depends(get_db)):
    """
    Train a model using rows from the ml_features table.
    Delegates the actual training to train.train_model().
    """
    try:
        result = train_model(db, payload)
        return result
    except ValueError as e:
        # expected validation/usage errors from train.py
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")


@app.post("/ml/predict", response_model=PredictResponseModel, tags=["Machine Learning"])
async def predict_endpoint(payload: PredictRequestModel):
    """
    Predict using a saved model bundle.
    Delegates prediction to train.predict().
    """
    try:
        result = predict_from_bundle(payload)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
    
# -------------------------------------------------
# /ml/predict endpoint – make it return a scalar
# -------------------------------------------------
@app.post("/ml/predict", response_model=PredictResponseModel, tags=["Machine Learning"])
async def predict_endpoint(payload: PredictRequestModel):
    try:
        result = predict_from_bundle(payload)          # now returns PredictResponse
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

# =====================
# ROOT ENDPOINT
# =====================

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint with documentation links."""
    return {
        "message": "Welcome to Agricultural Database API",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "endpoints": {
            "rainfall": "/rainfall",
            "temperature": "/temperature",
            "pesticides": "/pesticides",
            "crop_yield": "/crop-yield",
            "health": "/health"
        }
    }
    
    
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
