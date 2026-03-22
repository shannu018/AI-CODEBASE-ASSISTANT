"""
routes/auth.py
Handles authentication.
"""
import os
from flask import Blueprint, request, jsonify, session

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    password = data.get('password')
    correct_password = os.getenv('APP_PASSWORD', 'admin')
    
    if password == correct_password:
        session['logged_in'] = True
        return jsonify({'message': 'Logged in successfully', 'success': True})
    return jsonify({'error': 'Invalid password', 'success': False}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/check_auth', methods=['GET'])
def check_auth():
    if session.get('logged_in'):
        return jsonify({'authenticated': True})
    return jsonify({'authenticated': False}), 401
