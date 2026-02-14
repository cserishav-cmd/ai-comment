from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to sys.path to allow imports from sibling modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from gemini_service import generate_comment_gemini, get_usage_stats
    from fallback_service import get_fallback_comment
    from smart_search import generate_from_prompt
    from browse_service import get_comments_by_filters, get_all_styles
except ImportError:
    # Adjust imports for Vercel environment where source is the root
    from .gemini_service import generate_comment_gemini, get_usage_stats
    from .fallback_service import get_fallback_comment
    from .smart_search import generate_from_prompt
    from .browse_service import get_comments_by_filters, get_all_styles

# Define paths for templates and static files relative to this file
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_comment():
    # Legacy endpoint, keeping for compatibility if needed
    data = request.json
    mood = data.get('mood', 'happy')
    language = data.get('language', 'english')
    context = data.get('context', '')
    response_data = generate_comment_gemini(mood, language, context)
    
    if response_data and isinstance(response_data, dict):
        return jsonify({
            "comment": response_data.get("comment"),
            "mood": response_data.get("mood"),
            "style": response_data.get("style"),
            "source": "AI"
        })
    elif response_data:
         return jsonify({"comment": response_data, "source": "AI", "mood": mood, "style": "General"})
    else:
        return jsonify({"error": "Failed to generate comment"}), 500

@app.route('/api/search', methods=['POST'])
def search_comments():
    """
    Endpoint for Smart Search (Local)
    Accepts: prompt, mood (optional), language (optional)
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    prompt = data.get('prompt', '')
    mood = data.get('mood')
    language = data.get('language')
    
    # Use the local smart search logic with optional filters
    results = generate_from_prompt(prompt, mood=mood, language=language, top_k=5)
    
    return jsonify({
        "results": results,
        "source": "Smart Search (Local)"
    })

@app.route('/api/browse', methods=['POST'])
def browse_comments():
    """
    Endpoint for Browse Mode
    Accepts: language, mood, style (optional), page, page_size, sort
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    language = data.get('language', 'english')
    mood = data.get('mood', 'Romantic')
    style = data.get('style', 'all')
    page = data.get('page', 1)
    page_size = data.get('page_size', 10)
    sort = data.get('sort', 'random')
    
    result = get_comments_by_filters(
        language=language,
        mood=mood,
        style=style,
        page=page,
        page_size=page_size,
        sort=sort
    )
    
    return jsonify(result)

@app.route('/api/styles', methods=['GET'])
def get_styles():
    """
    Endpoint to get all unique styles
    """
    styles = get_all_styles()
    return jsonify({"styles": styles})

@app.route('/api/usage', methods=['GET'])
def api_usage():
    """
    Endpoint to get AI query usage stats
    """
    stats = get_usage_stats()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
