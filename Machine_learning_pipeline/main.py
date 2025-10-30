"""
FastAPI application for CRUD operations on agricultural database.

Endpoints for managing Rainfall, Temperature, Pesticides, and Crop Yield data.
"""
import os
from typing import List, Optional
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =====================
# CONFIGURATION
# =====================
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "agriculture_db")

# Create MySQL connection string
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

# Create engine and session
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base for models
Base = declarative_base()

# =====================
# PYDANTIC MODELS (Schemas)
# =====================

# --- RAINFALL SCHEMAS ---
class RainfallBase(BaseModel):
    area: str = Field(..., min_length=1, description="Area name")
    year: int = Field(..., ge=1900, le=2100, description="Year")
    average_rain_fall_mm_per_year: Optional[float] = Field(None, ge=0, description="Average rainfall in mm/year")


class RainfallCreate(RainfallBase):
    pass


class RainfallUpdate(BaseModel):
    area: Optional[str] = None
    year: Optional[int] = None
    average_rain_fall_mm_per_year: Optional[float] = None


class RainfallResponse(RainfallBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- TEMPERATURE SCHEMAS ---
class TemperatureBase(BaseModel):
    year: int = Field(..., ge=1900, le=2100, description="Year")
    country: str = Field(..., min_length=1, description="Country name")
    avg_temp: Optional[float] = Field(None, description="Average temperature in Celsius")


class TemperatureCreate(TemperatureBase):
    pass


class TemperatureUpdate(BaseModel):
    year: Optional[int] = None
    country: Optional[str] = None
    avg_temp: Optional[float] = None


class TemperatureResponse(TemperatureBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- PESTICIDES SCHEMAS ---
class PesticidesBase(BaseModel):
    domain: Optional[str] = None
    area: str = Field(..., min_length=1, description="Area name")
    element: Optional[str] = None
    item: Optional[str] = None
    year: int = Field(..., ge=1900, le=2100, description="Year")
    unit: Optional[str] = None
    value: Optional[float] = None


class PesticidesCreate(PesticidesBase):
    pass


class PesticidesUpdate(BaseModel):
    domain: Optional[str] = None
    area: Optional[str] = None
    element: Optional[str] = None
    item: Optional[str] = None
    year: Optional[int] = None
    unit: Optional[str] = None
    value: Optional[float] = None


class PesticidesResponse(PesticidesBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- CROP YIELD SCHEMAS ---
class CropYieldBase(BaseModel):
    domain_code: Optional[str] = None
    domain: Optional[str] = None
    area_code: Optional[int] = None
    area: str = Field(..., min_length=1, description="Area name")
    element_code: Optional[int] = None
    element: Optional[str] = None
    item_code: Optional[int] = None
    item: str = Field(..., min_length=1, description="Item/Crop name")
    year_code: Optional[int] = None
    year: int = Field(..., ge=1900, le=2100, description="Year")
    unit: Optional[str] = None
    value: Optional[float] = None


class CropYieldCreate(CropYieldBase):
    pass


class CropYieldUpdate(BaseModel):
    domain_code: Optional[str] = None
    domain: Optional[str] = None
    area_code: Optional[int] = None
    area: Optional[str] = None
    element_code: Optional[int] = None
    element: Optional[str] = None
    item_code: Optional[int] = None
    item: Optional[str] = None
    year_code: Optional[int] = None
    year: Optional[int] = None
    unit: Optional[str] = None
    value: Optional[float] = None


class CropYieldResponse(CropYieldBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =====================
# SQLALCHEMY MODELS
# =====================

class Rainfall(Base):
    __tablename__ = "rainfall"
    id = Column(Integer, primary_key=True, index=True)
    area = Column(String(100), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    average_rain_fall_mm_per_year = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Temperature(Base):
    __tablename__ = "temperature"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    avg_temp = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Pesticides(Base):
    __tablename__ = "pesticides"
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(100), nullable=True)
    area = Column(String(100), nullable=False, index=True)
    element = Column(String(100), nullable=True)
    item = Column(String(100), nullable=True)
    year = Column(Integer, nullable=False, index=True)
    unit = Column(String(100), nullable=True)
    value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CropYield(Base):
    __tablename__ = "crop_yield"
    id = Column(Integer, primary_key=True, index=True)
    domain_code = Column(String(10), nullable=True)
    domain = Column(String(100), nullable=True)
    area_code = Column(Integer, nullable=True)
    area = Column(String(100), nullable=False, index=True)
    element_code = Column(Integer, nullable=True)
    element = Column(String(100), nullable=True)
    item_code = Column(Integer, nullable=True)
    item = Column(String(100), nullable=False)
    year_code = Column(Integer, nullable=True)
    year = Column(Integer, nullable=False, index=True)
    unit = Column(String(50), nullable=True)
    value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================
# FASTAPI APP SETUP
# =====================

app = FastAPI(
    title="Agricultural Database API",
    description="CRUD API for managing agricultural data (Rainfall, Temperature, Pesticides, Crop Yield)",
    version="1.0.0",
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
    """Check API health and database connection."""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")


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
