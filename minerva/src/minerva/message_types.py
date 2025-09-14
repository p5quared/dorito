from pydantic import BaseModel
from enum import Enum


class EventType(str, Enum):
    RESERVOIR_RAW = "reservoir.raw"
    TRAWL_RAW = "trawl.raw"


class EventMetadata(BaseModel):
    correlation_id: str
    event_type: EventType
    source_date: str


class RawData(BaseModel):
    id: str
    body: str


class KeyWordResult(BaseModel):
    keyword: str
    confidence: float


class RawDataProducedEvent(BaseModel):
    meta: EventMetadata
    data: RawData
