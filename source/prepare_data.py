import pandas as pd
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# Absolute paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# dataset is at ../dataset/comments.xlsx from source/ dir
INPUT_FILE = os.path.join(SCRIPT_DIR, '../dataset/comments.xlsx')
# output is at ../dataset/ from source/ dir
OUTPUT_DATA_FILE = os.path.join(SCRIPT_DIR, '../dataset/comments.json')
OUTPUT_EMBEDDINGS_FILE = os.path.join(SCRIPT_DIR, '../dataset/embeddings.npy')

def prepare_data():
    print(f"Script Directory: {SCRIPT_DIR}")
    print(f"Input File: {INPUT_FILE}")
    print(f"Output Data: {OUTPUT_DATA_FILE}")

    print("Loading dataset...")
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Dataset not found at {INPUT_FILE}")
        return

    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # Fill NaN values
    df.fillna('', inplace=True)
    
    # Select relevant columns
    data = []
    texts = []
    
    print("Processing rows...")
    for _, row in df.iterrows():
        comment_text = str(row.get('comment', '')).strip()
        if not comment_text:
            continue
            
        item = {
            'id': str(row.get('serial_no', '')),
            'text': comment_text,
            'language': str(row.get('language', '')).lower(),
            'mood': str(row.get('mood', '')).lower(),
            'intensity': str(row.get('intensity', '')),
            'emoji_level': str(row.get('emoji_level', '')),
            'style': str(row.get('style', ''))
        }
        data.append(item)
        texts.append(comment_text) 
        
    print(f"Loaded {len(data)} comments.")
    
    # Save JSON data
    print(f"Saving data to {OUTPUT_DATA_FILE}...")
    try:
        with open(OUTPUT_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return

    # Generate Embeddings
    print("Loading model for embeddings...")
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    print("Generating embeddings...")
    try:
        embeddings = model.encode(texts, show_progress_bar=True)
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return
    
    # Save Embeddings
    print(f"Saving embeddings to {OUTPUT_EMBEDDINGS_FILE}...")
    try:
        np.save(OUTPUT_EMBEDDINGS_FILE, embeddings)
    except Exception as e:
        print(f"Error saving embeddings: {e}")
        return
    
    print("Done!")

if __name__ == "__main__":
    prepare_data()
