"""
Database models for the Script and Breakdown objects.
Using Pydantic models with MongoDB through Beanie ODM.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID, uuid4
from beanie import Document, Link, Insert, Replace, PydanticObjectId


class ScriptFormat(str, Enum):
    """Supported script formats."""
    FOUNTAIN = "fountain"
    PDF = "pdf"
    FINAL_DRAFT = "final_draft"
    PLAIN_TEXT = "plain_text"


class ElementType(str, Enum):
    """Types of elements that can be extracted from a script."""
    CHARACTER = "character"
    LOCATION = "location"
    PROP = "prop"
    WARDROBE = "wardrobe"
    VEHICLE = "vehicle"
    SPECIAL_EFFECT = "special_effect"
    MAKEUP = "makeup"
    ANIMAL = "animal"
    CAST = "cast"
    STUNT = "stunt"
    SOUND = "sound"
    MUSIC = "music"
    CAMERA = "camera"
    LIGHTING = "lighting"
    OTHER = "other"


class Script(Document):
    """Script document model."""
    title: str
    production_id: UUID
    format: ScriptFormat
    version: str
    author: Optional[str] = None
    upload_date: datetime = datetime.utcnow()
    modified_date: datetime = datetime.utcnow()
    file_path: str
    original_filename: str
    content_hash: str  # MD5 hash of file content for deduplication
    metadata: Dict[str, Any] = {}
    is_active: bool = True
    is_locked: bool = False
    
    class Settings:
        name = "scripts"
        indexes = [
            "production_id",
            ("production_id", "version"),
            "content_hash"
        ]


class SceneElement(Document):
    """An element extracted from a scene."""
    script_id: PydanticObjectId
    scene_number: str
    element_type: ElementType
    name: str
    description: Optional[str] = None
    occurrences: List[int] = []  # Page/line numbers where element appears
    context: Optional[str] = None
    importance: Optional[float] = None  # 0-1 score of importance
    metadata: Dict[str, Any] = {}
    
    class Settings:
        name = "scene_elements"
        indexes = [
            "script_id",
            ("script_id", "element_type"),
            ("script_id", "scene_number")
        ]


class Scene(Document):
    """A scene extracted from a script."""
    script_id: PydanticObjectId
    scene_number: str
    slug_line: str
    description: Optional[str] = None
    page_number: Optional[float] = None
    int_ext: Optional[str] = None  # INT/EXT
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    characters: List[PydanticObjectId] = []  # References to Character elements
    elements: List[PydanticObjectId] = []  # References to other SceneElements
    duration_estimate: Optional[float] = None  # Estimated duration in minutes
    complexity_score: Optional[float] = None  # 0-1 score of scene complexity
    content: Optional[str] = None  # Full text content of the scene
    
    class Settings:
        name = "scenes"
        indexes = [
            "script_id",
            ("script_id", "scene_number")
        ]


class ScriptBreakdown(Document):
    """Overall breakdown of a script."""
    script_id: PydanticObjectId
    production_id: UUID
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    is_complete: bool = False
    progress: float = 0.0  # 0-1 progress of breakdown process
    scene_count: int = 0
    page_count: Optional[float] = None
    estimated_duration: Optional[float] = None  # in minutes
    elements_by_type: Dict[ElementType, int] = {}  # Count of elements by type
    summary_statistics: Dict[str, Any] = {}
    
    class Settings:
        name = "script_breakdowns"
        indexes = [
            "script_id",
            "production_id"
        ]


class Character(Document):
    """A character extracted from a script."""
    script_id: PydanticObjectId
    name: str
    gender: Optional[str] = None
    age_range: Optional[str] = None
    description: Optional[str] = None
    dialogue_count: int = 0
    word_count: int = 0
    scene_appearances: List[str] = []  # List of scene numbers
    character_relationships: Dict[str, float] = {}  # Other characters and interaction strength
    dominant_emotions: Dict[str, float] = {}  # Emotions and their prevalence
    importance_score: Optional[float] = None  # 0-1 score of character importance
    
    class Settings:
        name = "characters"
        indexes = [
            "script_id",
            ("script_id", "name")
        ]