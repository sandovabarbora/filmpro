"""
Service for extracting elements from script content using NLP.
"""
import spacy
import logging
from typing import List, Dict, Any, Set, Tuple
import re
from collections import Counter

from app.core.config import settings
from app.models.script import ElementType

logger = logging.getLogger("filmpro")


class ElementExtractor:
    """Extract elements from script content using NLP."""
    
    def __init__(self):
        """Initialize the element extractor with NLP models."""
        self.nlp = None
        self.is_initialized = False
        self.prop_patterns = [
            r"\b(?:holding|carries|carrying|using|with|puts? down|picks? up|hands|handed|giving|gave|takes?|taking|took|pulls? out|bringing|brings?|brought|wears?|wearing|wore|dressed in|dressed with)\s+(?:a|an|the|his|her|their)?\s*([A-Z][a-z]+(?:\s+[a-z]+){0,3})",
            r"\b(?:a|an|the)\s+([A-Z][a-z]+(?:\s+[a-z]+){0,3})\s+(?:sits|rests|lies|lying|placed|is placed|on|beside|next to|above|below|under|behind|in front of)",
        ]
        self.vehicle_keywords = {"car", "truck", "bus", "motorcycle", "bike", "bicycle", "SUV", "van", "taxi", "boat", "ship", "plane", "helicopter", "jet", "train"}
        self.prop_stop_words = {"man", "woman", "boy", "girl", "person", "friend", "mother", "father", "child", "children", "people", "group", "crowd", "audience", "everyone", "anybody", "somebody", "man's", "woman's", "guy", "guys"}
    
    async def initialize(self):
        """Load NLP models if not already loaded."""
        if not self.is_initialized:
            logger.info(f"Loading spaCy model: {settings.SPACY_MODEL}")
            self.nlp = spacy.load(settings.SPACY_MODEL)
            self.is_initialized = True
            logger.info("NLP models loaded successfully")
    
    async def extract_elements(self, parsed_script: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract elements from parsed script.
        
        Args:
            parsed_script: Dictionary of parsed script data
            
        Returns:
            Dictionary of extracted elements by type
        """
        await self.initialize()
        
        results = {
            ElementType.CHARACTER: [],
            ElementType.LOCATION: [],
            ElementType.PROP: [],
            ElementType.VEHICLE: [],
            ElementType.WARDROBE: [],
            ElementType.SPECIAL_EFFECT: [],
        }
        
        # Characters are already parsed in the fountain parser
        for character in parsed_script.get('characters', []):
            results[ElementType.CHARACTER].append({
                'name': character['name'],
                'occurrences': [int(scene_num) if scene_num.isdigit() else scene_num 
                               for scene_num in character.get('scenes', [])],
                'importance': len(character.get('scenes', [])) / len(parsed_script.get('scenes', [])) 
                              if parsed_script.get('scenes') else 0
            })
        
        # Extract locations from scene headings
        locations = {}
        for scene in parsed_script.get('scenes', []):
            location = scene.get('location')
            if location:
                scene_num = scene.get('scene_number', '')
                if location not in locations:
                    locations[location] = {'name': location, 'occurrences': [scene_num]}
                else:
                    if scene_num not in locations[location]['occurrences']:
                        locations[location]['occurrences'].append(scene_num)
        
        for location in locations.values():
            location['importance'] = len(location['occurrences']) / len(parsed_script.get('scenes', [])) if parsed_script.get('scenes') else 0
            results[ElementType.LOCATION].append(location)
        
        # Extract props, vehicles, and other elements from action lines
        all_action_text = ""
        scene_action_map = {}
        
        for scene in parsed_script.get('scenes', []):
            scene_num = scene.get('scene_number', '')
            scene_action = '\n'.join(scene.get('action', []))
            if scene_action:
                all_action_text += scene_action + "\n"
                scene_action_map[scene_action] = scene_num
        
        # Extract props using regex patterns
        props = await self._extract_props_from_text(all_action_text, scene_action_map)
        results[ElementType.PROP].extend(props)
        
        # Extract vehicles
        vehicles = await self._extract_vehicles_from_text(all_action_text, scene_action_map)
        results[ElementType.VEHICLE].extend(vehicles)
        
        # Extract wardrobe items
        wardrobe = await self._extract_wardrobe_from_text(all_action_text, scene_action_map)
        results[ElementType.WARDROBE].extend(wardrobe)
        
        # Extract special effects
        special_effects = await self._extract_special_effects_from_text(all_action_text, scene_action_map)
        results[ElementType.SPECIAL_EFFECT].extend(special_effects)
        
        # Deduplicate elements
        for element_type, elements in results.items():
            results[element_type] = self._deduplicate_elements(elements)
        
        return results
    
    async def _extract_props_from_text(self, text: str, scene_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract props from text using regex patterns and NLP.
        
        Args:
            text: Text to extract props from
            scene_map: Mapping of text sections to scene numbers
            
        Returns:
            List of extracted props
        """
        props = []
        doc = self.nlp(text)
        
        # Use regex patterns to find props
        for pattern in self.prop_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                prop_name = match.group(1).strip()
                if prop_name.lower() not in self.prop_stop_words:
                    # Find which scene this belongs to
                    scene_nums = self._find_scenes_for_span(match.span(), text, scene_map)
                    
                    props.append({
                        'name': prop_name,
                        'occurrences': scene_nums,
                        'context': text[max(0, match.start() - 20):min(len(text), match.end() + 20)].strip()
                    })
        
        # Use NLP to find objects
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "WORK_OF_ART", "ORG"]:
                if ent.text.lower() not in self.prop_stop_words:
                    scene_nums = self._find_scenes_for_span(ent.start_char, text, scene_map)
                    
                    props.append({
                        'name': ent.text,
                        'occurrences': scene_nums,
                        'context': text[max(0, ent.start_char - 20):min(len(text), ent.end_char + 20)].strip()
                    })
        
        return props
    
    async def _extract_vehicles_from_text(self, text: str, scene_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract vehicles from text.
        
        Args:
            text: Text to extract vehicles from
            scene_map: Mapping of text sections to scene numbers
            
        Returns:
            List of extracted vehicles
        """
        vehicles = []
        doc = self.nlp(text)
        
        # Look for vehicle keywords
        for vehicle_word in self.vehicle_keywords:
            for match in re.finditer(rf"\b{vehicle_word}\b", text, re.IGNORECASE):
                scene_nums = self._find_scenes_for_span(match.span(), text, scene_map)
                
                # Get context around the match
                start_idx = max(0, match.start() - 50)
                end_idx = min(len(text), match.end() + 50)
                context = text[start_idx:end_idx].strip()
                
                # Try to get a more specific vehicle description
                vehicle_name = self._get_vehicle_description(match.start(), doc)
                if not vehicle_name:
                    vehicle_name = match.group(0)
                
                vehicles.append({
                    'name': vehicle_name,
                    'occurrences': scene_nums,
                    'context': context
                })
        
        return vehicles
    
    def _get_vehicle_description(self, char_pos: int, doc: Any) -> str:
        """Get a more detailed vehicle description from surrounding text."""
        # Find the token at this character position
        token = None
        for t in doc:
            if t.idx <= char_pos < t.idx + len(t.text):
                token = t
                break
        
        if not token:
            return ""
        
        # Look for adjectives or compound modifiers
        modifiers = []
        for left_token in token.lefts:
            if left_token.dep_ in ["amod", "compound", "nummod"] or left_token.pos_ == "ADJ":
                modifiers.append(left_token.text)
        
        if modifiers:
            return " ".join(modifiers) + " " + token.text
        return token.text
    
    async def _extract_wardrobe_from_text(self, text: str, scene_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract wardrobe items from text.
        
        Args:
            text: Text to extract wardrobe from
            scene_map: Mapping of text sections to scene numbers
            
        Returns:
            List of extracted wardrobe items
        """
        wardrobe_items = []
        
        # Wardrobe-related patterns
        wardrobe_patterns = [
            r"(?:wearing|wears|dressed in|dressed with|puts on|wearing a|wearing an|in a|in an)\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,3}?)\s+(?:jacket|shirt|dress|suit|pants|skirt|hat|coat|sweater|blouse|shoes|boots|uniform|costume|outfit)",
            r"(?:wearing|wears|dressed in|dressed with|puts on)\s+(?:a|an|the|his|her|their)?\s*([A-Za-z]+(?:\s+[A-Za-z]+){0,3}?)\s+(?:jacket|shirt|dress|suit|pants|skirt|hat|coat|sweater|blouse|shoes|boots|uniform|costume|outfit)",
            r"(?:a|an|the|his|her|their)?\s*([A-Za-z]+(?:\s+[A-Za-z]+){0,3}?)\s+(?:jacket|shirt|dress|suit|pants|skirt|hat|coat|sweater|blouse|shoes|boots|uniform|costume|outfit)"
        ]
        
        for pattern in wardrobe_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                item_desc = match.group(0).strip()
                scene_nums = self._find_scenes_for_span(match.span(), text, scene_map)
                
                wardrobe_items.append({
                    'name': item_desc,
                    'occurrences': scene_nums,
                    'context': text[max(0, match.start() - 20):min(len(text), match.end() + 20)].strip()
                })
        
        return wardrobe_items
    
    async def _extract_special_effects_from_text(self, text: str, scene_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract special effects from text.
        
        Args:
            text: Text to extract special effects from
            scene_map: Mapping of text sections to scene numbers
            
        Returns:
            List of extracted special effects
        """
        special_effects = []
        
        # Special effects keywords
        effect_keywords = [
            "explosion", "explodes", "exploding", "fire", "smoke", "rain", "storm", "lightning",
            "thunder", "earthquake", "crash", "crashes", "shatter", "shatters", "shattering",
            "blood", "bleeding", "gunshot", "shoots", "shooting", "fight", "fighting", "stunt",
            "falls", "falling", "jumps", "jumping", "vfx", "cgi", "effect", "practical effect",
            "slow motion", "timelapse", "makeup effect", "prosthetic", "animatronic", "pyrotechnic"
        ]
        
        for keyword in effect_keywords:
            for match in re.finditer(rf"\b{keyword}\b", text, re.IGNORECASE):
                scene_nums = self._find_scenes_for_span(match.span(), text, scene_map)
                
                special_effects.append({
                    'name': f"{keyword.title()} Effect",
                    'occurrences': scene_nums,
                    'context': text[max(0, match.start() - 30):min(len(text), match.end() + 30)].strip()
                })
        
        return special_effects
    
    def _find_scenes_for_span(self, span, text: str, scene_map: Dict[str, str]) -> List[str]:
        """
        Find which scenes a text span belongs to.
        
        Args:
            span: Character span (start, end) or single position
            text: Full text
            scene_map: Mapping of text sections to scene numbers
            
        Returns:
            List of scene numbers
        """
        if isinstance(span, tuple):
            start_pos, end_pos = span
        else:
            start_pos = end_pos = span
            
        matching_scenes = []
        
        for section_text, scene_num in scene_map.items():
            section_start = text.find(section_text)
            if section_start == -1:
                continue
                
            section_end = section_start + len(section_text)
            
            # If span overlaps with this section
            if not (end_pos < section_start or start_pos > section_end):
                matching_scenes.append(scene_num)
        
        return matching_scenes if matching_scenes else ["unknown"]
    
    def _deduplicate_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate elements by name and merge occurrences.
        
        Args:
            elements: List of element dictionaries
            
        Returns:
            Deduplicated element list
        """
        element_map = {}
        
        for element in elements:
            name = element['name'].lower()
            if name in element_map:
                # Merge occurrences
                for occurrence in element['occurrences']:
                    if occurrence not in element_map[name]['occurrences']:
                        element_map[name]['occurrences'].append(occurrence)
                
                # Update context if this one is better
                if len(element.get('context', '')) > len(element_map[name].get('context', '')):
                    element_map[name]['context'] = element.get('context')
            else:
                element_map[name] = element.copy()
        
        # Update importance based on number of occurrences
        for name, element in element_map.items():
            if 'importance' not in element:
                element['importance'] = len(element['occurrences']) / 10  # Arbitrary scaling
        
        return list(element_map.values())