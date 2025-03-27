"""
API endpoints for script breakdown management.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, Query, BackgroundTasks
from beanie import PydanticObjectId

from app.models.script import Script, ScriptBreakdown, Scene, SceneElement, Character, ElementType
from app.schemas.script import (
    BreakdownCreate, BreakdownResponse, SceneResponse, SceneElementResponse, 
    CharacterResponse, AnalysisRequest, AnalysisResponse, AnalysisOptions
)
from app.services.script_analysis.element_extractor import ElementExtractor
from app.core.security import get_current_user
from app.api.deps import get_element_extractor

router = APIRouter()
logger = logging.getLogger("filmpro")


@router.post("", response_model=BreakdownResponse, status_code=201)
async def create_breakdown(
    breakdown_create: BreakdownCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    element_extractor: ElementExtractor = Depends(get_element_extractor)
):
    """
    Create a new script breakdown.
    """
    # Verify script exists
    try:
        script_obj_id = PydanticObjectId(breakdown_create.script_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid script ID format")
    
    script = await Script.get(script_obj_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Check if breakdown already exists
    existing_breakdown = await ScriptBreakdown.find_one({"script_id": script_obj_id}).to_list()
    if existing_breakdown:
        raise HTTPException(
            status_code=409,
            detail=f"A breakdown for this script already exists with ID: {existing_breakdown[0].id}"
        )
    
    # Create breakdown record
    breakdown = ScriptBreakdown(
        script_id=script_obj_id,
        production_id=breakdown_create.production_id,
        is_complete=False,
        progress=0.0,
        scene_count=0,
        elements_by_type={},
        summary_statistics={}
    )
    
    await breakdown.insert()
    
    # Start breakdown process in background
    background_tasks.add_task(
        _process_breakdown_background,
        breakdown.id,
        script.id,
        element_extractor
    )
    
    return BreakdownResponse(
        id=str(breakdown.id),
        script_id=str(breakdown.script_id),
        production_id=breakdown.production_id,
        created_at=breakdown.created_at,
        updated_at=breakdown.updated_at,
        is_complete=breakdown.is_complete,
        progress=breakdown.progress,
        scene_count=breakdown.scene_count,
        page_count=breakdown.page_count,
        estimated_duration=breakdown.estimated_duration,
        elements_by_type=breakdown.elements_by_type,
        summary_statistics=breakdown.summary_statistics
    )


@router.get("/{breakdown_id}", response_model=BreakdownResponse)
async def get_breakdown(
    breakdown_id: str = Path(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a script breakdown by ID.
    """
    try:
        breakdown_obj_id = PydanticObjectId(breakdown_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid breakdown ID format")
    
    breakdown = await ScriptBreakdown.get(breakdown_obj_id)
    if not breakdown:
        raise HTTPException(status_code=404, detail="Breakdown not found")
    
    return BreakdownResponse(
        id=str(breakdown.id),
        script_id=str(breakdown.script_id),
        production_id=breakdown.production_id,
        created_at=breakdown.created_at,
        updated_at=breakdown.updated_at,
        is_complete=breakdown.is_complete,
        progress=breakdown.progress,
        scene_count=breakdown.scene_count,
        page_count=breakdown.page_count,
        estimated_duration=breakdown.estimated_duration,
        elements_by_type=breakdown.elements_by_type,
        summary_statistics=breakdown.summary_statistics
    )


@router.get("/script/{script_id}", response_model=BreakdownResponse)
async def get_breakdown_by_script(
    script_id: str = Path(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a script breakdown by script ID.
    """
    try:
        script_obj_id = PydanticObjectId(script_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid script ID format")
    
    breakdown = await ScriptBreakdown.find_one({"script_id": script_obj_id})
    if not breakdown:
        raise HTTPException(status_code=404, detail="Breakdown not found for this script")
    
    return BreakdownResponse(
        id=str(breakdown.id),
        script_id=str(breakdown.script_id),
        production_id=breakdown.production_id,
        created_at=breakdown.created_at,
        updated_at=breakdown.updated_at,
        is_complete=breakdown.is_complete,
        progress=breakdown.progress,
        scene_count=breakdown.scene_count,
        page_count=breakdown.page_count,
        estimated_duration=breakdown.estimated_duration,
        elements_by_type=breakdown.elements_by_type,
        summary_statistics=breakdown.summary_statistics
    )


@router.get("/{breakdown_id}/scenes", response_model=List[SceneResponse])
async def get_breakdown_scenes(
    breakdown_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get scenes from a script breakdown.
    """
    try:
        breakdown_obj_id = PydanticObjectId(breakdown_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid breakdown ID format")
    
    breakdown = await ScriptBreakdown.get(breakdown_obj_id)
    if not breakdown:
        raise HTTPException(status_code=404, detail="Breakdown not found")
    
    scenes = await Scene.find({"script_id": breakdown.script_id}).skip(skip).limit(limit).to_list()
    
    return [
        SceneResponse(
            id=str(scene.id),
            script_id=str(scene.script_id),
            scene_number=scene.scene_number,
            slug_line=scene.slug_line,
            description=scene.description,
            page_number=scene.page_number,
            int_ext=scene.int_ext,
            location=scene.location,
            time_of_day=scene.time_of_day,
            duration_estimate=scene.duration_estimate,
            complexity_score=scene.complexity_score,
            content=scene.content,
            characters=[str(char_id) for char_id in scene.characters],
            elements=[str(elem_id) for elem_id in scene.elements]
        ) for scene in scenes
    ]


@router.get("/{breakdown_id}/elements/{element_type}", response_model=List[SceneElementResponse])
async def get_breakdown_elements(
    breakdown_id: str = Path(...),
    element_type: ElementType = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get elements of a specific type from a script breakdown.
    """
    try:
        breakdown_obj_id = PydanticObjectId(breakdown_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid breakdown ID format")
    
    breakdown = await ScriptBreakdown.get(breakdown_obj_id)
    if not breakdown:
        raise HTTPException(status_code=404, detail="Breakdown not found")
    
    elements = await SceneElement.find(
        {"script_id": breakdown.script_id, "element_type": element_type}
    ).skip(skip).limit(limit).to_list()
    
    return [
        SceneElementResponse(
            id=str(element.id),
            script_id=str(element.script_id),
            scene_number=element.scene_number,
            element_type=element.element_type,
            name=element.name,
            description=element.description,
            occurrences=element.occurrences,
            context=element.context,
            importance=element.importance,
            metadata=element.metadata
        ) for element in elements
    ]


@router.get("/{breakdown_id}/characters", response_model=List[CharacterResponse])
async def get_breakdown_characters(
    breakdown_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get characters from a script breakdown.
    """
    try:
        breakdown_obj_id = PydanticObjectId(breakdown_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid breakdown ID format")
    
    breakdown = await ScriptBreakdown.get(breakdown_obj_id)
    if not breakdown:
        raise HTTPException(status_code=404, detail="Breakdown not found")
    
    characters = await Character.find({"script_id": breakdown.script_id}).skip(skip).limit(limit).to_list()
    
    return [
        CharacterResponse(
            id=str(character.id),
            script_id=str(character.script_id),
            name=character.name,
            gender=character.gender,
            age_range=character.age_range,
            description=character.description,
            dialogue_count=character.dialogue_count,
            word_count=character.word_count,
            scene_appearances=character.scene_appearances,
            character_relationships=character.character_relationships,
            dominant_emotions=character.dominant_emotions,
            importance_score=character.importance_score
        ) for character in characters
    ]


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_script(
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    element_extractor: ElementExtractor = Depends(get_element_extractor)
):
    """
    Analyze a script and create or update its breakdown.
    """
    try:
        script_obj_id = PydanticObjectId(analysis_request.script_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid script ID format")
    
    script = await Script.get(script_obj_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Check if breakdown exists
    breakdown = await ScriptBreakdown.find_one({"script_id": script_obj_id})
    
    # If breakdown doesn't exist, create it
    if not breakdown:
        breakdown = ScriptBreakdown(
            script_id=script_obj_id,
            production_id=script.production_id,
            is_complete=False,
            progress=0.0,
            scene_count=0,
            elements_by_type={},
            summary_statistics={}
        )
        await breakdown.insert()
    else:
        # Reset progress if reanalyzing
        await breakdown.update({"$set": {"progress": 0.0, "is_complete": False}})
    
    # Start analysis in background
    background_tasks.add_task(
        _process_breakdown_background,
        breakdown.id,
        script.id,
        element_extractor,
        analysis_request.options
    )
    
    return AnalysisResponse(
        breakdown_id=str(breakdown.id),
        script_id=str(script.id),
        status="processing",
        message="Script analysis started",
        progress=0.0
    )


async def _process_breakdown_background(
    breakdown_id: PydanticObjectId,
    script_id: PydanticObjectId,
    element_extractor: ElementExtractor,
    options: Optional[AnalysisOptions] = None
):
    """
    Process script breakdown in the background.
    
    Args:
        breakdown_id: Breakdown ID
        script_id: Script ID
        element_extractor: Element extractor service
        options: Analysis options
    """
    try:
        # Get script and breakdown
        script = await Script.get(script_id)
        if not script:
            logger.error(f"Script {script_id} not found for breakdown")
            return
        
        breakdown = await ScriptBreakdown.get(breakdown_id)
        if not breakdown:
            logger.error(f"Breakdown {breakdown_id} not found")
            return
        
        # Update progress
        await breakdown.update({"$set": {"progress": 0.1}})
        
        # Check if script has been parsed
        if not script.metadata.get("parsed"):
            logger.error(f"Script {script_id} has not been parsed yet")
            await breakdown.update({
                "$set": {
                    "progress": 0.0,
                    "is_complete": False,
                    "summary_statistics": {"error": "Script has not been parsed yet"}
                }
            })
            return
        
        # Load script parser for the appropriate format
        if script.format == "fountain":
            from app.services.script_parser.fountain import FountainParser
            parser = FountainParser()
        else:
            logger.error(f"Unsupported script format: {script.format}")
            await breakdown.update({
                "$set": {
                    "progress": 0.0,
                    "is_complete": False,
                    "summary_statistics": {"error": f"Unsupported script format: {script.format}"}
                }
            })
            return
        
        # Parse script
        parsed_data = await parser.parse(script.file_path)
        
        # Update progress
        await breakdown.update({"$set": {"progress": 0.3}})
        
        # Store scenes
        scene_count = len(parsed_data.get("scenes", []))
        for i, scene_data in enumerate(parsed_data.get("scenes", [])):
            # Create or update scene
            scene = await Scene.find_one({"script_id": script_id, "scene_number": scene_data["scene_number"]})
            if not scene:
                scene = Scene(
                    script_id=script_id,
                    scene_number=scene_data["scene_number"],
                    slug_line=scene_data["slug_line"],
                    page_number=scene_data.get("page_number"),
                    int_ext=scene_data.get("int_ext"),
                    location=scene_data.get("location"),
                    time_of_day=scene_data.get("time_of_day"),
                    content=scene_data.get("content"),
                    characters=[],
                    elements=[]
                )
                await scene.insert()
        
        # Update progress
        await breakdown.update({"$set": {"progress": 0.5, "scene_count": scene_count}})
        
        # Extract elements
        extracted_elements = await element_extractor.extract_elements(parsed_data)
        
        # Update progress
        await breakdown.update({"$set": {"progress": 0.7}})
        
        # Store elements
        elements_by_type = {}
        for element_type, elements in extracted_elements.items():
            elements_by_type[element_type] = len(elements)
            
            for element_data in elements:
                if element_type == ElementType.CHARACTER:
                    # Store characters in the Character collection
                    character = await Character.find_one({"script_id": script_id, "name": element_data["name"]})
                    if not character:
                        character = Character(
                            script_id=script_id,
                            name=element_data["name"],
                            scene_appearances=[str(scene_num) for scene_num in element_data.get("occurrences", [])],
                            importance_score=element_data.get("importance")
                        )
                        await character.insert()
                else:
                    # Store other elements in the SceneElement collection
                    for scene_num in element_data.get("occurrences", []):
                        if scene_num != "unknown":
                            element = SceneElement(
                                script_id=script_id,
                                scene_number=str(scene_num),
                                element_type=element_type,
                                name=element_data["name"],
                                description=element_data.get("description"),
                                occurrences=[scene_num],
                                context=element_data.get("context"),
                                importance=element_data.get("importance"),
                                metadata={}
                            )
                            await element.insert()
        
        # Calculate summary statistics
        page_count = max([scene.get("page_number", 0) for scene in parsed_data.get("scenes", []) if scene.get("page_number")], default=0)
        estimated_duration = page_count * 1.0  # Rough estimate: 1 minute per page
        
        # Finalize breakdown
        await breakdown.update({
            "$set": {
                "progress": 1.0,
                "is_complete": True,
                "page_count": page_count,
                "estimated_duration": estimated_duration,
                "elements_by_type": elements_by_type,
                "summary_statistics": {
                    "scene_count": scene_count,
                    "page_count": page_count,
                    "estimated_duration": estimated_duration,
                    "character_count": len(extracted_elements.get(ElementType.CHARACTER, [])),
                    "location_count": len(extracted_elements.get(ElementType.LOCATION, [])),
                    "prop_count": len(extracted_elements.get(ElementType.PROP, [])),
                }
            }
        })
        
        logger.info(f"Successfully processed breakdown {breakdown_id} for script {script_id}")
    except Exception as e:
        logger.exception(f"Error processing breakdown {breakdown_id} for script {script_id}: {str(e)}")
        # Update breakdown with error
        try:
            await ScriptBreakdown.get(breakdown_id).update({
                "$set": {
                    "progress": 0.0,
                    "is_complete": False,
                    "summary_statistics": {"error": str(e)}
                }
            })
        except Exception as update_error:
            logger.error(f"Error updating breakdown with error status: {str(update_error)}")