"""
routes/analyze.py
Code analysis endpoints: explain, impact analysis, test generation, security scan, diff, docs.
"""

from flask import Blueprint, request, jsonify
from services.rag import analyze_code, security_scan, explain_diff

analyze_bp = Blueprint('analyze', __name__)


@analyze_bp.route('/analyze/explain', methods=['POST'])
def explain_code():
    """Explain a code snippet."""
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    if not code:
        return jsonify({'error': 'code field is required'}), 400
    try:
        explanation = analyze_code(code, 'explain')
        return jsonify({'explanation': explanation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analyze_bp.route('/analyze/impact', methods=['POST'])
def impact_analysis():
    """Analyze potential impact of changing a code snippet."""
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    if not code:
        return jsonify({'error': 'code field is required'}), 400
    try:
        analysis = analyze_code(code, 'impact')
        return jsonify({'analysis': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analyze_bp.route('/analyze/tests', methods=['POST'])
def generate_tests():
    """Generate unit tests for a code snippet."""
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    if not code:
        return jsonify({'error': 'code field is required'}), 400
    try:
        tests = analyze_code(code, 'tests')
        return jsonify({'tests': tests})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analyze_bp.route('/analyze/docs', methods=['POST'])
def generate_docs():
    """Generate docstrings for code."""
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    if not code:
        return jsonify({'error': 'code field is required'}), 400
    try:
        result = analyze_code(code, 'docs')
        return jsonify({'docs': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analyze_bp.route('/analyze/diff', methods=['POST'])
def diff_explainer():
    """Explain a git diff."""
    data = request.get_json() or {}
    diff = data.get('diff', '').strip()
    if not diff:
        return jsonify({'error': 'diff field is required'}), 400
    try:
        explanation = explain_diff(diff)
        return jsonify({'explanation': explanation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analyze_bp.route('/analyze/security', methods=['POST'])
def security_analysis():
    """Scan code for security vulnerabilities."""
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    if not code:
        return jsonify({'error': 'code field is required'}), 400
    try:
        report = security_scan(code)
        return jsonify({'security_report': report})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
