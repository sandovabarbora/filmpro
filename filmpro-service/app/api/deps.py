"""
API dependencies for the FILMPRO application.
"""
from typing import Generator
from fastapi import Depends

from app.services.script_parser.fountain import FountainParser
from app.services.script_analysis.element_extractor import ElementExtractor


async def get_script_parser() -> FountainParser:
    """
    Dependency to get a script parser.
    """
    return FountainParser()


async def get_element_extractor() -> ElementExtractor:
    """
    Dependency to get a script element extractor.
    """
    extractor = ElementExtractor()
    await extractor.initialize()
    return extractor