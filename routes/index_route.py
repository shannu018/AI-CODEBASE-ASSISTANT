"""
routes/index_route.py
Indexing pipeline: parse → chunk → embed → store in ChromaDB.
"""

import threading
from flask import Blueprint, request, jsonify, current_app

from routes.upload import get_upload_dir
from services.parser import parse_directory
from services.chunker import chunk_all_files
from services.embeddings import embed_batch
from services.vectordb import get_client, get_or_create_collection, add_chunks, get_collection_stats, clear_collection

index_bp = Blueprint('index', __name__)

# Track indexing jobs: { upload_id: { status, progress, total, error } }
_index_jobs = {}


def _run_indexing(upload_id: str, upload_dir: str, chroma_dir: str):
    """Background thread function that runs the full indexing pipeline."""
    job = _index_jobs[upload_id]

    try:
        # Step 1: Parse
        job['status'] = 'parsing'
        job['message'] = 'Parsing files...'
        parsed_files = parse_directory(upload_dir)
        job['total_files'] = len(parsed_files)

        if not parsed_files:
            job['status'] = 'error'
            job['message'] = 'No supported files found'
            return

        # Step 2: Chunk
        job['status'] = 'chunking'
        job['message'] = 'Chunking code...'
        chunks = chunk_all_files(parsed_files)
        job['total_chunks'] = len(chunks)

        # Step 3: Embed
        job['status'] = 'embedding'
        job['message'] = f'Embedding {len(chunks)} chunks...'
        texts = [c['chunk_text'] for c in chunks]
        embeddings = embed_batch(texts)
        job['progress'] = 50

        # Step 4: Store in ChromaDB
        job['status'] = 'storing'
        job['message'] = 'Storing in vector database...'
        client = get_client(chroma_dir)
        collection = clear_collection(client)  # fresh index each time
        add_chunks(collection, chunks, embeddings)

        job['status'] = 'complete'
        job['progress'] = 100
        job['message'] = f'Indexed {len(parsed_files)} files, {len(chunks)} chunks'

    except Exception as e:
        job['status'] = 'error'
        job['message'] = str(e)
        print(f"[Index] Error: {e}")


@index_bp.route('/index', methods=['POST'])
def start_indexing():
    """Start indexing an uploaded codebase."""
    data = request.get_json() or {}
    upload_id = data.get('upload_id')

    if not upload_id:
        return jsonify({'error': 'upload_id is required'}), 400

    upload_dir = get_upload_dir(upload_id)
    if not upload_dir:
        return jsonify({'error': 'Upload not found'}), 404

    chroma_dir = current_app.config['CHROMA_PERSIST_DIRECTORY']

    # Initialize job tracker
    _index_jobs[upload_id] = {
        'upload_id': upload_id,
        'status': 'starting',
        'progress': 0,
        'message': 'Starting...',
        'total_files': 0,
        'total_chunks': 0
    }

    # Run in background thread so HTTP request returns immediately
    thread = threading.Thread(
        target=_run_indexing,
        args=(upload_id, upload_dir, chroma_dir),
        daemon=True
    )
    thread.start()

    return jsonify({'upload_id': upload_id, 'message': 'Indexing started'})


@index_bp.route('/index/status/<upload_id>', methods=['GET'])
def indexing_status(upload_id: str):
    """Poll indexing progress."""
    job = _index_jobs.get(upload_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)


@index_bp.route('/index/stats', methods=['GET'])
def index_stats():
    """Return stats about the current ChromaDB index."""
    try:
        from flask import current_app
        chroma_dir = current_app.config['CHROMA_PERSIST_DIRECTORY']
        client = get_client(chroma_dir)
        collection = get_or_create_collection(client)
        stats = get_collection_stats(collection)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
