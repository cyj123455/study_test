from pydantic import BaseModel
from typing import Optional
from datetime import date


class WeatherRecordCreate(BaseModel):
    origin: str
    record_date: date
    temp_avg: Optional[float] = None
    precipitation: Optional[float] = None
    sunshine_hours: Optional[float] = None
    extreme_weather: str = "无极端天气"


class WeatherRecordResponse(BaseModel):
    id: int
    origin: str
    record_date: date
    temp_avg: Optional[float] = None
    precipitation: Optional[float] = None
    sunshine_hours: Optional[float] = None
    extreme_weather: str

    class Config:
        from_attributes = True
