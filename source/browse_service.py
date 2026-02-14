import pandas as pd
import os
import random

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, '../dataset/comments.json'))

# Global Data Cache
DF = None

def load_data():
    global DF
    if DF is None and os.path.exists(DATA_FILE):
        try:
            print("Loading dataset for browse...")
            DF = pd.read_json(DATA_FILE)
            print(f"Loaded {len(DF)} comments.")
        except Exception as e:
            print(f"Error loading dataset: {e}")

def get_comments_by_filters(language, mood, style=None, page=1, page_size=10, sort='random'):
    """
    Fetch comments by language, mood, and optionally style.
    Supports pagination and sorting.
    
    Args:
        language: 'english' or 'bengali'
        mood: Mood filter
        style: Optional style filter (e.g., 'Mentor', 'Friend')
        page: Page number (1-indexed)
        page_size: Number of results per page
        sort: 'alphabetical' or 'random'
    
    Returns:
        {
            'comments': [...],
            'total': total_count,
            'page': current_page,
            'total_pages': total_pages
        }
    """
    load_data()
    
    if DF is None:
        return {
            'comments': [],
            'total': 0,
            'page': page,
            'total_pages': 0,
            'error': 'Dataset not loaded'
        }
    
    # Filter by language and mood
    filtered_df = DF[
        (DF["language"].str.lower() == language.lower()) &
        (DF["mood"].str.lower() == mood.lower())
    ]
    
    # Optionally filter by style
    if style and style.lower() != 'all':
        filtered_df = filtered_df[filtered_df["style"].str.lower() == style.lower()]
    
    total_count = len(filtered_df)
    
    if total_count == 0:
        return {
            'comments': [],
            'total': 0,
            'page': page,
            'total_pages': 0
        }
    
    # Apply sorting
    if sort == 'alphabetical':
        filtered_df = filtered_df.sort_values(by='text')
    elif sort == 'random':
        filtered_df = filtered_df.sample(frac=1, random_state=random.randint(1, 10000))
    
    # Pagination
    total_pages = (total_count + page_size - 1) // page_size
    page = max(1, min(page, total_pages))  # Clamp page number
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_df = filtered_df.iloc[start_idx:end_idx]
    
    paginated_df = filtered_df.iloc[start_idx:end_idx]
    
    # Return list of dictionaries: [{'comment': '...', 'mood': '...', 'style': '...'}, ...]
    # Rename 'text' column to 'comment' for frontend consistency
    comments = paginated_df[['text', 'mood', 'style']].rename(columns={'text': 'comment'}).to_dict('records')
    
    return {
        'comments': comments,
        'total': total_count,
        'page': page,
        'total_pages': total_pages
    }

def get_all_styles():
    """Get all unique styles from the dataset."""
    load_data()
    if DF is not None and 'style' in DF.columns:
        return sorted(DF['style'].unique().tolist())
    return []
