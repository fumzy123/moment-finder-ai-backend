import logging
from app.services.ai.base import BaseAIEngine
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_ai_engine() -> BaseAIEngine:
    """
    Factory function that dynamically loaded the chosen AI engine based on environment variables.
    Currently only supports GEMINI, but acts as the single point of entry for future engines (like VECTOR).
    """
    engine_name = settings.ACTIVE_AI_ENGINE.upper()
    
    if engine_name == "GEMINI":
        from app.services.ai.gemini_engine import GeminiAIEngine
        logger.info("Initializing the Gemini 2.5 Flash-Lite UI Engine...")
        return GeminiAIEngine()
        
    elif engine_name == "VECTOR":
        # Placeholder for future Phase
        # from app.services.ai.vector_engine import VectorAIEngine
        # return VectorAIEngine()
        raise NotImplementedError("Vector DB AI Engine is not yet implemented.")
        
    else:
        logger.error(f"Unknown ACTIVE_AI_ENGINE configured in .env: {engine_name}")
        raise ValueError(f"Unsupported AI Engine: {engine_name}")
