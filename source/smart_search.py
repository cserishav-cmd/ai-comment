import pandas as pd
import numpy as np
import random
import faiss
from sentence_transformers import SentenceTransformer
import os

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, '../dataset/comments.json'))
EMBEDDINGS_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, '../dataset/embeddings.npy'))

# Global Data Cache
DF = None
EMBEDDINGS = None
MODEL = None
INDEX = None

# Mood Keywords & Emoji Pools (From file.txt)
MOOD_KEYWORDS = {
    "love": "Romantic",
    "romantic": "Romantic",
    "sad": "Sad",
    "emotional": "Sad",
    "energy": "Energetic",
    "gym": "Energetic",
    "devotional": "Devotional",
    "admire": "Admiring"
}

EMOJI_POOLS = {
    "Romantic": ["❤️", "💖", "🥺", "✨", "🌸", "💞", "😘", "🥰"],
    "Energetic": ["🔥", "⚡", "🎶", "🚀", "💃", "🥳", "🎉", "🌟"],
    "Sad": ["🌙", "💔", "😔", "🌧️", "😢", "😞", "😥", "🍂"],
    "Devotional": ["🙏", "🌺", "🕊️", "✨", "😇", "🌿", "🧘"],
    "Admiring": ["👏", "🔥", "🙏", "✨", "🤩", "💯", "🙌"]
}

def load_resources():
    global DF, EMBEDDINGS, MODEL
    
    if DF is None and os.path.exists(DATA_FILE):
        try:
            print("Loading dataset...")
            DF = pd.read_json(DATA_FILE)
            print(f"Loaded {len(DF)} comments.")
        except Exception as e:
            print(f"Error loading dataset: {e}")

    if EMBEDDINGS is None and os.path.exists(EMBEDDINGS_FILE):
        try:
            print("Loading embeddings...")
            EMBEDDINGS = np.load(EMBEDDINGS_FILE)
            print(f"Loaded embeddings shape: {EMBEDDINGS.shape}")
        except Exception as e:
            print(f"Error loading embeddings: {e}")

    if MODEL is None:
        try:
            print("Loading SentenceTransformer model...")
            MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Error loading model: {e}")

def detect_language(prompt):
    prompt_lower = prompt.lower()
    if any(word in prompt_lower for word in ["bangla", "bengali", "বাংলা", "gan", "gaan"]):
        return "bengali"
    return "english"

def detect_mood(prompt):
    prompt_lower = prompt.lower()
    for key, value in MOOD_KEYWORDS.items():
        if key in prompt_lower:
            return value
    return "Romantic"

def add_emojis(text, mood):
    emojis = EMOJI_POOLS.get(mood, [])
    if not emojis:
        return text
    chosen = random.sample(emojis, min(2, len(emojis)))
    return text + " " + " ".join(chosen)

def generate_from_prompt(user_prompt, mood=None, language=None, top_k=6):
    load_resources()
    
    if DF is None or EMBEDDINGS is None:
        return ["System initializing or data missing. Please try again."]

    # If prompt is empty but filters are provided, set a generic prompt to find *something* relevant
    if not user_prompt:
        user_prompt = "" 
    
    # Logic: If mood/lang are provided (from buttons), use them.
    # Otherwise, detect from prompt.
    
    target_lang = language.lower() if language else detect_language(user_prompt).lower()
    target_mood = mood if mood else detect_mood(user_prompt)
    
    # Start detection log
    print(f"Search Query: '{user_prompt}'")
    print(f"Target Language: {target_lang}")
    print(f"Target Mood: {target_mood}")

    # Normalize DataFrame columns for comparison (if simpler)
    # Assuming dataset has 'language' (lowercased) and 'mood' (mixed)
    
    # Filter DataFrame
    filtered_df = DF[
        (DF["language"].str.lower() == target_lang) &
        (DF["mood"].str.lower() == target_mood.lower())
    ]

    if len(filtered_df) == 0:
        return [f"No matching {target_lang} {target_mood} comments found."]

    subset_indices = filtered_df.index.tolist()
    
    # If no prompt is given, just return random samples from the filtered list?
    # Or strict semantic search against empty string (bad idea)?
    # Let's say if prompt is empty, return random samples.
    # If no prompt is given, just return random samples from the filtered list?
    # Or strict semantic search against empty string (bad idea)?
    # Let's say if prompt is given, return random samples.
    if not user_prompt.strip():
        # Return random samples
        sample_size = min(top_k, len(filtered_df))
        samples = filtered_df.sample(n=sample_size)
        results = []
        for _, row in samples.iterrows():
            varied = add_emojis(row["text"], target_mood)
            results.append({
                "comment": varied,
                "mood": target_mood,
                "style": row.get("style", "Smart Search")
            })
        return results

    # Semantic Search Logic with Randomization
    if MODEL is None:
         return [{"comment": "Model loading failed.", "mood": "Error", "style": "Error"}]

    subset_embeddings = EMBEDDINGS[subset_indices]

    dimension = subset_embeddings.shape[1]
    temp_index = faiss.IndexFlatL2(dimension)
    temp_index.add(subset_embeddings)

    query_vector = MODEL.encode([user_prompt])
    
    # Fetch MORE results than needed (3x), then randomly sample
    # This ensures variety even for the same query
    fetch_k = min(top_k * 3, len(subset_indices))
    distances, indices = temp_index.search(query_vector, fetch_k)

    # Collect all candidates
    candidates = []
    for relative_idx in indices[0]:
        if relative_idx < len(filtered_df):
            row = filtered_df.iloc[relative_idx]
            base_comment = row["text"]
            varied = add_emojis(base_comment, target_mood)
            candidates.append({
                "comment": varied,
                "mood": target_mood,
                "style": row.get("style", "Smart Search") 
            })
    
    # Randomly sample top_k from candidates for variety
    if len(candidates) > top_k:
        results = random.sample(candidates, top_k)
    else:
        results = candidates
            
    return results
