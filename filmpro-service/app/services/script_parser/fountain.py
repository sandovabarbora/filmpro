"""
Parser for Fountain format scripts.
Fountain is a plain text markup format for screenplays.
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

from app.services.script_parser.base import ScriptParserBase

logger = logging.getLogger("filmpro")


class FountainParser(ScriptParserBase):
    """Parser for Fountain format scripts."""
    
    # Regular expressions for parsing
    SCENE_HEADING_PATTERN = re.compile(r'^(INT|EXT|I/E|INT/EXT)[\./].*$', re.IGNORECASE)
    CHARACTER_PATTERN = re.compile(r'^[A-Z\s]+$')
    PARENTHETICAL_PATTERN = re.compile(r'^\(.*\)$')
    TRANSITION_PATTERN = re.compile(r'^(FADE|CUT|DISSOLVE|SMASH|WIPE|IRIS|JUMP).*$', re.IGNORECASE)
    PAGE_BREAK_PATTERN = re.compile(r'^==+$')
    SCENE_NUMBER_PATTERN = re.compile(r'#(.+)#')
    
    async def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Fountain script file.
        
        Args:
            file_path: Path to the Fountain script file
            
        Returns:
            Dictionary with parsed script data
        """
        logger.info(f"Parsing Fountain script: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Split the script into lines
        lines = content.split('\n')
        
        # Initialize data structures
        scenes = []
        characters = {}
        current_scene = None
        current_character = None
        current_dialogue = None
        in_dialogue = False
        scene_number_counter = 1
        page_number = 1
        metadata = self._extract_metadata(lines)
        
        # Process the script line by line
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Page breaks
            if self.PAGE_BREAK_PATTERN.match(line):
                page_number += 1
                continue
            
            # Scene headings
            if self.SCENE_HEADING_PATTERN.match(line) or line.startswith('.'):
                # If we were in a scene, save it
                if current_scene:
                    scenes.append(current_scene)
                
                # Extract scene number if present
                scene_number = str(scene_number_counter)
                scene_number_match = self.SCENE_NUMBER_PATTERN.search(line)
                if scene_number_match:
                    scene_number = scene_number_match.group(1)
                    line = self.SCENE_NUMBER_PATTERN.sub('', line).strip()
                
                # Remove leading dot if forced scene heading
                if line.startswith('.'):
                    line = line[1:].strip()
                
                # Extract INT/EXT, location, time of day
                int_ext, location, time_of_day = self.extract_scene_heading(line)
                
                # Create new scene
                current_scene = {
                    'scene_number': scene_number,
                    'slug_line': line,
                    'page_number': page_number,
                    'int_ext': int_ext,
                    'location': location,
                    'time_of_day': time_of_day,
                    'content': line + '\n',
                    'characters': [],
                    'dialogue': [],
                    'action': []
                }
                
                scene_number_counter += 1
                in_dialogue = False
                continue
            
            # Character
            if not in_dialogue and self.CHARACTER_PATTERN.match(line) and not line.startswith('!'):
                current_character = line
                in_dialogue = True
                current_dialogue = {
                    'character': current_character,
                    'lines': [],
                    'parentheticals': []
                }
                
                # Add character to scene
                if current_scene and current_character not in current_scene['characters']:
                    current_scene['characters'].append(current_character)
                
                # Add/update character in overall list
                if current_character not in characters:
                    characters[current_character] = {
                        'name': current_character,
                        'dialogue_count': 1,
                        'word_count': 0,
                        'scenes': [current_scene['scene_number']] if current_scene else []
                    }
                else:
                    characters[current_character]['dialogue_count'] += 1
                    if current_scene and current_scene['scene_number'] not in characters[current_character]['scenes']:
                        characters[current_character]['scenes'].append(current_scene['scene_number'])
                
                continue
            
            # Parenthetical
            if in_dialogue and self.PARENTHETICAL_PATTERN.match(line):
                if current_dialogue:
                    current_dialogue['parentheticals'].append(line)
                continue
            
            # Dialogue
            if in_dialogue and current_dialogue is not None:
                current_dialogue['lines'].append(line)
                word_count = len(line.split())
                if current_character in characters:
                    characters[current_character]['word_count'] += word_count
                
                if current_scene:
                    current_scene['content'] += line + '\n'
                continue
            
            # Action lines
            if current_scene:
                current_scene['action'].append(line)
                current_scene['content'] += line + '\n'
            
            # End of dialogue
            in_dialogue = False
            if current_dialogue and current_scene:
                current_scene['dialogue'].append(current_dialogue)
                current_dialogue = None
        
        # Add the last scene if there is one
        if current_scene:
            scenes.append(current_scene)
        
        # Convert characters dictionary to list
        character_list = list(characters.values())
        
        return {
            'scenes': scenes,
            'characters': character_list,
            'metadata': metadata
        }
    
    def _extract_metadata(self, lines: List[str]) -> Dict[str, Any]:
        """
        Extract metadata from the script.
        
        Fountain metadata is in the format:
        Key: Value
        
        Args:
            lines: Script lines
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        in_metadata = True
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Stop when we hit a non-metadata line
            if in_metadata and ':' not in line:
                in_metadata = False
                break
                
            if in_metadata:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    metadata[key] = value
        
        return metadata