"""
Scene analyzer service for calculating scene complexity, estimating durations, and analyzing scene content.
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
import math
import spacy
from collections import Counter

from app.core.config import settings

logger = logging.getLogger("filmpro")


class SceneAnalyzer:
    """Analyzes scenes for complexity, duration estimates, and other metrics."""
    
    def __init__(self):
        """Initialize the scene analyzer."""
        self.nlp = None
        self.is_initialized = False
        
        # Complexity factors
        self.complexity_factors = {
            "character_count": 0.2,       # More characters = more complex
            "dialogue_density": 0.15,     # More dialogue = more complex
            "action_density": 0.15,       # More action description = more complex
            "special_elements": 0.2,      # Special effects, stunts, etc.
            "location_complexity": 0.15,  # INT vs EXT, unusual locations
            "time_complexity": 0.15,      # Night, magic hour, etc.
        }
        
        # Special elements that increase complexity
        self.complexity_keywords = {
            "fight", "explosion", "chase", "stunt", "effect", "vfx", "sfx", "rain", "storm",
            "underwater", "crash", "fire", "burn", "blood", "crowd", "animals", "children",
            "vehicle", "car chase", "gunshot", "shoot", "shot", "bullet", "weapon",
            "difficult", "complex", "dangerous", "challenging", "airborne", "aerial",
            "snow", "ice", "mountain", "climb", "falling", "fall", "jump"
        }
        
        # Time of day complexity factors (night shoots are more complex)
        self.time_complexity = {
            "day": 0.5,
            "morning": 0.6,
            "afternoon": 0.5,
            "evening": 0.7,
            "night": 1.0,
            "dawn": 0.9,
            "dusk": 0.9,
            "magic hour": 1.0,
            "sunrise": 0.9,
            "sunset": 0.9,
        }
        
        # Location complexity factors
        self.location_type_complexity = {
            "int": 0.6,    # Interior is generally simpler
            "ext": 0.8,    # Exterior adds weather and lighting variables
            "int/ext": 0.9  # Both interior and exterior adds complexity
        }
        
        # Location keywords that suggest complex locations
        self.complex_location_keywords = {
            "moving", "car", "vehicle", "boat", "ship", "airplane", "plane", "helicopter",
            "train", "subway", "water", "ocean", "sea", "lake", "river", "mountain",
            "forest", "jungle", "desert", "snow", "beach", "cliff", "rooftop", "stairs",
            "restaurant", "bar", "crowd", "public", "stadium", "theater", "concert"
        }
    
    async def initialize(self):
        """Load NLP models if not already loaded."""
        if not self.is_initialized:
            logger.info(f"Loading spaCy model for scene analysis: {settings.SPACY_MODEL}")
            self.nlp = spacy.load(settings.SPACY_MODEL)
            self.is_initialized = True
            logger.info("NLP models loaded successfully for scene analysis")
    
    async def analyze_scene(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a scene for complexity, duration estimate, and other metrics.
        
        Args:
            scene_data: Dictionary containing scene information from the parser
            
        Returns:
            Dictionary with analysis results
        """
        await self.initialize()
        
        # Extract scene properties
        scene_number = scene_data.get("scene_number", "")
        slug_line = scene_data.get("slug_line", "")
        content = scene_data.get("content", "")
        characters = scene_data.get("characters", [])
        action_lines = scene_data.get("action", [])
        dialogue = scene_data.get("dialogue", [])
        int_ext = scene_data.get("int_ext", "")
        location = scene_data.get("location", "")
        time_of_day = scene_data.get("time_of_day", "")
        
        # Calculate basic metrics
        character_count = len(characters)
        dialogue_line_count = sum(len(d.get("lines", [])) for d in dialogue)
        action_line_count = len(action_lines)
        total_line_count = dialogue_line_count + action_line_count
        
        # Calculate dialogue and action density
        dialogue_density = dialogue_line_count / total_line_count if total_line_count > 0 else 0
        action_density = action_line_count / total_line_count if total_line_count > 0 else 0
        
        # Check for complexity keywords in content
        complexity_keyword_matches = self._count_keyword_matches(content, self.complexity_keywords)
        has_complex_elements = complexity_keyword_matches > 0
        
        # Calculate location complexity
        location_complexity = self._calculate_location_complexity(int_ext, location)
        
        # Calculate time complexity
        time_complexity = self._calculate_time_complexity(time_of_day)
        
        # Overall complexity score calculation (0-1 scale)
        complexity_score = self._calculate_complexity_score(
            character_count=character_count,
            dialogue_density=dialogue_density,
            action_density=action_density,
            special_elements=complexity_keyword_matches,
            location_complexity=location_complexity,
            time_complexity=time_complexity
        )
        
        # Estimate scene duration
        duration_estimate = self._estimate_duration(
            character_count=character_count,
            dialogue_line_count=dialogue_line_count,
            action_line_count=action_line_count,
            complexity_score=complexity_score
        )
        
        # Perform sentiment analysis on the scene
        emotions, overall_sentiment = await self._analyze_sentiment(content)
        
        # Identify key actions in the scene
        key_actions = self._extract_key_actions(action_lines)
        
        return {
            "scene_number": scene_number,
            "complexity_score": complexity_score,
            "duration_estimate": duration_estimate,  # In minutes
            "metrics": {
                "character_count": character_count,
                "dialogue_line_count": dialogue_line_count,
                "action_line_count": action_line_count,
                "total_line_count": total_line_count,
                "dialogue_density": dialogue_density,
                "action_density": action_density,
                "complexity_keyword_matches": complexity_keyword_matches,
                "has_complex_elements": has_complex_elements,
                "location_complexity": location_complexity,
                "time_complexity": time_complexity
            },
            "emotions": emotions,
            "overall_sentiment": overall_sentiment,
            "key_actions": key_actions
        }
    
    def _count_keyword_matches(self, text: str, keywords: set) -> int:
        """Count the number of matches for complexity keywords in text."""
        text = text.lower()
        count = 0
        for keyword in keywords:
            count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
        return min(count, 10)  # Cap at 10 to prevent outliers
    
    def _calculate_location_complexity(self, int_ext: str, location: str) -> float:
        """Calculate the complexity factor for a location."""
        # Base complexity from INT/EXT
        base_complexity = 0.5  # Default
        if int_ext and int_ext.lower() in self.location_type_complexity:
            base_complexity = self.location_type_complexity[int_ext.lower()]
        
        # Check for complex location keywords
        location_complexity_factor = 0.0
        if location:
            location = location.lower()
            keyword_count = self._count_keyword_matches(location, self.complex_location_keywords)
            location_complexity_factor = min(keyword_count * 0.1, 0.5)  # Up to 0.5 additional complexity
        
        return min(base_complexity + location_complexity_factor, 1.0)
    
    def _calculate_time_complexity(self, time_of_day: str) -> float:
        """Calculate the complexity factor for time of day."""
        if not time_of_day:
            return 0.5  # Default complexity
        
        time_of_day = time_of_day.lower()
        
        for time_key, complexity in self.time_complexity.items():
            if time_key in time_of_day:
                return complexity
        
        return 0.5  # Default if no match
    
    def _calculate_complexity_score(self, **factors) -> float:
        """
        Calculate overall scene complexity score (0-1 scale).
        
        Args:
            character_count: Number of characters in scene
            dialogue_density: Proportion of dialogue lines to total lines
            action_density: Proportion of action lines to total lines
            special_elements: Count of special elements (stunts, effects, etc.)
            location_complexity: Complexity score for the location (0-1)
            time_complexity: Complexity score for the time of day (0-1)
            
        Returns:
            Complexity score (0-1 scale)
        """
        # Normalize character count (0-10+ scale to 0-1)
        character_factor = min(factors.get("character_count", 0) / 10.0, 1.0)
        
        # Special elements (0-10 scale to 0-1)
        special_factor = min(factors.get("special_elements", 0) / 10.0, 1.0)
        
        # Get other factors directly (already 0-1)
        dialogue_factor = factors.get("dialogue_density", 0.5)
        action_factor = factors.get("action_density", 0.5)
        location_factor = factors.get("location_complexity", 0.5)
        time_factor = factors.get("time_complexity", 0.5)
        
        # Weighted sum
        complexity = (
            character_factor * self.complexity_factors["character_count"] +
            dialogue_factor * self.complexity_factors["dialogue_density"] +
            action_factor * self.complexity_factors["action_density"] +
            special_factor * self.complexity_factors["special_elements"] +
            location_factor * self.complexity_factors["location_complexity"] +
            time_factor * self.complexity_factors["time_complexity"]
        )
        
        # Ensure it's in 0-1 range and round to 2 decimals
        return round(min(max(complexity, 0.0), 1.0), 2)
    
    def _estimate_duration(self, character_count: int, dialogue_line_count: int, 
                         action_line_count: int, complexity_score: float) -> float:
        """
        Estimate scene duration in minutes.
        
        Args:
            character_count: Number of characters in scene
            dialogue_line_count: Number of dialogue lines
            action_line_count: Number of action lines
            complexity_score: Overall complexity score (0-1)
            
        Returns:
            Estimated duration in minutes
        """
        # Base duration estimates
        # - Dialogue: ~3 seconds per line average
        # - Action: Variable, but ~5 seconds per line on average for simple actions
        
        dialogue_time = dialogue_line_count * 3 / 60  # Convert to minutes
        
        # Action time depends on complexity
        action_time = action_line_count * (5 + 5 * complexity_score) / 60  # More time for complex actions
        
        # Setup time depends on character count and complexity
        setup_time = (0.5 + 0.2 * character_count) * (1 + complexity_score)
        
        # Sum and add buffer for complex scenes
        duration = dialogue_time + action_time + setup_time
        
        # Add complexity multiplier (more complex = more time for takes, setups, etc.)
        duration = duration * (1 + 0.5 * complexity_score)
        
        # Round to nearest 0.1 minute
        return round(duration, 1)
    
    async def _analyze_sentiment(self, content: str) -> Tuple[Dict[str, float], str]:
        """
        Analyze the emotional content of a scene.
        
        Args:
            content: Scene content text
            
        Returns:
            Tuple of (emotion_scores, overall_sentiment)
        """
        if not content:
            return {}, "neutral"
        
        # Basic emotion keywords (could be expanded or replaced with a more sophisticated model)
        emotion_keywords = {
            "anger": {"angry", "fury", "rage", "furious", "mad", "outraged", "yells", "shouts", "screams", "fight", "argue"},
            "fear": {"afraid", "scared", "terrified", "frightened", "fear", "panic", "horror", "dread", "trembles"},
            "joy": {"happy", "joy", "delighted", "pleased", "smile", "laugh", "excited", "thrilled", "celebrate"},
            "sadness": {"sad", "sorrow", "grief", "miserable", "depressed", "crying", "tears", "weeping", "sob"},
            "surprise": {"surprised", "shocked", "amazed", "astonished", "stunned", "gasps", "unexpected"},
            "disgust": {"disgusted", "revolted", "repulsed", "gross", "sickened", "nauseous"},
            "anticipation": {"waiting", "expecting", "anticipated", "hope", "eager", "looking forward"},
            "trust": {"trust", "belief", "faith", "confident", "rely", "depend", "honest"}
        }
        
        # Analyze text using spaCy
        doc = self.nlp(content)
        
        # Count emotion keywords
        emotion_counts = {emotion: 0 for emotion in emotion_keywords}
        for token in doc:
            for emotion, keywords in emotion_keywords.items():
                if token.lemma_.lower() in keywords:
                    emotion_counts[emotion] += 1
        
        # Normalize counts to get scores (0-1 range)
        max_count = max(emotion_counts.values()) if emotion_counts.values() else 1
        emotion_scores = {emotion: count / max_count if max_count > 0 else 0 
                          for emotion, count in emotion_counts.items() if count > 0}
        
        # Determine overall sentiment
        if not emotion_scores:
            return {}, "neutral"
        
        # Get dominant emotion
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
        
        # Map to basic sentiment categories
        sentiment_mapping = {
            "anger": "negative",
            "fear": "negative",
            "joy": "positive",
            "sadness": "negative",
            "surprise": "neutral",
            "disgust": "negative",
            "anticipation": "neutral",
            "trust": "positive"
        }
        
        return emotion_scores, sentiment_mapping.get(dominant_emotion, "neutral")
    
    def _extract_key_actions(self, action_lines: List[str]) -> List[str]:
        """
        Extract key action descriptions from action lines.
        
        Args:
            action_lines: List of action description lines
            
        Returns:
            List of key action descriptions
        """
        if not action_lines:
            return []
        
        # Join all action lines
        all_action = " ".join(action_lines)
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', all_action)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Find sentences with strong action verbs
        action_verbs = {
            "run", "jump", "fight", "grab", "throw", "hit", "shoot", "chase", "escape",
            "climb", "fall", "crash", "explode", "break", "smash", "slam", "rush", "race",
            "attack", "defend", "push", "pull", "lift", "drop", "enter", "exit", "kiss",
            "embrace", "punch", "kick", "dive", "swim", "drive", "ride", "fly", "land"
        }
        
        key_actions = []
        for sentence in sentences:
            words = sentence.lower().split()
            if any(verb in words for verb in action_verbs):
                # Clean up the sentence
                clean_sentence = sentence.strip()
                if clean_sentence and len(clean_sentence) > 10:  # Avoid very short fragments
                    key_actions.append(clean_sentence)
        
        # Limit to top 5 key actions
        return key_actions[:5]