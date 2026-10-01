"""
Configuration for the YouTube Viral Clipper application.

This module loads environment variables and sets up default configurations
for the application. It includes settings for API keys, directories,
and model configurations.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

load_dotenv()

# Load from environment or use defaults
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_API_KEY_HERE')
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', './clips'))
TEMP_DIR = Path(os.getenv('TEMP_DIR', './temp'))
# Whisper model size (options: tiny, base, small, medium, large-v2)
# Using medium model for better performance while maintaining good accuracy
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'medium')
# Language for transcription (e.g., 'en', 'id'). Set to None for auto-detection.
WHISPER_LANGUAGE = os.getenv('WHISPER_LANGUAGE') # Defaults to None (auto-detect)
# YOUTUBE_COOKIES_CONTENT is used by yt-dlp for authentication (optional)
YOUTUBE_COOKIES_CONTENT = os.getenv('YOUTUBE_COOKIES_CONTENT')
YOUTUBE_COOKIES_BROWSER = os.getenv('YOUTUBE_COOKIES_BROWSER')
YOUTUBE_USER_AGENT = os.getenv('YOUTUBE_USER_AGENT')

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
# Default to a free/cheap model, or let user specify
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'arcee-ai/trinity-large-preview:free')

# Create directories
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

if "YOUR_API_KEY_HERE" in GEMINI_API_KEY:
    print("⚠️ WARNING: Please replace 'YOUR_API_KEY_HERE' with your actual Google AI Studio API key in your .env file.")
