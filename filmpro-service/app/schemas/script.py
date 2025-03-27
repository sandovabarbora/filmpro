"""
Pydantic schemas for API requests and responses.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, UUID4
from enum import Enum
from app.models.script import ScriptFormat, ElementType


# Script Schemas
class ScriptCreate(BaseModel):
    """Schema for creating a new script."""
    title: str
    production_id: UUID4
    version: str = "1.0"
    author: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScriptUpdate(BaseModel):
    """Schema for updating a script."""
    title: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_locked: Optional[bool] = None


class ScriptResponse(BaseModel):
    """Schema for script response."""
    id: str
    title: str
    production_id: UUID4
    format: ScriptFormat
    version: str
    author: Optional[str] = None
    upload_date: datetime
    modified_date: datetime
    original_filename: str
    metadata: Dict[str, Any]
    is_active: bool
    is_locked: bool
    
    class Config:
        orm_mode = True


class ScriptListResponse(BaseModel):
    """Schema for list of scripts response."""
    scripts: List[ScriptResponse]
    total: int


# Scene Element Schemas
class SceneElementCreate(BaseModel):
    """Schema for creating a scene element."""
    scene_number: str
    element_type: ElementType
    name: str
    description: Optional[str] = None
    occurrences: List[int] = Field(default_factory=list)
    context: Optional[str] = None
    importance: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('importance')
    def validate_importance(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Importance must be between 0 and 1")
        return v


class SceneElementResponse(BaseModel):
    """Schema for scene element response."""
    id: str
    script_id: str
    scene_number: str
    element_type: ElementType
    name: str
    description: Optional[str] = None
    occurrences: List[int]
    context: Optional[str] = None
    importance: Optional[float] = None
    metadata: Dict[str, Any]
    
    class Config:
        orm_mode = True


# Scene Schemas
class SceneCreate(BaseModel):
    """Schema for creating a scene."""
    scene_number: str
    slug_line: str
    description: Optional[str] = None
    page_number: Optional[float] = None
    int_ext: Optional[str] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    duration_estimate: Optional[float] = None
    complexity_score: Optional[float] = None
    content: Optional[str] = None
    
    @validator('complexity_score')
    def validate_complexity(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Complexity score must be between 0 and 1")
        return v


class SceneResponse(BaseModel):
    """Schema for scene response."""
    id: str
    script_id: str
    scene_number: str
    slug_line: str
    description: Optional[str] = None
    page_number: Optional[float] = None
    int_ext: Optional[str] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    duration_estimate: Optional[float] = None
    complexity_score: Optional[float] = None
    content: Optional[str] = None
    characters: List[str]
    elements: List[str]
    
    class Config:
        orm_mode = True


# Breakdown Schemas
class BreakdownCreate(BaseModel):
    """Schema for creating a script breakdown."""
    script_id: str
    production_id: UUID4


class BreakdownResponse(BaseModel):
    """Schema for breakdown response."""
    id: str
    script_id: str
    production_id: UUID4
    created_at: datetime
    updated_at: datetime
    is_complete: bool
    progress: float
    scene_count: int
    page_count: Optional[float] = None
    estimated_duration: Optional[float] = None
    elements_by_type: Dict[ElementType, int]
    summary_statistics: Dict[str, Any]
    
    class Config:
        orm_mode = True


# Character Schemas
class CharacterCreate(BaseModel):
    """Schema for creating a character."""
    name: str
    gender: Optional[str] = None
    age_range: Optional[str] = None
    description: Optional[str] = None
    dialogue_count: int = 0
    word_count: int = 0
    scene_appearances: List[str] = Field(default_factory=list)
    character_relationships: Dict[str, float] = Field(default_factory=dict)
    dominant_emotions: Dict[str, float] = Field(default_factory=dict)
    importance_score: Optional[float] = None


class CharacterResponse(BaseModel):
    """Schema for character response."""
    id: str
    script_id: str
    name: str
    gender: Optional[str] = None
    age_range: Optional[str] = None
    description: Optional[str] = None
    dialogue_count: int
    word_count: int
    scene_appearances: List[str]
    character_relationships: Dict[str, float]
    dominant_emotions: Dict[str, float]
    importance_score: Optional[float] = None
    
    class Config:
        orm_mode = True


# Script Analysis Schemas
class AnalysisOptions(BaseModel):
    """Options for script analysis."""
    extract_characters: bool = True
    extract_locations: bool = True
    extract_props: bool = True
    extract_scene_elements: bool = True
    estimate_durations: bool = True
    analyze_character_emotions: bool = True
    analyze_scene_complexity: bool = True
    

class AnalysisRequest(BaseModel):
    """Request to analyze a script."""
    script_id: str
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)


class AnalysisResponse(BaseModel):
    """Response from script analysis."""
    breakdown_id: str
    script_id: str
    status: str
    message: str
    progress: float