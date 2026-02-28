from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseAIEngine(ABC):
    """
    Abstract Base Class representing the strict contract for any AI engine 
    used to analyze videos in the Moment Finder application.
    """
    
    @abstractmethod
    def find_character_moments(self, video_file_path: str, screenshot_file_path: str, character_name: str) -> List[Dict[str, Any]]:
        """
        Analyzes a video to find moments where a specific character is present.
        
        Args:
            video_file_path (str): The local path to the video file to be analyzed.
            screenshot_file_path (str): The local path to the character reference image.
            character_name (str): The descriptive name of the character (e.g., "Viktor").
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the found moments.
                Must strictly adhere to the following schema:
                [
                    {
                        "start_timestamp": 15.5,    # float, in seconds
                        "end_timestamp": 22.0,      # float, in seconds
                        "action": "walking",        # string description
                        "confidence_score": 0.96    # float between 0 and 1
                    }
                ]
        """
        pass
