"""
Character analyzer service for analyzing character information, relationships, and arcs.
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import Counter, defaultdict
import spacy
import math
from itertools import combinations

from app.core.config import settings

logger = logging.getLogger("filmpro")


class CharacterAnalyzer:
    """Analyzes characters, their relationships, and dialogue patterns."""
    
    def __init__(self):
        """Initialize the character analyzer."""
        self.nlp = None
        self.is_initialized = False
        
        # Emotion keywords for character analysis
        self.emotion_keywords = {
            "anger": {"angry", "fury", "rage", "furious", "mad", "outraged", "yells", "shouts", "screams", "fight", "argue"},
            "fear": {"afraid", "scared", "terrified", "frightened", "fear", "panic", "horror", "dread", "trembles"},
            "joy": {"happy", "joy", "delighted", "pleased", "smile", "laugh", "excited", "thrilled", "celebrate"},
            "sadness": {"sad", "sorrow", "grief", "miserable", "depressed", "crying", "tears", "weeping", "sob"},
            "surprise": {"surprised", "shocked", "amazed", "astonished", "stunned", "gasps", "unexpected"},
            "disgust": {"disgusted", "revolted", "repulsed", "gross", "sickened", "nauseous"},
            "anticipation": {"waiting", "expecting", "anticipated", "hope", "eager", "looking forward"},
            "trust": {"trust", "belief", "faith", "confident", "rely", "depend", "honest"}
        }
        
        # Gender indicators
        self.male_indicators = {
            "he", "him", "his", "himself", "man", "boy", "father", "son", "brother", "uncle", 
            "nephew", "grandfather", "husband", "boyfriend", "sir", "mr", "male", "gentleman"
        }
        
        self.female_indicators = {
            "she", "her", "hers", "herself", "woman", "girl", "mother", "daughter", "sister", 
            "aunt", "niece", "grandmother", "wife", "girlfriend", "madam", "ms", "mrs", "miss", 
            "female", "lady"
        }
        
        # Age indicators
        self.age_indicators = {
            "child": {"child", "kid", "young", "little", "small", "boy", "girl", "toddler", "baby"},
            "teen": {"teen", "teenage", "adolescent", "youth", "young", "puberty"},
            "young_adult": {"young adult", "twenties", "college", "university", "graduate"},
            "adult": {"adult", "man", "woman", "middle-aged", "thirties", "forties"},
            "senior": {"old", "elderly", "senior", "aged", "retired", "gray-haired", "white-haired", "grandparent"}
        }
        
        # Relationship indicators (keywords that suggest relationships between characters)
        self.relationship_indicators = {
            "family": {"father", "mother", "son", "daughter", "brother", "sister", "uncle", "aunt", 
                     "nephew", "niece", "cousin", "grandfather", "grandmother", "grandparent", 
                     "husband", "wife", "spouse", "family", "parent", "child", "sibling"},
            "romantic": {"boyfriend", "girlfriend", "lover", "fiancé", "fiancée", "engaged", 
                       "married", "dating", "love", "romance", "kiss", "kissing", "affair", 
                       "ex", "ex-husband", "ex-wife", "partner"},
            "professional": {"boss", "employee", "colleague", "coworker", "partner", "assistant",
                          "manager", "worker", "staff", "team", "department", "supervisor", 
                          "subordinate", "client", "customer", "associate", "contractor"},
            "friendship": {"friend", "buddy", "pal", "mate", "acquaintance", "companion", "comrade",
                        "confidant", "bestie", "best friend", "roommate", "neighbor"},
            "antagonistic": {"enemy", "nemesis", "opponent", "rival", "adversary", "foe", "antagonist",
                           "hostile", "hates", "hate", "conflict", "fight", "argue", "arguing"}
        }
    
    async def initialize(self):
        """Load NLP models if not already loaded."""
        if not self.is_initialized:
            logger.info(f"Loading spaCy model for character analysis: {settings.SPACY_MODEL}")
            self.nlp = spacy.load(settings.SPACY_MODEL)
            self.is_initialized = True
            logger.info("NLP models loaded successfully for character analysis")
    
    async def analyze_characters(self, parsed_script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze characters in a script.
        
        Args:
            parsed_script: Dictionary containing parsed script data
            
        Returns:
            Dictionary with character analysis results
        """
        await self.initialize()
        
        # Extract characters and scenes
        characters = parsed_script.get("characters", [])
        scenes = parsed_script.get("scenes", [])
        
        # Process each character
        character_analysis = {}
        character_arcs = {}
        gender_predictions = {}
        age_range_predictions = {}
        
        # Scene appearance map for tracking co-occurrences
        character_scene_map = {}
        
        # Setup data structures
        for character in characters:
            char_name = character["name"]
            character_analysis[char_name] = {
                "name": char_name,
                "dialogue_count": character.get("dialogue_count", 0),
                "word_count": character.get("word_count", 0),
                "scenes": character.get("scenes", []),
                "importance_score": 0.0,
                "emotions": {},
                "dialogue_style": {},
                "relationships": {}
            }
            
            # Add to character scene map
            character_scene_map[char_name] = set(character.get("scenes", []))
            
            # Analyze character dialogue for emotions and style
            if character.get("dialogue_count", 0) > 0:
                await self._analyze_character_dialogue(characters, scenes, char_name, character_analysis)
            
            # Predict gender based on context
            gender_predictions[char_name] = await self._predict_character_gender(character, scenes)
            
            # Predict age range based on context
            age_range_predictions[char_name] = await self._predict_character_age(character, scenes)
            
            # Track character arcs
            character_arcs[char_name] = await self._analyze_character_arc(character, scenes)
        
        # Calculate importance scores based on various factors
        for char_name, analysis in character_analysis.items():
            analysis["importance_score"] = self._calculate_character_importance(
                analysis, len(scenes), len(characters)
            )
        
        # Analyze character relationships
        relationship_matrix = await self._analyze_character_relationships(
            characters, scenes, character_scene_map
        )
        
        # Add relationship data to character analysis
        for char1, relationships in relationship_matrix.items():
            if char1 in character_analysis:
                character_analysis[char1]["relationships"] = relationships
        
        # Add gender and age predictions to character analysis
        for char_name, analysis in character_analysis.items():
            analysis["gender"] = gender_predictions.get(char_name)
            analysis["age_range"] = age_range_predictions.get(char_name)
            analysis["arc"] = character_arcs.get(char_name, {})
        
        return {
            "characters": [analysis for analysis in character_analysis.values()],
            "relationship_matrix": relationship_matrix
        }
    
    async def _analyze_character_dialogue(self, characters: List[Dict[str, Any]], 
                                       scenes: List[Dict[str, Any]], 
                                       character_name: str,
                                       character_analysis: Dict[str, Dict[str, Any]]):
        """
        Analyze a character's dialogue for emotions and speech patterns.
        
        Args:
            characters: List of character dictionaries
            scenes: List of scene dictionaries
            character_name: Name of the character to analyze
            character_analysis: Dictionary to store analysis results
        """
        # Collect all dialogue for this character
        all_dialogue = []
        for scene in scenes:
            for dialogue in scene.get("dialogue", []):
                if dialogue.get("character") == character_name:
                    all_dialogue.extend(dialogue.get("lines", []))
        
        if not all_dialogue:
            return
        
        # Join all dialogue for analysis
        full_dialogue = " ".join(all_dialogue)
        
        # Analyze dialogue for emotions
        emotion_counts = {}
        for emotion, keywords in self.emotion_keywords.items():
            count = 0
            for keyword in keywords:
                count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', full_dialogue.lower()))
            if count > 0:
                emotion_counts[emotion] = count
        
        # Normalize to get emotion scores (0-1 range)
        total_emotions = sum(emotion_counts.values()) if emotion_counts else 1
        emotion_scores = {emotion: count / total_emotions for emotion, count in emotion_counts.items()}
        
        # Analyze dialogue style
        dialogue_style = {
            "avg_sentence_length": self._calculate_avg_sentence_length(full_dialogue),
            "vocabulary_richness": self._calculate_vocabulary_richness(full_dialogue),
            "question_frequency": self._calculate_question_frequency(full_dialogue),
            "exclamation_frequency": self._calculate_exclamation_frequency(full_dialogue)
        }
        
        # Update character analysis
        character_analysis[character_name]["emotions"] = emotion_scores
        character_analysis[character_name]["dialogue_style"] = dialogue_style
    
    async def _analyze_character_relationships(self, 
                                            characters: List[Dict[str, Any]],
                                            scenes: List[Dict[str, Any]],
                                            character_scene_map: Dict[str, Set[str]]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze relationships between characters based on scene co-occurrence and dialogue.
        
        Args:
            characters: List of character dictionaries
            scenes: List of scene dictionaries
            character_scene_map: Mapping of characters to the scenes they appear in
            
        Returns:
            Dictionary of character relationships
        """
        # Initialize relationship matrix
        relationship_matrix = defaultdict(dict)
        
        # Calculate co-occurrence strength
        for char1, char2 in combinations(character_scene_map.keys(), 2):
            # Skip if either character has no scenes
            if not character_scene_map[char1] or not character_scene_map[char2]:
                continue
                
            # Calculate overlap in scenes
            shared_scenes = character_scene_map[char1].intersection(character_scene_map[char2])
            
            if not shared_scenes:
                continue
                
            # Calculate co-occurrence score (Jaccard similarity)
            union_scenes = character_scene_map[char1].union(character_scene_map[char2])
            co_occurrence = len(shared_scenes) / len(union_scenes)
            
            # Calculate dialogue interaction score
            dialogue_interaction = await self._calculate_dialogue_interaction(char1, char2, scenes, shared_scenes)
            
            # Determine relationship type
            relationship_type = await self._detect_relationship_type(char1, char2, scenes, shared_scenes)
            
            # Combined relationship strength (co-occurrence + dialogue interaction)
            relationship_strength = 0.7 * co_occurrence + 0.3 * dialogue_interaction
            
            # Store relationship data
            relationship_matrix[char1][char2] = {
                "strength": round(relationship_strength, 2),
                "co_occurrence": round(co_occurrence, 2),
                "dialogue_interaction": round(dialogue_interaction, 2),
                "shared_scenes": list(shared_scenes),
                "relationship_type": relationship_type
            }
            
            # Mirror the relationship (symmetric)
            relationship_matrix[char2][char1] = {
                "strength": round(relationship_strength, 2),
                "co_occurrence": round(co_occurrence, 2),
                "dialogue_interaction": round(dialogue_interaction, 2),
                "shared_scenes": list(shared_scenes),
                "relationship_type": relationship_type
            }
        
        return dict(relationship_matrix)
    
    async def _calculate_dialogue_interaction(self, char1: str, char2: str, 
                                           scenes: List[Dict[str, Any]], 
                                           shared_scenes: Set[str]) -> float:
        """
        Calculate how much two characters interact through dialogue.
        
        Args:
            char1: First character name
            char2: Second character name
            scenes: List of scene dictionaries
            shared_scenes: Set of scene numbers where both characters appear
            
        Returns:
            Dialogue interaction score (0-1)
        """
        # Count dialogue exchanges between characters
        interaction_count = 0
        max_possible_interactions = 0
        
        for scene in scenes:
            if scene.get("scene_number") not in shared_scenes:
                continue
                
            # Extract dialogue in order
            scene_dialogue = scene.get("dialogue", [])
            if len(scene_dialogue) <= 1:
                continue
                
            # Count consecutive dialogue between char1 and char2
            for i in range(len(scene_dialogue) - 1):
                speaker1 = scene_dialogue[i].get("character")
                speaker2 = scene_dialogue[i + 1].get("character")
                
                if (speaker1 == char1 and speaker2 == char2) or (speaker1 == char2 and speaker2 == char1):
                    interaction_count += 1
            
            # Count total possible interactions in this scene
            char1_speaks = any(d.get("character") == char1 for d in scene_dialogue)
            char2_speaks = any(d.get("character") == char2 for d in scene_dialogue)
            
            if char1_speaks and char2_speaks:
                max_possible_interactions += min(
                    sum(1 for d in scene_dialogue if d.get("character") == char1),
                    sum(1 for d in scene_dialogue if d.get("character") == char2)
                )
        
        # Calculate interaction score
        if max_possible_interactions == 0:
            return 0.0
            
        return interaction_count / max_possible_interactions
    
    async def _detect_relationship_type(self, char1: str, char2: str, 
                                     scenes: List[Dict[str, Any]], 
                                     shared_scenes: Set[str]) -> str:
        """
        Detect the type of relationship between two characters.
        
        Args:
            char1: First character name
            char2: Second character name
            scenes: List of scene dictionaries
            shared_scenes: Set of scene numbers where both characters appear
            
        Returns:
            Relationship type
        """
        # Collect all dialogue and action lines from shared scenes
        scene_texts = []
        
        for scene in scenes:
            if scene.get("scene_number") not in shared_scenes:
                continue
                
            # Get dialogue
            for dialogue in scene.get("dialogue", []):
                scene_texts.extend(dialogue.get("lines", []))
            
            # Get action lines
            scene_texts.extend(scene.get("action", []))
        
        # Join all text for analysis
        full_text = " ".join(scene_texts).lower()
        
        # Check for relationship indicators
        type_scores = {}
        for rel_type, indicators in self.relationship_indicators.items():
            count = 0
            for indicator in indicators:
                # Check for indicator near character names
                char1_pattern = r'\b' + re.escape(char1.lower()) + r'.{0,30}' + re.escape(indicator) + r'\b'
                char2_pattern = r'\b' + re.escape(char2.lower()) + r'.{0,30}' + re.escape(indicator) + r'\b'
                inv_char1_pattern = r'\b' + re.escape(indicator) + r'.{0,30}' + re.escape(char1.lower()) + r'\b'
                inv_char2_pattern = r'\b' + re.escape(indicator) + r'.{0,30}' + re.escape(char2.lower()) + r'\b'
                
                count += len(re.findall(char1_pattern, full_text))
                count += len(re.findall(char2_pattern, full_text))
                count += len(re.findall(inv_char1_pattern, full_text))
                count += len(re.findall(inv_char2_pattern, full_text))
                
                # Also check for direct indicator in text
                count += len(re.findall(r'\b' + re.escape(indicator) + r'\b', full_text)) * 0.2  # Lower weight
            
            if count > 0:
                type_scores[rel_type] = count
        
        # Get relationship type with highest score
        if not type_scores:
            return "associates"  # Default if no clear relationship detected
            
        return max(type_scores.items(), key=lambda x: x[1])[0]
    
    def _calculate_character_importance(self, character_data: Dict[str, Any], 
                                      total_scenes: int, total_characters: int) -> float:
        """
        Calculate a character's importance score based on various metrics.
        
        Args:
            character_data: Character analysis data
            total_scenes: Total number of scenes in the script
            total_characters: Total number of characters in the script
            
        Returns:
            Importance score (0-1)
        """
        # Factors for importance
        factors = {
            "scene_presence": 0.4,  # Percentage of scenes character appears in
            "dialogue_volume": 0.3,  # Relative amount of dialogue
            "relationship_centrality": 0.2,  # How connected to other characters
            "name_prominence": 0.1   # How early the character appears
        }
        
        # Calculate scene presence
        scene_count = len(character_data.get("scenes", []))
        scene_presence = scene_count / total_scenes if total_scenes > 0 else 0
        
        # Calculate dialogue volume (normalized by highest possible)
        word_count = character_data.get("word_count", 0)
        max_possible_words = 5000  # Arbitrary cap for normalization
        dialogue_volume = min(word_count / max_possible_words, 1.0)
        
        # Calculate relationship centrality
        relationship_count = len(character_data.get("relationships", {}))
        relationship_centrality = relationship_count / (total_characters - 1) if total_characters > 1 else 0
        
        # Calculate name prominence (inverse of first appearance)
        scenes = character_data.get("scenes", [])
        if scenes:
            # Convert scene numbers to integers if possible
            try:
                first_scene = min(int(s) if s.isdigit() else float('inf') for s in scenes)
                name_prominence = max(1 - (first_scene / (total_scenes * 2)), 0)  # Earlier is better
            except ValueError:
                name_prominence = 0.5  # Default if scene numbers aren't numeric
        else:
            name_prominence = 0
        
        # Calculate weighted importance score
        importance = (
            scene_presence * factors["scene_presence"] +
            dialogue_volume * factors["dialogue_volume"] +
            relationship_centrality * factors["relationship_centrality"] +
            name_prominence * factors["name_prominence"]
        )
        
        # Ensure it's in 0-1 range and round to 2 decimals
        return round(min(max(importance, 0.0), 1.0), 2)
    
    async def _predict_character_gender(self, character: Dict[str, Any], 
                                     scenes: List[Dict[str, Any]]) -> Optional[str]:
        """
        Predict a character's gender based on dialogue and references.
        
        Args:
            character: Character dictionary
            scenes: List of scene dictionaries
            
        Returns:
            Predicted gender or None if undetermined
        """
        char_name = character["name"]
        
        # Collect all text where this character is mentioned
        references = []
        
        for scene in scenes:
            # Check action lines for mentions
            for action in scene.get("action", []):
                if char_name in action:
                    references.append(action)
            
            # Check dialogue for mentions
            for dialogue in scene.get("dialogue", []):
                if char_name in " ".join(dialogue.get("lines", [])):
                    references.append(" ".join(dialogue.get("lines", [])))
                    
                # Also check parentheticals
                for parenthetical in dialogue.get("parentheticals", []):
                    if char_name in parenthetical:
                        references.append(parenthetical)
        
        if not references:
            return None
            
        # Join all references for analysis
        full_text = " ".join(references).lower()
        
        # Count gender indicators
        male_count = 0
        female_count = 0
        
        for indicator in self.male_indicators:
            # Look for indicators near character name
            pattern = r'\b' + re.escape(char_name.lower()) + r'.{0,30}' + re.escape(indicator) + r'\b'
            inv_pattern = r'\b' + re.escape(indicator) + r'.{0,30}' + re.escape(char_name.lower()) + r'\b'
            
            male_count += len(re.findall(pattern, full_text))
            male_count += len(re.findall(inv_pattern, full_text))
        
        for indicator in self.female_indicators:
            # Look for indicators near character name
            pattern = r'\b' + re.escape(char_name.lower()) + r'.{0,30}' + re.escape(indicator) + r'\b'
            inv_pattern = r'\b' + re.escape(indicator) + r'.{0,30}' + re.escape(char_name.lower()) + r'\b'
            
            female_count += len(re.findall(pattern, full_text))
            female_count += len(re.findall(inv_pattern, full_text))
        
        # Determine gender based on counts
        if male_count > female_count:
            return "male"
        elif female_count > male_count:
            return "female"
        else:
            return None  # Undetermined
    
    async def _predict_character_age(self, character: Dict[str, Any], 
                                  scenes: List[Dict[str, Any]]) -> Optional[str]:
        """
        Predict a character's age range based on dialogue and references.
        
        Args:
            character: Character dictionary
            scenes: List of scene dictionaries
            
        Returns:
            Predicted age range or None if undetermined
        """
        char_name = character["name"]
        
        # Collect all text where this character is mentioned
        references = []
        
        for scene in scenes:
            # Check action lines for mentions
            for action in scene.get("action", []):
                if char_name in action:
                    references.append(action)
            
            # Check dialogue for mentions
            for dialogue in scene.get("dialogue", []):
                if char_name in " ".join(dialogue.get("lines", [])):
                    references.append(" ".join(dialogue.get("lines", [])))
                    
                # Also check parentheticals
                for parenthetical in dialogue.get("parentheticals", []):
                    if char_name in parenthetical:
                        references.append(parenthetical)
        
        if not references:
            return None
            
        # Join all references for analysis
        full_text = " ".join(references).lower()
        
        # Count age indicators
        age_counts = {age: 0 for age in self.age_indicators}
        
        for age, indicators in self.age_indicators.items():
            for indicator in indicators:
                # Look for indicators near character name
                pattern = r'\b' + re.escape(char_name.lower()) + r'.{0,30}' + re.escape(indicator) + r'\b'
                inv_pattern = r'\b' + re.escape(indicator) + r'.{0,30}' + re.escape(char_name.lower()) + r'\b'
                
                age_counts[age] += len(re.findall(pattern, full_text))
                age_counts[age] += len(re.findall(inv_pattern, full_text))
        
        # Determine age based on counts
        if sum(age_counts.values()) == 0:
            return "adult"  # Default to adult if no indicators
            
        # Get age with highest count
        return max(age_counts.items(), key=lambda x: x[1])[0]
    
    async def _analyze_character_arc(self, character: Dict[str, Any], 
                                   scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a character's arc through the script.
        
        Args:
            character: Character dictionary
            scenes: List of scene dictionaries
            
        Returns:
            Dictionary with character arc information
        """
        char_name = character["name"]
        char_scenes = character.get("scenes", [])
        
        if not char_scenes:
            return {"has_arc": False}
        
        try:
            # Convert scene numbers to integers for proper ordering
            # Note: This assumes scene numbers are numeric strings
            scene_ids = [int(s) if s.isdigit() else s for s in char_scenes]
            scene_ids.sort()
        except (ValueError, TypeError):
            # If scene numbers aren't all numeric, use original order
            scene_ids = char_scenes
        
        # Map emotions across scenes
        emotion_progression = []
        
        for scene_id in scene_ids:
            scene_id_str = str(scene_id)
            
            # Find corresponding scene
            scene = next((s for s in scenes if s.get("scene_number") == scene_id_str), None)
            if not scene:
                continue
                
            # Get character's dialogue in this scene
            char_dialogue = []
            for dialogue in scene.get("dialogue", []):
                if dialogue.get("character") == char_name:
                    char_dialogue.extend(dialogue.get("lines", []))
            
            # Skip scenes without dialogue
            if not char_dialogue:
                continue
                
            # Analyze emotions in dialogue
            text = " ".join(char_dialogue)
            emotion_scores = await self._get_emotion_scores(text)
            
            # Add to progression with scene number
            emotion_progression.append({
                "scene": scene_id_str,
                "emotions": emotion_scores
            })
        
        # Identify emotional changes throughout the script
        emotional_changes = self._analyze_emotional_changes(emotion_progression)
        
        # Check for character arc (significant emotional changes)
        has_arc = len(emotional_changes) >= 2  # Need at least two emotional shifts for an arc
        
        return {
            "has_arc": has_arc,
            "emotion_progression": emotion_progression,
            "emotional_changes": emotional_changes,
            "arc_description": self._generate_arc_description(emotional_changes) if has_arc else None
        }
    
    async def _get_emotion_scores(self, text: str) -> Dict[str, float]:
        """
        Get emotion scores for a text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of emotion scores
        """
        text = text.lower()
        emotion_counts = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            count = 0
            for keyword in keywords:
                count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
            if count > 0:
                emotion_counts[emotion] = count
        
        # Normalize to get emotion scores (0-1 range)
        total_emotions = sum(emotion_counts.values()) if emotion_counts else 1
        emotion_scores = {emotion: round(count / total_emotions, 2) for emotion, count in emotion_counts.items()}
        
        # If no emotions detected, return neutral
        if not emotion_scores:
            emotion_scores["neutral"] = 1.0
            
        return emotion_scores
    
    def _analyze_emotional_changes(self, emotion_progression: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze emotional changes throughout a character's scenes.
        
        Args:
            emotion_progression: List of scene emotions
            
        Returns:
            List of significant emotional changes
        """
        if len(emotion_progression) < 2:
            return []
            
        changes = []
        prev_dominant = None
        
        for i, scene_emotions in enumerate(emotion_progression):
            emotions = scene_emotions.get("emotions", {})
            
            if not emotions:
                continue
                
            # Get dominant emotion
            dominant = max(emotions.items(), key=lambda x: x[1])[0] if emotions else "neutral"
            
            # Check if dominant emotion changed
            if prev_dominant is not None and dominant != prev_dominant:
                changes.append({
                    "from_scene": emotion_progression[i-1]["scene"],
                    "to_scene": scene_emotions["scene"],
                    "from_emotion": prev_dominant,
                    "to_emotion": dominant
                })
                
            prev_dominant = dominant
            
        return changes
    
    def _generate_arc_description(self, emotional_changes: List[Dict[str, Any]]) -> str:
        """
        Generate a description of a character's emotional arc.
        
        Args:
            emotional_changes: List of emotional changes
            
        Returns:
            Description of the character's arc
        """
        if not emotional_changes:
            return "No significant emotional journey."
            
        # Get start and end emotions
        start_emotion = emotional_changes[0]["from_emotion"]
        end_emotion = emotional_changes[-1]["to_emotion"]
        
        # Map to general arc types
        positive_emotions = {"joy", "trust", "anticipation"}
        negative_emotions = {"anger", "fear", "sadness", "disgust"}
        
        if start_emotion in positive_emotions and end_emotion in negative_emotions:
            return "Fall from grace: Character begins positively but ends in a negative emotional state."
        elif start_emotion in negative_emotions and end_emotion in positive_emotions:
            return "Redemptive arc: Character begins negatively but ends in a positive emotional state."
        elif start_emotion == end_emotion:
            return "Circular arc: Character returns to their original emotional state after changes."
        else:
            # Count total transitions for complexity
            transition_count = len(emotional_changes)
            if transition_count > 4:
                return "Complex emotional journey with multiple shifts."
            else:
                return f"Character undergoes {transition_count} significant emotional changes."
    
    def _calculate_avg_sentence_length(self, text: str) -> float:
        """Calculate average sentence length in words."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
            
        word_counts = [len(s.split()) for s in sentences]
        return round(sum(word_counts) / len(sentences), 1)
    
    def _calculate_vocabulary_richness(self, text: str) -> float:
        """Calculate vocabulary richness (unique words / total words)."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        if not words:
            return 0.0
            
        unique_words = set(words)
        return round(len(unique_words) / len(words), 2)
    
    def _calculate_question_frequency(self, text: str) -> float:
        """Calculate frequency of questions (sentences ending with ?)."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
            
        question_count = sum(1 for s in sentences if s.endswith('?'))
        return round(question_count / len(sentences), 2)
    
    def _calculate_exclamation_frequency(self, text: str) -> float:
        """Calculate frequency of exclamations (sentences ending with !)."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
            
        exclamation_count = sum(1 for s in sentences if s.endswith('!'))
        return round(exclamation_count / len(sentences), 2)