from pydantic import BaseModel
from datetime import date


class Region(BaseModel):
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


class DepthRange(BaseModel):
    min: float
    max: float


class ArgoQueryRequest(BaseModel):
    parameter: str
    region: Region
    depth: DepthRange
    start_date: date
    end_date: date