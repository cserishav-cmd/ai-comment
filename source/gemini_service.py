from google import genai
from google.genai import types
import os
import random
from datetime import datetime, date

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
client = None

if API_KEY:
    print(f"DEBUG: Loaded Gemini API Key starting with: {API_KEY[:5]}...")
    client = genai.Client(api_key=API_KEY)
else:
    print("DEBUG: No Gemini API Key found in environment variables.")

MODEL_NAME = "gemini-2.5-flash-lite"

# Generation Config
generate_config = types.GenerateContentConfig(
    temperature=1.0,
    top_p=0.95,
    top_k=64,
    max_output_tokens=2000, # Increased for batch output
)

import json

# Daily Query Tracking
DAILY_LIMIT = 500
USAGE_FILE = 'usage_data.json'

# Initialize globals
query_count = 0
query_date = date.today()

def _save_usage():
    """Save current usage data to file."""
    try:
        data = {
            "date": query_date.isoformat(),
            "count": query_count
        }
        with open(USAGE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving usage data: {e}")

def _load_usage():
    """Load usage data from file."""
    global query_count, query_date
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, 'r') as f:
                data = json.load(f)
                saved_date = date.fromisoformat(data.get("date", date.today().isoformat()))
                query_count = data.get("count", 0)
                query_date = saved_date
        except Exception as e:
            print(f"Error loading usage data: {e}")

# Load on module import
_load_usage()

# In-Memory Cache for Batch Generation
# Format: {(mood, language, context): [list_of_comments]}
COMMENT_CACHE = {}

def _reset_if_new_day():
    """Reset counter if it's a new day."""
    global query_count, query_date
    today = date.today()
    if today != query_date:
        query_count = 0
        query_date = today
        _save_usage() # Save the reset state

def get_usage_stats():
    """Get current API usage statistics."""
    _reset_if_new_day()
    return {
        "used": query_count,
        "remaining": max(0, DAILY_LIMIT - query_count),
        "total": DAILY_LIMIT,
        "date": query_date.isoformat()
    }

# System instruction to set the AI persona
SYSTEM_INSTRUCTION = """You are a music lover who writes engaging, personal, and heartfelt comments on songs, music videos, and artist pages.

Your task is to generate 5 DIFFERENT, UNIQUE comments based on the user's request.

Each comment must be:
- About music, songs, artists, melodies, lyrics, or the listening experience
- 2-3 complete sentences long (25-40 words minimum)
- Written in a personal, conversational, storytelling tone
- Include exactly 3 relevant emojis
- Share a personal experience related to listening to the song/music

Output Format:
You MUST return a JSON Object with a single key "comments" which is a LIST of 5 objects.
Each object in the list must have:
- "comment": The text
- "mood": The mood
- "style": A short style descriptor

Example JSON Structure:
{
  "comments": [
    {"comment": "...", "mood": "...", "style": "..."},
    {"comment": "...", "mood": "...", "style": "..."},
    ...
  ]
}
"""

MOOD_PROMPTS = {
    # ... (same as before) ...
    "romantic": "Write a romantic comment about how this song makes you feel in love.",
    "sad": "Write an emotional comment about how this song captures your sadness.",
    "energetic": "Write a high-energy comment about how this song pumps you up.",
    "devotional": "Write a spiritual comment about how this song connects you to something divine.",
    "admiring": "Write an admiring comment praising the artist's musical talent and this song.",
    "supportive": "Write a supportive comment encouraging the artist and their music.",
    "nostalgic": "Write a nostalgic comment about memories this song brings back.",
    "funny": "Write a funny, lighthearted comment about your experience with this song.",
    "sarcastic": "Write a sarcastic, witty comment about this song or music.",
    "angry": "Write a passionate comment about how intensely this song hits you.",
    "happy": "Write a joyful comment about how this song brightens your day.",
    "neutral": "Write a thoughtful comment sharing your honest take on this song.",
    "comforting": "Write a warm comment about how this song comforts and heals you.",
    "casual": "Write a casual, friendly comment about vibing to this song.",
    "inspirational": "Write an inspiring comment about how this song motivates you.",
}

def generate_comment_gemini(mood, language, context=None):
    """
    Generates a comment using Gemini API with Batching and Caching.
    """
    global query_count, COMMENT_CACHE
    
    if not client:
        print("Gemini API Client not initialized.")
        return None

    # 1. Check Cache
    cache_key = (mood, language, context)
    if cache_key in COMMENT_CACHE and COMMENT_CACHE[cache_key]:
        print("DEBUG: Serving comment from CACHE.")
        return COMMENT_CACHE[cache_key].pop(0)

    try:
        print("DEBUG: Cache miss. Fetching new batch from Gemini.")
        mood_instruction = MOOD_PROMPTS.get(mood.lower(), "Write an engaging comment.")
        
        lang_instruction = ""
        if language.lower() == "bengali":
            lang_instruction = "Write in Bengali (Bangla script)."
        else:
            lang_instruction = "Write in English."

        context_part = ""
        if context:
            context_part = f"\nTopic: {context}"

        prompt = f"""{mood_instruction} {lang_instruction}{context_part}

Generate 5 distinct comments in the requested style.
Ensure they are varied in tone and wording.
Return ONLY the JSON object with the "comments" list.
"""

        current_config = types.GenerateContentConfig(
            temperature=1.0,
            top_p=0.95,
            top_k=64,
            max_output_tokens=2000,
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json" # Force JSON output
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=current_config
        )
        
        if response.text:
            import json
            try:
                result_json = json.loads(response.text)
                
                comments_list = result_json.get("comments", [])
                
                if not comments_list:
                    print("DEBUG: No comments found in JSON response.")
                    return None

                # Process and normalize comments
                processed_comments = []
                for item in comments_list:
                    # Normalize keys
                    norm_item = {k.lower(): v for k, v in item.items()}
                    processed_comments.append(norm_item)

                # Increment usage (1 API call)
                _reset_if_new_day()
                query_count += 1
                _save_usage() # Persist the new count
                
                # 2. Store in Cache
                # Return first one, cache the rest
                first_comment = processed_comments.pop(0)
                if processed_comments:
                    COMMENT_CACHE[cache_key] = processed_comments
                    print(f"DEBUG: Cached {len(processed_comments)} additional comments for this key.")
                
                return first_comment

            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Failed JSON text: {response.text}")
                return None
        else:
            print("Empty response from Gemini")
            return None

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None
