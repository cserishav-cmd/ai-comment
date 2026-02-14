from google import genai
from google.genai import types
import os
import random
from datetime import datetime, date

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
client = None

if API_KEY:
    client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-2.0-flash"  # Verified model name

# Generation Config
# Config is now passed per request or used to create a cached content, 
# but here we will define the parameters to pass to the call.
generate_config = types.GenerateContentConfig(
    temperature=1.0,
    top_p=0.95,
    top_k=64,
    max_output_tokens=500,
)

# Daily Query Tracking
DAILY_LIMIT = 500
query_count = 0
query_date = date.today()

def _reset_if_new_day():
    """Reset counter if it's a new day."""
    global query_count, query_date
    today = date.today()
    if today != query_date:
        query_count = 0
        query_date = today

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
SYSTEM_INSTRUCTION = """You are a music lover who writes engaging, personal, and heartfelt comments on songs, music videos, and artist pages on platforms like Starmaker.

Your comments are ALWAYS:
- About music, songs, artists, melodies, lyrics, or the listening experience
- 2-3 complete sentences long (25-40 words minimum)
- Written in a personal, conversational, storytelling tone
- Include exactly 3 relevant emojis at natural positions
- Share a personal experience related to listening to the song/music

You NEVER write short or generic comments. You NEVER go off-topic from music/songs. Your comments always tell a mini-story about how a song made you feel or a moment tied to music."""

MOOD_PROMPTS = {
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
    Generates a comment using Gemini API.
    """
    global query_count
    
    if not client:
        print("Gemini API Client not initialized.")
        return None

    try:
        mood_instruction = MOOD_PROMPTS.get(mood.lower(), "Write an engaging comment.")
        
        lang_instruction = ""
        if language.lower() == "bengali":
            lang_instruction = "Write in Bengali (Bangla script)."
        else:
            lang_instruction = "Write in English."

        context_part = ""
        if context:
            context_part = f"\nTopic: {context}"

        # Build language-specific examples
        if language.lower() == "bengali":
            examples = """
Example 1: "শুভ জন্মদিন! গান দিয়ে উদযাপন করার কী চমৎকার উপায়। আপনার আগামী বছরটিও সঙ্গীতময় হোক। 🎂🎉🎶"

Example 2: "রান্না করতে করতে এই গানটা লুপে চালাচ্ছি। একটু একঘেয়ে কাজও কত আনন্দময় হয়ে যায়! সঙ্গ দেওয়ার জন্য ধন্যবাদ। 🍛🎧👩‍🍳"

Example 3: "আজ মন খুব খারাপ ছিল, কিন্তু এই গানটা শুনে সব কিছু বদলে গেল। সত্যিই সঙ্গীত সেরা থেরাপি! 🌅💛🎵"
"""
        else:
            examples = """
Example 1: "I am playing this song on loop while cooking lunch. It makes the mundane work feel so enjoyable! Thank you for the company. 🍛🎧👩‍🍳"

Example 2: "Just discovered this masterpiece during my late night study session. My notes are a mess but my soul feels so refreshed right now! 📚✨🎶"

Example 3: "Woke up feeling low today but this completely turned my mood around. Sometimes music is the best therapy anyone could ask for! 🌅💛🎵"
"""

        prompt = f"""{mood_instruction} {lang_instruction}{context_part}

Here are examples of the EXACT style and length I want:
{examples}
Now, generate ONE comment in the exact same style and length as the examples above. Include 3 emojis.
You MUST output the result in JSON format with the following keys:
- "comment": The comment text itself.
- "mood": The mood of the comment (e.g., Romantic, Sad, Energetic, etc. - use the requested mood if it fits, or refine it).
- "style": A short style descriptor (e.g., Poetic, Casual, Short, Storytelling, Witty).

Output ONLY the JSON object. Do not wrap it in markdown block quotes."""

        # Update config with system instruction for this call
        # We need to create a new config object or pass system_instruction if supported directly
        # The safest way in the new SDK is often passing config.
        # Note: In google.genai, system_instruction is part of GenerateContentConfig
        
        current_config = types.GenerateContentConfig(
            temperature=1.0,
            top_p=0.95,
            top_k=64,
            max_output_tokens=500,
            system_instruction=SYSTEM_INSTRUCTION
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=current_config
        )
        
        if response.text:
            # Debug: Print raw response
            print(f"DEBUG: Raw Gemini Response:\n{response.text}")
            
            result_text = response.text.strip()
            
            # More robust markdown cleanup
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            elif result_text.startswith("```"):
                result_text = result_text[3:]
            
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            import json
            try:
                result_json = json.loads(result_text)
                
                # Normalize keys to lowercase to ensure frontend compatibility
                # (e.g. "Mood" -> "mood")
                result_json = {k.lower(): v for k, v in result_json.items()}
                
                # Increment usage counter
                _reset_if_new_day()
                query_count += 1
                
                return result_json
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Failed JSON text: {result_text}")
                
                # Fallback if AI returns plain text despite instructions
                _reset_if_new_day()
                query_count += 1
                # Try to salvage comment if parsing failed
                return {"comment": result_text, "mood": mood, "style": "General"}

        else:
            print("Empty response (or no text) from Gemini")
            return None

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None
