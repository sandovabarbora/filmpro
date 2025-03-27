"""
Database connection and initialization for the FILMPRO application.
"""
import logging
import motor.motor_asyncio
from beanie import init_beanie
from typing import List, Type

from app.models.script import Script, Scene, SceneElement, Character, ScriptBreakdown
from app.core.config import settings

logger = logging.getLogger("filmpro")


async def init_db():
    """
    Initialize database connection and Beanie ODM.
    """
    try:
        # Connect to MongoDB
        logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}")
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
        
        # Initialize Beanie with document models
        models: List[Type] = [Script, Scene, SceneElement, Character, ScriptBreakdown]
        await init_beanie(
            database=client[settings.MONGO_DB_NAME],
            document_models=models
        )
        
        logger.info(f"Connected to MongoDB database: {settings.MONGO_DB_NAME}")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def close_db(client):
    """
    Close database connection.
    """
    if client:
        logger.info("Closing MongoDB connection")
        client.close()