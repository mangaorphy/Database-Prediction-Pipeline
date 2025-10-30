"""SQLAlchemy ORM models for database tables."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Rainfall(Base):
    """SQLAlchemy model for rainfall table."""
    __tablename__ = "rainfall"

    id = Column(Integer, primary_key=True, index=True)
    area = Column(String(100), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    average_rain_fall_mm_per_year = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('area', 'year', name='uk_rainfall_area_year'),
        Index('idx_rainfall_area_year', 'area', 'year'),
    )


class Temperature(Base):
    """SQLAlchemy model for temperature table."""
    __tablename__ = "temperature"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    avg_temp = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_temperature_country_year', 'country', 'year'),
    )


class Pesticides(Base):
    """SQLAlchemy model for pesticides table."""
    __tablename__ = "pesticides"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(100), nullable=True)
    area = Column(String(100), nullable=False, index=True)
    element = Column(String(100), nullable=True)
    item = Column(String(100), nullable=True)
    year = Column(Integer, nullable=False, index=True)
    unit = Column(String(100), nullable=True)
    value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_pesticides_area_year', 'area', 'year'),
    )


class CropYield(Base):
    """SQLAlchemy model for crop_yield table."""
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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_crop_yield_area_year_item', 'area', 'year', 'item'),
    )
