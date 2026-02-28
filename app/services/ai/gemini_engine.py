import os
import json
import logging
import time
from typing import List, Dict, Any
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.services.ai.base import BaseAIEngine
from app.core.config import settings

logger = logging.getLogger(__name__)

# Pydantic models to force Gemini to return exactly this JSON structure
class CharacterMomentSchema(BaseModel):
    action: str = Field(description="A short description of what the character is doing in this scene.")
    start_timestamp: float = Field(description="The timestamp in seconds when the character first appears in this scene.")
    end_timestamp: float = Field(description="The timestamp in seconds when the character leaves or the scene ends.")
    confidence_score: float = Field(description="A score between 0.0 and 1.0 indicating how confident you are this is the correct character.")

class VideoAnalysisResultSchema(BaseModel):
    moments: list[CharacterMomentSchema]

class GeminiAIEngine(BaseAIEngine):
    """
    Concrete implementation of the AI Engine using Google's Gemini 2.5 Flash-Lite.
    Uses the modern google-genai SDK.
    """
    
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
            
        # Initialize the new SDK client
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        # Load the dynamic model name from environment variables (e.g. gemini-1.5-pro or gemini-2.5-flash-lite)
        self.model_name = settings.GEMINI_MODEL_NAME
        
    def find_character_moments(self, video_file_path: str, screenshot_file_path: str, character_name: str) -> List[Dict[str, Any]]:
        """
        Uploads physical files to the Gemini File API, prompts the model, and parses the structured response.
        """
        logger.info(f"Uploading files to Gemini File API for {character_name}...")
        video_file = None
        img_file = None
        
        try:
            # 1. Upload the files to Google's temporary storage server
            video_file = self.client.files.upload(file=video_file_path)
            img_file = self.client.files.upload(file=screenshot_file_path)
            
            # Wait for video to process in Google's system before prompting
            logger.info(f"Waiting for video {video_file.name} to process on Gemini servers...")
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = self.client.files.get(name=video_file.name)
                
            if video_file.state.name == "FAILED":
                raise Exception("Gemini failed to process the uploaded video file.")
                
            logger.info("Files ready. Prompting Gemini...")
            
            # 2. Formulate the highly specific prompt
            prompt = (
                f"You are an expert video analysis AI. \n"
                f"1. Look at the attached image. This character's name is '{character_name}'.\n"
                f"2. Watch the attached video carefully.\n"
                f"3. Find every distinct scene or moment where '{character_name}' is clearly visible.\n"
                f"4. Return a list of those moments, including the start and end timestamps (in seconds), "
                f"a brief description of what they are doing, and your confidence score."
            )
            
            # 3. Call the model using Structured Outputs to guarantee we get back JSON matching our DB schema
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[img_file, video_file, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VideoAnalysisResultSchema,
                    temperature=0.2 # Keep it analytical, not creative
                )
            )
            
            # 4. Parse the guaranteed JSON text back into a Python dictionary list
            raw_json = response.text
            data = json.loads(raw_json)
            
            logger.info(f"Gemini Analysis Successful. Found {len(data.get('moments', []))} moments.")
            return data.get("moments", [])
            
        except Exception as e:
            logger.error(f"Error during Gemini Analysis: {e}")
            raise e
            
        finally:
            # 5. Cleanup: ALWAYS delete the files from Google's servers to save space and maintain privacy
            logger.info("Cleaning up temporary Gemini files...")
            try:
                if video_file:
                    self.client.files.delete(name=video_file.name)
                if img_file:
                    self.client.files.delete(name=img_file.name)
            except Exception as cleanup_error:
                logger.error(f"Failed to delete files from Gemini: {cleanup_error}")
