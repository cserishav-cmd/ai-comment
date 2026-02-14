import json
import random
import os
import numpy as np

# Path configurations
# source/fallback_service.py
# dataset/comments.json
DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../dataset/comments.json'))
EMBEDDINGS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../dataset/embeddings.npy'))

# Global cache for data
COMMENTS_DATA = []
EMBEDDINGS_DATA = None
MODEL = None

def load_data():
    global COMMENTS_DATA, EMBEDDINGS_DATA, MODEL
    
    if not COMMENTS_DATA and os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                COMMENTS_DATA = json.load(f)
            print(f"Loaded {len(COMMENTS_DATA)} comments.")
        except Exception as e:
            print(f"Error loading comments data: {e}")
    elif not os.path.exists(DATA_FILE):
        print(f"Data file not found at: {DATA_FILE}")

    if EMBEDDINGS_DATA is None and os.path.exists(EMBEDDINGS_FILE):
        try:
            EMBEDDINGS_DATA = np.load(EMBEDDINGS_FILE)
            print(f"Loaded embeddings shape: {EMBEDDINGS_DATA.shape}")
        except Exception as e:
            print(f"Error loading embeddings: {e}")

    # Try to load SentenceTransformer if possible, but don't crash if it fails (Vercel limits)
    if MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Using a very small model or relying on pre-computed if we can't load a full model
            # For Vercel, this might fail due to size. 
            # We will use a try-except block to gracefully degrade.
            MODEL = SentenceTransformer('all-MiniLM-L6-v2') 
        except ImportError:
            print("sentence-transformers not installed or failed to load. Semantic search disabled.")
        except Exception as e:
            print(f"Error loading SentenceTransformer: {e}")

def get_fallback_comment(mood, language, context=None):
    """
    Retrieves a comment from the local dataset.
    Prioritizes semantic match if context is provided and model is loaded.
    Fallbacks to random selection based on Mood and Language.
    """
    load_data()
    
    # 1. Filter by Language and Mood
    filtered_indices = []
    filtered_comments = []
    
    for idx, comment in enumerate(COMMENTS_DATA):
        if comment['language'].lower() == language.lower() and \
           comment['mood'].lower() == mood.lower():
            filtered_indices.append(idx)
            filtered_comments.append(comment)
            
    if not filtered_comments:
        return "Sorry, I couldn't find a suitable comment for this mood and language."

    # 2. Semantic Search if Context is provided AND Model + Embeddings are available
    if context and MODEL and EMBEDDINGS_DATA is not None and len(filtered_indices) > 0:
        try:
            # Encode the context
            query_embedding = MODEL.encode([context])[0]
            
            # Calculate cosine similarity manually to avoid heavy libraries like scikit-learn/faiss
            # We only search within the filtered indices to be efficient
            
            best_score = -1
            best_comment = None
            
            for idx in filtered_indices:
                if idx < len(EMBEDDINGS_DATA):
                    embedding = EMBEDDINGS_DATA[idx]
                    # Cosine Similarity: (A . B) / (||A|| * ||B||)
                    dot_product = np.dot(query_embedding, embedding)
                    norm_a = np.linalg.norm(query_embedding)
                    norm_b = np.linalg.norm(embedding)
                    
                    if norm_a > 0 and norm_b > 0:
                        score = dot_product / (norm_a * norm_b)
                        if score > best_score:
                            best_score = score
                            best_comment = COMMENTS_DATA[idx]['text']
                            
            if best_comment:
                return best_comment
                
        except Exception as e:
            print(f"Semantic search failed: {e}")
            # Fallback to random
            
    # 3. Random Selection (Default Fallback)
    selected = random.choice(filtered_comments)
    return selected['text']
