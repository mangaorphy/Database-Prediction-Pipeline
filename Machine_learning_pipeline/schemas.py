"""Pydantic models for API request/response validation."""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


# =====================
# RAINFALL MODELS
# =====================
class RainfallBase(BaseModel):
    """Base model for rainfall data."""
    area: str = Field(..., min_length=1, description="Area name")
    year: int = Field(..., ge=1900, le=2100, description="Year")
    average_rain_fall_mm_per_year: Optional[float] = Field(None, ge=0, description="Average rainfall in mm/year")


class RainfallCreate(RainfallBase):
    """Model for creating rainfall data."""
    pass


class RainfallUpdate(BaseModel):
    """Model for updating rainfall data."""
    area: Optional[str] = None
    year: Optional[int] = None
    average_rain_fall_mm_per_year: Optional[float] = None


class RainfallResponse(RainfallBase):
    """Model for rainfall response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =====================
# TEMPERATURE MODELS
# =====================
class TemperatureBase(BaseModel):
    """Base model for temperature data."""
    year: int = Field(..., ge=1900, le=2100, description="Year")
    country: str = Field(..., min_length=1, description="Country name")
    avg_temp: Optional[float] = Field(None, description="Average temperature in Celsius")


class TemperatureCreate(TemperatureBase):
    """Model for creating temperature data."""
    pass


class TemperatureUpdate(BaseModel):
    """Model for updating temperature data."""
    year: Optional[int] = None
    country: Optional[str] = None
    avg_temp: Optional[float] = None


class TemperatureResponse(TemperatureBase):
    """Model for temperature response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =====================
# PESTICIDES MODELS
# =====================
class PesticidesBase(BaseModel):
    """Base model for pesticides data."""
    domain: Optional[str] = None
    area: str = Field(..., min_length=1, description="Area name")
    element: Optional[str] = None
    item: Optional[str] = None
    year: int = Field(..., ge=1900, le=2100, description="Year")
    unit: Optional[str] = None
    value: Optional[float] = None


class PesticidesCreate(PesticidesBase):
    """Model for creating pesticides data."""
    pass


class PesticidesUpdate(BaseModel):
    """Model for updating pesticides data."""
    domain: Optional[str] = None
    area: Optional[str] = None
    element: Optional[str] = None
    item: Optional[str] = None
    year: Optional[int] = None
    unit: Optional[str] = None
    value: Optional[float] = None


class PesticidesResponse(PesticidesBase):
    """Model for pesticides response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =====================
# CROP YIELD MODELS
# =====================
class CropYieldBase(BaseModel):
    """Base model for crop yield data."""
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
    """Model for creating crop yield data."""
    pass


class CropYieldUpdate(BaseModel):
    """Model for updating crop yield data."""
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
    """Model for crop yield response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
