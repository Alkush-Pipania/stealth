from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EmbedRequest(BaseModel):
    user_id: str
    azure_url: str


class EmbedResponse(BaseModel):
    user_id: str
    azure_url: str
    status: str
    embeddings: Optional[Dict[str, Any]] = None
    error: Optional[str] = None



# ------------------------------------------------------------



class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    CHART = "chart"

class Entity(BaseModel):
    name: str
    type: str
    properties: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None

class Relationship(BaseModel):
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = {}

class DocumentChunk(BaseModel):
    id: str
    content: str
    content_type: ContentType
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    image_path: Optional[str] = None
    
class GraphContext(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]
    chunks: List[DocumentChunk]