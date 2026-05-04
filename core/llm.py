import anthropic
from core.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)