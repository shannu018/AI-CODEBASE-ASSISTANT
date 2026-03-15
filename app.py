"""
AI Codebase Assistant - Main Flask Application
RAG-powered assistant for large-scale codebase comprehension using Google Gemini
"""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_SIZE_MB', 2048)) * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', './uploads')
app.config['CHROMA_PERSIST_DIRECTORY'] = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_db')

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CHROMA_PERSIST_DIRECTORY'], exist_ok=True)

# Import and register blueprints
from routes.upload     import upload_bp
from routes.index_route import index_bp
from routes.chat        import chat_bp
from routes.analyze     import analyze_bp

app.register_blueprint(upload_bp,    url_prefix='/api')
app.register_blueprint(index_bp,     url_prefix='/api')
app.register_blueprint(chat_bp,      url_prefix='/api')
app.register_blueprint(analyze_bp,   url_prefix='/api')

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'AI Codebase Assistant'}

if __name__ == '__main__':
    print(">> Starting AI Codebase Assistant...")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"ChromaDB path: {app.config['CHROMA_PERSIST_DIRECTORY']}")
    print("Server running at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
