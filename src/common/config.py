import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    env: str = os.getenv("ENV", "development")

class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# class AnthropicConfig(BaseModel):
#     """Anthropic API configuration."""
#     api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

class NVIDIAConfig(BaseModel):
    """NVIDIA API configuration."""
    api_key: str = os.getenv("NVIDIA_API_KEY", "")

class BraveSearchConfig(BaseModel):
    """Brave Search API configuration."""
    api_key: str = os.getenv("BRAVE_SEARCH_KEY", "")

class GoogleMapsConfig(BaseModel):
    """Google Maps API configuration."""
    api_key: str = os.getenv("GOOGLE_MAPS_KEY", "")
    
class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = os.getenv("LOG_LEVEL", "INFO")

class Config(BaseModel):
    """Application configuration."""
    server: ServerConfig = ServerConfig()
    openai: OpenAIConfig = OpenAIConfig()
    # anthropic: AnthropicConfig = AnthropicConfig()
    nvidia: NVIDIAConfig = NVIDIAConfig()  
    brave_search: BraveSearchConfig = BraveSearchConfig()
    google_maps: GoogleMapsConfig = GoogleMapsConfig()
    logging: LoggingConfig = LoggingConfig()


config = Config()