"""
routes/upload.py
Handles file/folder uploads from the frontend.
Saves files to UPLOAD_FOLDER with a unique upload_id.
"""

import os
import uuid
import shutil
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


@upload_bp.route('/uploads', methods=['GET'])
def get_all_uploads():
    """Returns a list of all uploaded codebases including size."""
    uploads_list = []
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    def get_size(start_path='.'):
        total = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
        return total
    
    if os.path.exists(upload_folder):
        for entry in os.listdir(upload_folder):
            entry_path = os.path.join(upload_folder, entry)
            if os.path.isdir(entry_path):
                file_count = 0
                proj_name = entry
                
                try:
                    subdirs = os.listdir(entry_path)
                    if len(subdirs) == 1 and os.path.isdir(os.path.join(entry_path, subdirs[0])):
                        proj_name = subdirs[0]
                        for root, _, files in os.walk(os.path.join(entry_path, subdirs[0])):
                            file_count += len(files)
                    else:
                        for root, _, files in os.walk(entry_path):
                            file_count += len(files)
                except Exception:
                    pass

                size_bytes = get_size(entry_path)
                if size_bytes > 1024 * 1024:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{size_bytes / 1024:.1f} KB"

                uploads_list.append({
                    'id': entry,
                    'name': proj_name,
                    'file_count': file_count,
                    'size': size_str
                })
    
    return jsonify({'uploads': uploads_list})


@upload_bp.route('/uploads/<upload_id>', methods=['DELETE'])
def delete_upload(upload_id: str):
    """Deletes an entire uploaded codebase directory."""
    target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_id)
    if os.path.exists(target_dir) and os.path.isdir(target_dir):
        shutil.rmtree(target_dir, ignore_errors=True)
        _uploads.pop(upload_id, None)
        return jsonify({'success': True, 'message': 'Codebase deleted successfully'})
    return jsonify({'error': 'Codebase not found'}), 404



@upload_bp.route('/search', methods=['GET'])
def search_files():
    """Search for files by name or path fragment in UPLOAD_FOLDER."""
    q = (request.args.get('q') or '').strip().lower()
    if not q or len(q) < 2:
        return jsonify({'results': []})
    upload_folder = current_app.config['UPLOAD_FOLDER']
    results = []
    if os.path.exists(upload_folder):
        for root, dirs, files in os.walk(upload_folder):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), upload_folder)
                if q in rel.lower():
                    results.append({'path': rel.replace('\\', '/')})
                    if len(results) >= 30:
                        break
            if len(results) >= 30:
                break
    return jsonify({'results': results})


def get_upload_dir(upload_id: str) -> str | None:
    """Helper used by index route to find upload directory."""
    upload = _uploads.get(upload_id)
    if upload:
        return upload['upload_dir']
        
    # Fallback to checking the filesystem in case server reloaded
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_id)
    if os.path.exists(upload_dir) and os.path.isdir(upload_dir):
        return upload_dir
    return None
