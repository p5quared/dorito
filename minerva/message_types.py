from typing import Iterable
from fastembed.common.types import NumpyArray
from pydantic import BaseModel
from enum import Enum


class EventType(str, Enum):
    RESERVOIR_RAW = "reservoir.raw"
    TRAWL_RAW = "trawl.raw"


class EventMetadata(BaseModel):
    correlation_id: str
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

class KeyWordProducedEvent(BaseModel):
    meta: EventMetadata
    data: KeyWordResult

class EmbeddingResult(BaseModel):
    keyword: str
    embedding: list[float]

class PyABSAResult(BaseModel):
    keyword: str
    sentiment: int # -1, 0, 1
    confidence: float # 0 to 1 

class PyABSAProducedEvent(BaseModel):
    meta: EventMetadata
    data: PyABSAResult
