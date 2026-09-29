import re, ast, tokenize, io
src = open("main.py").read()
lines = src.split("\n")
start = next(i for i, l in enumerate(lines)
             if l.startswith("index = (lambda") or l.startswith("html_content = "))
end = next(i for i, l in enumerate(lines) if l.startswith("def start_flask"))

rest = lines[start].split("html_content = ", 1)[1]
tok = next(tokenize.generate_tokens(io.StringIO(rest).readline))
html = ast.literal_eval(tok.string)
open("index.html", "w").write(html)
print("html chars:", len(html), "| ends with </html>:", html.rstrip().endswith("</html>"))

ROUTES = '''from flask import send_file, jsonify, request

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

'''
lines[start:end] = ROUTES.split("\n")
src = "\n".join(lines)

PATHS = '''def get_resource_path(relative_path):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def get_base_path():
    return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()'''
src, n1 = re.subn(r"def get_resource_path.*?BASE_PATH = get_base_path\(\)", lambda m: PATHS, src, flags=re.S)

WAIT = '''def wait_for_flask(port, timeout=30):
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
'''
src, n2 = re.subn(r"def wait_for_flask.*?(?=\ndef |\nif __name__)", lambda m: WAIT, src, flags=re.S)
print("paths fixed:", n1, "| wait fixed:", n2)
open("main.py", "w").write(src)
