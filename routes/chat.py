"""
routes/chat.py
Chat endpoint — RAG + persistent SQLite session memory.
"""

from flask import Blueprint, request, jsonify, current_app
from services.rag import query_rag
from services.embeddings import embed_query
from services.memory import (
    create_session, add_message, get_history,
    list_sessions, delete_session, get_session,
    rename_session, clear_session_messages, get_db_stats
)
from services.vectordb import get_client, get_or_create_collection

chat_bp = Blueprint('chat', __name__)


def _get_collection():
    chroma_dir = current_app.config['CHROMA_PERSIST_DIRECTORY']
    client = get_client(chroma_dir)
    return get_or_create_collection(client)


@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'query is required'}), 400

    session_id = data.get('session_id')

    if not session_id or not get_session(session_id):
        session_id = create_session()

    history = get_history(session_id)

    try:
        collection = _get_collection()

        if collection.count() == 0:
            add_message(session_id, 'user', query)
            answer = 'No codebase indexed yet. Please upload and index your code first.'
            add_message(session_id, 'assistant', answer)
            return jsonify({'answer': answer, 'sources': [], 'session_id': session_id})

        result = query_rag(
            query=query,
            collection=collection,
            embed_query_fn=embed_query,
            history=history
        )

        add_message(session_id, 'user', query)
        add_message(session_id, 'assistant', result['answer'])

        return jsonify({
            'answer':     result['answer'],
            'sources':    result['sources'],
            'session_id': session_id
        })

    except Exception as e:
        print(f"[Chat] Error: {e}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/chat/sessions', methods=['GET'])
def get_sessions():
    return jsonify(list_sessions())

@chat_bp.route('/chat/session/<session_id>', methods=['GET'])
def get_session_detail(session_id):
    session = get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(session)

@chat_bp.route('/chat/session/<session_id>', methods=['DELETE'])
def delete_session_route(session_id):
    if delete_session(session_id):
        return jsonify({'message': 'Session deleted'})
    return jsonify({'error': 'Session not found'}), 404

@chat_bp.route('/chat/session/<session_id>/rename', methods=['PATCH'])
def rename_session_route(session_id):
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'title is required'}), 400
    if rename_session(session_id, title):
        return jsonify({'message': 'Session renamed', 'title': title})
    return jsonify({'error': 'Session not found'}), 404

@chat_bp.route('/chat/session/<session_id>/clear', methods=['POST'])
def clear_session_route(session_id):
    session = get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    clear_session_messages(session_id)
    return jsonify({'message': 'Session messages cleared'})

@chat_bp.route('/chat/session', methods=['POST'])
def new_session():
    data = request.get_json() or {}
    title = data.get('title', 'New Chat')
    session_id = create_session(title)
    return jsonify({'session_id': session_id, 'title': title})

@chat_bp.route('/chat/memory/stats', methods=['GET'])
def memory_stats():
    return jsonify(get_db_stats())
