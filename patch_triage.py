import shutil, sys

P = 'main.py'
src = open(P, encoding='utf-8').read()

if 'api_triage' in src:
    sys.exit('Already patched (api_triage found). Nothing to do.')

a = src.find("@app.route('/api/chat', methods=['POST'])")
b = src.find("def _analysis_route")
if a == -1 or b == -1 or b < a:
    sys.exit('Could not find the chat block. Send me the output of: grep -n "api/chat\\|_analysis_route" main.py')

shutil.copy(P, 'main.py.bak5')

NEW = r"""import re as _re
try:
    from triage import classify as _triage_classify, rules_analyze as _rules_analyze
    _TRIAGE_OK = True
except Exception as _e:
    print(f'[triage] module not loaded: {_e}')
    _TRIAGE_OK = False

_CHECK_REQ = _re.compile(
    r"\b(is|are) (this|these|it)\b.{0,40}\b(scam|phish\w*|fake|legit\w*|real|genuine|safe|suspicious|fraud\w*)\b"
    r"|\b(check|analy[sz]e|scan|verify)\b.{0,25}\b(this|message|sms|email|text|link|whatsapp)\b",
    _re.I | _re.S)


def _format_triage(t):
    icon = {'High': '\U0001F534', 'Medium': '\U0001F7E0', 'Low': '\U0001F7E2'}.get(t['risk'], '')
    why = t['why'] if isinstance(t['why'], list) else [t['why']]
    lines = [
        f"{icon} {t['risk'].upper()} RISK ({t['score']}/100)",
        f"Verdict: {'Suspicious' if t['suspicious'] else 'Looks safe'}",
        f"Threat type: {t['threat_type']}",
        "",
        "Why:",
    ]
    lines += [f"- {w}" for w in why]
    lines += ["", f"What to do: {t['action']}", "", f"({t['engine']})"]
    return "\n".join(lines)


@app.route('/triage')
def triage_page():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'triage.html'), encoding='utf-8') as f:
        return f.read()


@app.route('/api/triage', methods=['POST'])
def api_triage():
    if not _TRIAGE_OK:
        return jsonify({'error': 'triage module missing'}), 500
    text = (request.get_json(silent=True) or {}).get('text', '')
    return jsonify(_triage_classify(text, llm=llm if model_loaded else None))


@app.route('/api/chat', methods=['POST'])
def chat():
    if not model_loaded:
        return jsonify({'error': 'Model not loaded'}), 500
    try:
        data = request.json or {}
        message = data.get('message', '')
        history = data.get('history', []) or []
        if not message:
            return jsonify({'error': 'No message'}), 400

        # Phishing / scam check: /check <text>, "is this a scam?", or scam-like content
        if _TRIAGE_OK:
            forced = message.strip().lower().startswith('/check')
            text = message.strip()[6:].strip() if forced else message
            if forced and not text:
                return jsonify({'response': 'Paste the message after /check, for example:\n/check Your account is suspended, click here to verify'})
            if forced or _CHECK_REQ.search(message) or _rules_analyze(message)['score'] >= 30:
                t = _triage_classify(text, llm=llm)
                return jsonify({'response': _format_triage(t), 'triage': t})

        msgs = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        msgs += [m for m in history if isinstance(m, dict) and 'role' in m and 'content' in m]
        msgs.append({'role': 'user', 'content': message})
        out = llm.create_chat_completion(messages=msgs, temperature=0.7, max_tokens=512)
        return jsonify({'response': out['choices'][0]['message']['content']})
    except Exception as e:
        print(f'Error in chat endpoint: {e}')
        return jsonify({'error': str(e)}), 500


"""

open(P, 'w', encoding='utf-8').write(src[:a] + NEW + src[b:])
print('Patched. Backup saved as main.py.bak5')
