"""
API endpoints for script management.
"""
import os
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Path, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from beanie import PydanticObjectId
import shutil

from app.models.script import Script, ScriptFormat
from app.schemas.script import ScriptCreate, ScriptUpdate, ScriptResponse, ScriptListResponse
from app.services.script_parser.base import ScriptParserBase
from app.services.script_parser.fountain import FountainParser
from app.core.config import settings
from app.core.security import get_current_user
from app.api.deps import get_script_parser

router = APIRouter()
logger = logging.getLogger("filmpro")


@router.post("", response_model=ScriptResponse, status_code=201)
async def create_script(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    production_id: uuid.UUID = Form(...),
    version: str = Form("1.0"),
    author: Optional[str] = Form(None),
    script_parser: ScriptParserBase = Depends(get_script_parser),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a new script and create a script record.
    """
    # Check if file size is within limits
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB
    max_size = settings.MAX_SCRIPT_SIZE_MB * 1024 * 1024
    
    chunks = []
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        chunks.append(chunk)
        file_size += len(chunk)
        if file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.MAX_SCRIPT_SIZE_MB}MB"
            )
    
    # Save file to disk
    os.makedirs(settings.SCRIPT_UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.SCRIPT_UPLOAD_DIR, f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}")
    
    with open(file_path, "wb") as f:
        for chunk in chunks:
            f.write(chunk)
    
    # Calculate hash for deduplication
    content_hash = ScriptParserBase.calculate_file_hash(file_path)
    
    # Check for duplicate script
    existing_script = await Script.find_one({"content_hash": content_hash, "production_id": production_id}).to_list()
    if existing_script:
        # Remove the uploaded file
        os.remove(file_path)
        raise HTTPException(
            status_code=409,
            detail=f"A script with the same content already exists with ID: {existing_script[0].id}"
        )
    
    # Detect format
    script_format = ScriptParserBase.detect_format(file_path)
    
    # Create script record
    script = Script(
        title=title,
        production_id=production_id,
        format=script_format,
        version=version,
        author=author,
        file_path=file_path,
        original_filename=file.filename,
        content_hash=content_hash,
        upload_date=datetime.utcnow(),
        modified_date=datetime.utcnow(),
        metadata={}
    )
    
    await script.insert()
    
    # Schedule parsing in background
    background_tasks.add_task(_parse_script_background, script.id, script_parser)
    
    return ScriptResponse(
        id=str(script.id),
        title=script.title,
        production_id=script.production_id,
        format=script.format,
        version=script.version,
        author=script.author,
        upload_date=script.upload_date,
        modified_date=script.modified_date,
        original_filename=script.original_filename,
        metadata=script.metadata,
        is_active=script.is_active,
        is_locked=script.is_locked
    )


@router.get("", response_model=ScriptListResponse)
async def list_scripts(
    production_id: Optional[uuid.UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    List scripts, optionally filtered by production ID.
    """
    query = {}
    if production_id:
        query["production_id"] = production_id
    
    total = await Script.find(query).count()
    scripts = await Script.find(query).skip(skip).limit(limit).to_list()
    
    return ScriptListResponse(
        scripts=[
            ScriptResponse(
                id=str(script.id),
                title=script.title,
                production_id=script.production_id,
                format=script.format,
                version=script.version,
                author=script.author,
                upload_date=script.upload_date,
                modified_date=script.modified_date,
                original_filename=script.original_filename,
                metadata=script.metadata,
                is_active=script.is_active,
                is_locked=script.is_locked
            ) for script in scripts
        ],
        total=total
    )


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: str = Path(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a script by ID.
    """
    try:
        script_obj_id = PydanticObjectId(script_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid script ID format")
    
    script = await Script.get(script_obj_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return ScriptResponse(
        id=str(script.id),
        title=script.title,
        production_id=script.production_id,
        format=script.format,
        version=script.version,
        author=script.author,
        upload_date=script.upload_date,
        modified_date=script.modified_date,
        original_filename=script.original_filename,
        metadata=script.metadata,
        is_active=script.is_active,
        is_locked=script.is_locked
    )


@router.patch("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_update: ScriptUpdate,
    script_id: str = Path(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a script's metadata.
    """
    try:
        script_obj_id = PydanticObjectId(script_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid script ID format")
    
    script = await Script.get(script_obj_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Prevent updates if script is locked
    if script.is_locked and not script_update.is_locked:
        raise HTTPException(status_code=403, detail="Script is locked and cannot be updated")
    
    update_data = script_update.dict(exclude_unset=True)
    if update_data:
        update_data["modified_date"] = datetime.utcnow()
        await script.update({"$set": update_data})
    
    # Refresh from database
    script = await Script.get(script_obj_id)
    
    return ScriptResponse(
        id=str(script.id),
        title=script.title,
        production_id=script.production_id,
        format=script.format,
        version=script.version,
        author=script.author,
        upload_date=script.upload_date,
        modified_date=script.modified_date,
        original_filename=script.original_filename,
        metadata=script.metadata,
        is_active=script.is_active,
        is_locked=script.is_locked
    )


@router.delete("/{script_id}", status_code=204)
async def delete_script(
    script_id: str = Path(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a script.
    """
    try:
        script_obj_id = PydanticObjectId(script_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid script ID format")
    
    script = await Script.get(script_obj_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Check if script is locked
    if script.is_locked:
        raise HTTPException(status_code=403, detail="Script is locked and cannot be deleted")
    
    # Delete the script file
    if os.path.exists(script.file_path):
        try:
            os.remove(script.file_path)
        except Exception as e:
            logger.error(f"Error deleting script file: {str(e)}")
    
    # Delete the script record
    await script.delete()
    
    return None


async def _parse_script_background(script_id: PydanticObjectId, parser: ScriptParserBase):
    """
    Background task to parse a script.
    
    Args:
        script_id: ID of the script to parse
        parser: Script parser instance
    """
    try:
        script = await Script.get(script_id)
        if not script:
            logger.error(f"Script {script_id} not found for parsing")
            return
        
        # Parse the script
        parsed_data = await parser.parse(script.file_path)
        
        # Update script metadata with parsed information
        metadata = script.metadata or {}
        metadata.update({
            "parsed": True,
            "parse_date": datetime.utcnow().isoformat(),
            "scene_count": len(parsed_data.get("scenes", [])),
            "character_count": len(parsed_data.get("characters", [])),
            "parse_metadata": parsed_data.get("metadata", {})
        })
        
        # Update the script record
        await script.update({"$set": {"metadata": metadata, "modified_date": datetime.utcnow()}})
        
        logger.info(f"Successfully parsed script {script_id}")
    except Exception as e:
        logger.exception(f"Error parsing script {script_id}: {str(e)}")