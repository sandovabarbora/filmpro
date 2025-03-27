"""
Base class for script parsers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import hashlib
import logging

from app.models.script import Script, ScriptFormat

logger = logging.getLogger("filmpro")


class ScriptParserBase(ABC):
    """Base class for all script parsers."""
    
    @abstractmethod
    async def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a script file and return structured data.
        
        Args:
            file_path: Path to the script file
            
        Returns:
            Dictionary with parsed script data including:
            - scenes: List of scene dictionaries
            - characters: List of character dictionaries
            - metadata: Dictionary of script metadata
        """
        pass
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """
        Calculate MD5 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 hash string
        """
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    @staticmethod
    def detect_format(file_path: str) -> ScriptFormat:
        """
        Detect the format of a script file.
        
        Args:
            file_path: Path to the script file
            
        Returns:
            Detected script format
        """
        suffix = Path(file_path).suffix.lower()
        
        if suffix == ".fountain" or suffix == ".spmd":
            return ScriptFormat.FOUNTAIN
        elif suffix == ".pdf":
            return ScriptFormat.PDF
        elif suffix == ".fdx":
            return ScriptFormat.FINAL_DRAFT
        else:
            # Try to detect format by content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(1000)  # Read first 1000 chars
                
                # Check for Final Draft XML
                if "<?xml" in content and "<FinalDraft" in content:
                    return ScriptFormat.FINAL_DRAFT
                
                # Check for Fountain markers
                if "INT." in content or "EXT." in content:
                    if "FADE IN:" in content or "CUT TO:" in content:
                        return ScriptFormat.FOUNTAIN
            
            # Default to plain text if we can't determine
            return ScriptFormat.PLAIN_TEXT
    
    @staticmethod
    def extract_scene_heading(line: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract components from a scene heading.
        
        Args:
            line: Scene heading line (e.g., "INT. LIVING ROOM - DAY")
            
        Returns:
            Tuple of (int_ext, location, time_of_day)
        """
        line = line.strip()
        
        # Default values
        int_ext = None
        location = None
        time_of_day = None
        
        # Check for INT/EXT
        if line.startswith("INT."):
            int_ext = "INT"
            line = line[4:].strip()
        elif line.startswith("EXT."):
            int_ext = "EXT"
            line = line[4:].strip()
        elif line.startswith("INT/EXT.") or line.startswith("I/E."):
            int_ext = "INT/EXT"
            line = line[line.find(".")+1:].strip()
        
        # Split by dash to separate location and time
        parts = line.split(" - ")
        if len(parts) > 1:
            location = parts[0].strip()
            time_of_day = parts[1].strip()
        else:
            location = line.strip()
        
        return int_ext, location, time_of_day