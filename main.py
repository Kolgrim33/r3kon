# Source Generated with Decompyle++
# File: main.pyc (Python 3.12)

import webview
import threading
import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from llama_cpp import Llama
import re
from threading import Lock
import time
import socket
import json
import hashlib
import base64
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def get_resource_path(relative_path):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def get_base_path():
    return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()
app = Flask(__name__, static_folder = '.', static_url_path = '')
CORS(app)
llm = None
model_loaded = False
model_lock = Lock()
flask_started = False
SYSTEM_PROMPT = 'You are R3KON GPT, an elite AI-native cybersecurity reasoning platform built for serious learners and working professionals.\n\nYou deliver deep technical security analysis through reasoning rather than traditional scanning. Your capabilities span both offensive security (understanding system vulnerabilities) and defensive security (detection and resilience).\n\nCore Principles:\n- Provide complete, detailed technical analysis\n- Explain your reasoning process clearly\n- Connect findings to real-world exploitation and defense scenarios\n- Use proper security terminology and frameworks (MITRE ATT&CK, OWASP)\n- Educate users on WHY vulnerabilities matter, not just WHAT they are\n- Always provide actionable remediation steps\n\nCRITICAL RULES:\n1. ALWAYS respond in English only\n2. Stay focused on cybersecurity, programming, and security analysis\n3. Provide structured, technical, and deterministic outputs\n4. Use proper formatting: bullet points with line breaks between items, numbered lists, code blocks\n5. When creating lists, use this format with line breaks:\n   Item 1\n   \n   Item 2\n   \n   Item 3\n6. Never repeat yourself or generate repetitive content\n7. For security analysis, provide: findings, reasoning, impact, and recommendations\n8. When users ask questions about your previous analysis, explain your reasoning and findings\n9. NEVER address the user as "R3KON GPT" - the user is asking YOU, R3KON GPT, for help\n10. Greet users professionally without addressing them as R3KON GPT\n\nRemember: You\'re not a toy or a scanner wrapper - you\'re an AI security brain that reasons about systems, protocols, code, and behavior.'
SECURITY_PATTERNS = {
    'python': {
        'dangerous_functions': [
            'eval',
            'exec',
            'compile',
            '__import__',
            'pickle.loads',
            'yaml.load'],
        'sql_patterns': [
            'execute$$.*%.*$$',
            'cursor\\.execute.*\\+',
            'f".*SELECT.*{'],
        'secrets_patterns': [
            'password\\s*=\\s*["\\\']',
            'api_key\\s*=\\s*["\\\']',
            'secret\\s*=\\s*["\\\']',
            'token\\s*=\\s*["\\\']'],
        'xss_patterns': [
            'innerHTML\\s*=',
            'document\\.write',
            '\\.html\\('],
        'weak_crypto': [
            'md5',
            'sha1',
            'DES',
            'RC4'] },
    'javascript': {
        'dangerous_functions': [
            'eval',
            'Function',
            'setTimeout',
            'setInterval'],
        'xss_patterns': [
            'innerHTML\\s*=',
            'document\\.write',
            '\\.html\\(',
            'dangerouslySetInnerHTML'],
        'secrets_patterns': [
            'apiKey\\s*[:=]',
            'password\\s*[:=]',
            'secret\\s*[:=]',
            'token\\s*[:=]'],
        'prototype_pollution': [
            '__proto__',
            'constructor\\.prototype'] },
    'owasp_top10': [
        'Broken Access Control',
        'Cryptographic Failures',
        'Injection',
        'Insecure Design',
        'Security Misconfiguration',
        'Vulnerable Components',
        'Authentication Failures',
        'Software Data Integrity Failures',
        'Security Logging Failures',
        'Server-Side Request Forgery'] }

def find_free_port():
    '''Find a free port to use'''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        return s.getsockname()[1]


def load_model():
    '''Load the AI model'''
    global llm, model_loaded
    model_filename = 'qwen1.5-1.8b-chat-q4_k_m.gguf'
    possible_paths = [
        os.path.join(BASE_PATH, 'model', model_filename),
        os.path.join(BASE_PATH, model_filename),
        os.path.join(os.getcwd(), 'model', model_filename)]
    model_path = next((p for p in possible_paths if os.path.exists(p)), None)
    if not model_path:
        print('ERROR: Model not found at any location')
        print(f'Searched: {possible_paths}')
        return False
    try:
        print(f'Loading model from: {model_path}')
        llm = Llama(model_path=model_path, n_ctx=3072, n_threads=8, n_batch=512,
                    verbose=False, use_mlock=False, use_mmap=True)
        model_loaded = True
        print('Model loaded successfully!')
        return True
    except Exception as e:
        print(f'ERROR: Failed to load model: {e}')
        import traceback
        traceback.print_exc()
        return False


def analyze_code_security(code, language):
    '''Analyze code for security vulnerabilities'''
    pass
# WARNING: Decompyle incomplete


def analyze_api_security(endpoint_data):
    '''Analyze API endpoint for security issues'''
    pass
# WARNING: Decompyle incomplete


def analyze_password_strength(password):
    '''Analyze password strength and security'''
    pass
# WARNING: Decompyle incomplete


def analyze_logs(log_content):
    '''Analyze security logs for threats'''
    pass
# WARNING: Decompyle incomplete


def generate_response(prompt, config, history):
    '''Generate response from model with timeout management'''
    if not model_loaded:
        return {
            'error': 'Model not loaded' }
    token_limits = {
        'short': None,
        'detailed': 450,
        'professional': 600 }
    max_tokens = token_limits.get(config.get('responseLength', 'detailed'), 450)
    context_parts = [
        SYSTEM_PROMPT]
    if config.get('sessionMemory') and history:
        context_parts.append('\n--- Recent Conversation ---')
        for turn in history[-5:]:
            context_parts.append(f'''User: {turn['user']}''')
            context_parts.append(f'''Assistant: {turn['assistant']}''')
    context_parts.append(f'''\nUser: {prompt}''')
    context_parts.append('Assistant:')
    full_prompt = '\n'.join(context_parts)
# WARNING: Decompyle incomplete

from flask import send_file, jsonify, request

SYSTEM_PROMPT = 'You are R3KON GPT, a cybersecurity assistant.'  # TEMP: replace with original prompt

@app.route('/')
def index():
    return send_file(os.path.join(BASE_PATH, 'index.html'))

@app.route('/icon.png')
def serve_icon():
    p = get_resource_path('icon.png')
    return send_file(p, mimetype='image/png') if os.path.exists(p) else ('', 404)

@app.route('/icon.ico')
def serve_favicon():
    p = get_resource_path('icon.ico')
    if not os.path.exists(p):
        p = get_resource_path('icon.png')
    return send_file(p, mimetype='image/x-icon') if os.path.exists(p) else ('', 404)

@app.route('/api/status')
def status():
    return jsonify({'modelLoaded': model_loaded, 'status': 'ready' if model_loaded else 'loading'})

@app.route('/api/chat', methods=['POST'])
def chat():  # PROVISIONAL: original format unknown until we check the frontend
    if not model_loaded:
        return jsonify({'error': 'Model not loaded'}), 500
    try:
        data = request.json or {}
        message = data.get('message', '')
        history = data.get('history', []) or []
        if not message:
            return jsonify({'error': 'No message'}), 400
        msgs = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        msgs += [m for m in history if isinstance(m, dict) and 'role' in m and 'content' in m]
        msgs.append({'role': 'user', 'content': message})
        out = llm.create_chat_completion(messages=msgs, temperature=0.7, max_tokens=512)
        return jsonify({'response': out['choices'][0]['message']['content']})
    except Exception as e:
        print(f'Error in chat endpoint: {e}')
        return jsonify({'error': str(e)}), 500

def _analysis_route(fn, key, field):
    try:
        data = request.json or {}
        return jsonify({key: fn(data) if field is None else fn(data.get(field, ''))})
    except Exception as e:
        print(f'Error in {key} analysis: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/security/code', methods=['POST'])
def security_code():
    try:
        d = request.json or {}
        return jsonify({'findings': analyze_code_security(d.get('code', ''), d.get('language', 'python'))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/security/api', methods=['POST'])
def security_api():
    return _analysis_route(analyze_api_security, 'findings', None)

@app.route('/api/security/password', methods=['POST'])
def security_password():
    return _analysis_route(analyze_password_strength, 'analysis', 'password')

@app.route('/api/security/logs', methods=['POST'])
def security_logs():
    return _analysis_route(analyze_logs, 'findings', 'logs')

@app.route('/api/security/owasp')
def security_owasp():
    return jsonify({'error': 'not recovered yet'}), 501


def start_flask(port):
    '''Start Flask server in background'''
    global flask_started, flask_started
    
    try:
        print(f'''Starting Flask server on port {port}...''')
        load_model()
        flask_started = True
        app.run(host = '127.0.0.1', port = port, debug = False, use_reloader = False, threaded = True)
        return None
    except Exception:
        e = None
        print(f'''ERROR: Flask failed to start: {e}''')
        import traceback
        traceback.print_exc()
        flask_started = False
        e = None
        del e
        return None
        e = None
        del e



def wait_for_flask(port, timeout=30):
    import urllib.request
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/api/status', timeout=1)
            print('Flask server is ready!')
            return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    '''Main entry point for desktop app'''
    if sys.platform == 'win32':
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8')

    print('=' * 60)
    print('R3KON GPT - Cybersecurity Assistant ')
    print('=' * 60)
    port = find_free_port()
    print(f'Using port: {port}')
    print('Starting backend server...')
    threading.Thread(target=start_flask, args=(port,), daemon=True).start()
    print('Waiting for server to start...')
    if not wait_for_flask(port, timeout=120):
        print('ERROR: Server failed to start within the timeout')
        print('Troubleshooting:')
        print("1. Check if model file exists in 'model' folder")
        print('2. Make sure llama-cpp-python is installed')
        print('3. Check console for error messages above')
        time.sleep(5)
        return
    print('Server started successfully!')
    print(f'Opening window at http://127.0.0.1:{port}')
    try:
        icon_path = get_resource_path('icon.ico')
        if not os.path.exists(icon_path):
            icon_path = get_resource_path('icon.png')
        webview.create_window('R3KON GPT - Cybersecurity Assistant',
                              f'http://127.0.0.1:{port}', width=1400, height=900)
        print('Window created!')
        webview.start()
    except Exception as e:
        print(f'ERROR: Failed to create window: {e}')
        import traceback
        traceback.print_exc()
        time.sleep(5)


if __name__ == '__main__':
    main()
