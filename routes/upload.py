"""
routes/upload.py
Handles file/folder uploads from the frontend.
Saves files to UPLOAD_FOLDER with a unique upload_id.
"""

import os
import uuid
from flask import Blueprint, request, jsonify, current_app

upload_bp = Blueprint('upload', __name__)

# Track upload sessions: { upload_id: { files: [...], status } }
_uploads = {}


@upload_bp.route('/upload', methods=['POST'])
def upload_files():
    """
    Accept multiple files via multipart form upload.
    Returns upload_id to track subsequent indexing.
    """
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'Empty file list'}), 400

    upload_id = str(uuid.uuid4())
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_id)
    os.makedirs(upload_dir, exist_ok=True)

    saved_files = []
    for file in files:
        if not file.filename:
            continue

        # Preserve relative directory structure from filename
        # Frontend should send relative paths as filename
        rel_path = file.filename.replace('\\', '/')
        full_path = os.path.join(upload_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        file.save(full_path)
        saved_files.append(rel_path)

    _uploads[upload_id] = {
        'upload_id': upload_id,
        'upload_dir': upload_dir,
        'file_count': len(saved_files),
        'files': saved_files,
        'status': 'uploaded'
    }

    return jsonify({
        'upload_id': upload_id,
        'file_count': len(saved_files),
        'message': f'Uploaded {len(saved_files)} files successfully'
    })


@upload_bp.route('/upload/<upload_id>', methods=['GET'])
def get_upload_info(upload_id: str):
    """Get info about a specific upload."""
    upload = _uploads.get(upload_id)
    if not upload:
        return jsonify({'error': 'Upload not found'}), 404
    return jsonify(upload)


def get_upload_dir(upload_id: str) -> str | None:
    """Helper used by index route to find upload directory."""
    upload = _uploads.get(upload_id)
    return upload['upload_dir'] if upload else None
