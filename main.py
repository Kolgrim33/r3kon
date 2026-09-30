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
    model_filename = os.environ.get('R3KON_MODEL', 'qwen1.5-1.8b-chat-q4_k_m.gguf')
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
        llm = Llama(model_path=model_path, n_ctx=3072, n_threads=4, n_batch=512,
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
    max_tokens = token_limits.get(config.get('responseLength', 'detailed'), 450) or 200
    context_parts = [
        SYSTEM_PROMPT]
    if config.get('sessionMemory') and history:
        context_parts.append('\n--- Recent Conversation ---')
        for turn in history[-5:]:
            context_parts.append(f'''User: {turn['user']}''')
            context_parts.append(f'''Assistant: {turn['assistant']}''')
    context_parts.append(f'''\nUser: {prompt}''')
    context_parts.append('Assistant:')
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    if config.get('sessionMemory') and history:
        for turn in history[-5:]:
            if turn.get('user'):
                messages.append({'role': 'user', 'content': turn['user']})
            if turn.get('assistant'):
                messages.append({'role': 'assistant', 'content': turn['assistant']})
    messages.append({'role': 'user', 'content': prompt})
    try:
        with model_lock:
            out = llm.create_chat_completion(messages=messages, max_tokens=max_tokens,
                                             temperature=0.7, top_p=0.9, repeat_penalty=1.1)
        return {'response': out['choices'][0]['message']['content'].strip()}
    except Exception as e:
        print(f'Error generating response: {e}')
        return {'error': str(e)}

from flask import send_file, jsonify, request


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

# =========================================================================== #
# Phishing / scam triage (offline): rules + local LLM -> risk score, type, why, action
# =========================================================================== #
# --------------------------------------------------------------------------- #
# Rules
# --------------------------------------------------------------------------- #
# (id, regex, weight 0-100, threat type, plain-language reason)
TRI_RULES = [
    ("credential_request",
     r"\b(send|share|give|enter|confirm|verify|provide|reply with)\b.{0,40}"
     r"\b(pin|otp|password|passcode|one[- ]time|cvv|card number|secret code)\b",
     45, "Phishing",
     "It asks for a PIN, OTP or password. Real banks and mobile-money services never ask for these."),
    ("reversal_scam",
     r"(sent|transferred|deposited)\b.{0,40}(by mistake|in error|wrongly|wrong number)"
     r"|reverse (the|this) (transaction|payment)|(return|send back) (the|my) (money|cash|funds)",
     55, "Financial scam",
     "It says money was sent by mistake and asks you to send it back, a common mobile-money trick."),
    ("prize",
     r"(you have|you've|you are|congratulations).{0,30}(won|selected|winner|lucky)"
     r"|\blottery\b|\bjackpot\b|claim (your )?(prize|reward|gift)",
     50, "Financial scam",
     "It claims you won a prize you never entered for."),
    ("advance_fee",
     r"(processing|registration|clearance|release|admin|delivery|activation|insurance) fee"
     r"|pay .{0,25}to (receive|release|claim|unlock|withdraw)",
     40, "Financial scam",
     "It asks you to pay a fee before you can receive something."),
    ("account_threat",
     r"(account|sim|line|card|wallet)\b.{0,30}(suspended|blocked|locked|deactivated|closed|"
     r"compromised|frozen|will be (closed|deleted|terminated))",
     30, "Phishing",
     "It threatens to block or close your account to scare you into acting."),
    ("verify_click",
     r"(click|tap|open|follow|visit)\b.{0,25}(link|here|below|url)"
     r"|verify (your )?(account|identity|details)|update your (details|account|kyc|information)",
     25, "Phishing",
     "It pushes you to click a link or 'verify' your details."),
    ("urgency",
     r"\b(urgent(ly)?|immediately|within \d+ ?(hours?|hrs|minutes?|mins)|expires? (today|soon|in)|"
     r"last chance|act now|final (notice|warning))\b",
     15, None,
     "It uses urgency and pressure so you don't stop to think."),
    ("family_emergency",
     r"(this is (your )?(son|daughter|mother|mum|dad|brother|sister|boss|manager|director|ceo)|"
     r"new number|lost my phone).{0,90}(send|transfer|need|urgent|airtime|money)",
     60, "Identity fraud",
     "Someone claims to be a relative or boss on a 'new number' and asks for money."),
    ("ai_media",
     r"(sounded (exactly )?like|voice (of|sounds like|was)|cloned voice|voice clon|deepfake|"
     r"ai[- ]generated (voice|video|image|photo))",
     30, "AI-enabled threat",
     "It involves a voice, video or image that may have been faked with AI."),
    ("investment",
     r"(double|triple|guaranteed).{0,20}(money|returns?|profit|investment)"
     r"|\d+ ?% (daily|weekly|monthly) (returns?|profit|interest)",
     35, "Financial scam",
     "It promises guaranteed or unrealistic returns."),
    ("job_scam",
     r"(job|vacanc|employment|recruit).{0,60}(fee|pay|deposit)"
     r"|earn \$?\d+.{0,20}(per|a) (day|week).{0,20}(home|online)",
     35, "Financial scam",
     "It offers a job or easy income but asks you to pay first."),
    ("remote_access",
     r"\b(anydesk|teamviewer|remote access)\b|install (this |the )?app|download (the )?(apk|app)",
     30, "Malicious link",
     "It asks you to install software or give someone remote access."),
    ("risky_attachment",
     r"\.(apk|exe|scr|bat|vbs|js)\b",
     30, "Malicious link",
     "It mentions a file type that can carry malware."),
    ("secrecy",
     r"(do not|don't|dont) (tell|share|inform)\b.{0,25}(anyone|family|bank)"
     r"|keep (this|it) (secret|confidential)",
     25, "Identity fraud",
     "It tells you to keep this secret, which scammers do to stop you checking."),
]
_TRI_COMPILED = [(i, re.compile(p, re.I | re.S), w, t, r) for i, p, w, t, r in TRI_RULES]

# --------------------------------------------------------------------------- #
# URL checks
# --------------------------------------------------------------------------- #
TRI_URL_RE = re.compile(
    r"(?i)\b((?:https?://|www\.)[^\s<>\"']+"
    r"|[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|co\.zw|zw|xyz|top|click|link|info|ru|tk|ml|ga|cf|gq|"
    r"site|online|vip|cc|shop|club)(?:/[^\s<>\"']*)?)")

TRI_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly",
              "rb.gy", "shorturl.at", "tiny.cc"}
TRI_RISKY_TLDS = (".xyz", ".top", ".click", ".link", ".tk", ".ml", ".ga", ".cf", ".gq",
              ".ru", ".vip", ".cc", ".site", ".online", ".club", ".shop")
TRI_BRANDS = ["ecocash", "econet", "netone", "onemoney", "telecash", "zesa", "zimra", "cbz",
          "stanbic", "fbc", "steward", "innbucks", "paynow", "nedbank", "absa", "rbz", "telone"]
TRI_OFFICIAL = ("ecocash.co.zw", "econet.co.zw", "netone.co.zw", "telone.co.zw", "zesa.co.zw",
            "zimra.co.zw", "rbz.co.zw", "cbz.co.zw", "stanbicbank.co.zw", "fbc.co.zw",
            "nedbank.co.zw", "steward.co.zw", "innbucks.co.zw", "paynow.co.zw", "absa.co.zw")


def _tri_host(url):
    u = url if "://" in url else "http://" + url
    try:
        return (urlparse(u).hostname or "").lower()
    except ValueError:
        return ""


def tri_url_signals(text):
    """Return (list of (weight, threat_type, reason), list of urls found)."""
    sigs, urls = [], []
    for m in TRI_URL_RE.finditer(text):
        raw = m.group(1).rstrip(".,;:!?)")
        urls.append(raw)
        host = _tri_host(raw)
        if not host:
            continue
        official = any(host == d or host.endswith("." + d) for d in TRI_OFFICIAL)
        if official:
            continue
        sigs.append((8, "Malicious link", f"It contains a link ({host}) you didn't ask for."))
        if host in TRI_SHORTENERS:
            sigs.append((25, "Malicious link", f"{host} is a link shortener that hides the real destination."))
        if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
            sigs.append((35, "Malicious link", "The link points to a raw IP address instead of a real website name."))
        if host.endswith(TRI_RISKY_TLDS):
            sigs.append((25, "Malicious link", f"The link ends in a domain type ({host.rsplit('.', 1)[-1]}) often used for scams."))
        if any(b in host for b in TRI_BRANDS):
            sigs.append((45, "Phishing", f"The link ({host}) imitates a known Zimbabwean brand but is not its real website."))
        if host.count("-") >= 2:
            sigs.append((10, "Malicious link", "The web address is stuffed with hyphens, a typical fake-site pattern."))
        if "@" in raw:
            sigs.append((20, "Malicious link", "The link contains an '@', a trick to disguise the real site."))
        if raw.lower().startswith("http://"):
            sigs.append((8, "Malicious link", "The link is not encrypted (http, not https)."))
    return sigs, urls


def tri_rules_analyze(text):
    """Noisy-OR of all signals -> 0-100 score, dominant threat type, reasons."""
    signals = []
    for rid, rx, w, t, reason in _TRI_COMPILED:
        if rx.search(text):
            signals.append((w, t, reason))
    usigs, urls = tri_url_signals(text)
    signals += usigs

    # de-duplicate identical reasons
    seen, uniq = set(), []
    for s in signals:
        if s[2] not in seen:
            seen.add(s[2])
            uniq.append(s)
    signals = sorted(uniq, key=lambda s: -s[0])

    p = 1.0
    for w, _, _ in signals:
        p *= 1 - w / 100.0
    score = min(98, round(100 * (1 - p)))

    by_type = {}
    for w, t, _ in signals:
        if t:
            by_type[t] = by_type.get(t, 0) + w
    threat = max(by_type, key=by_type.get) if by_type else "Benign"
    return {"score": score, "threat": threat,
            "reasons": [s[2] for s in signals], "urls": urls}


# --------------------------------------------------------------------------- #
# LLM layer
# --------------------------------------------------------------------------- #
TRI_THREATS = ["Phishing", "Financial scam", "Identity fraud", "Malicious link",
           "AI-enabled threat", "Benign"]

TRI_SCHEMA = {
    "type": "object",
    "properties": {
        "suspicious": {"type": "boolean"},
        "threat_type": {"type": "string", "enum": TRI_THREATS},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "why": {"type": "string"},
    },
    "required": ["suspicious", "threat_type", "score", "why"],
}

TRI_SYSTEM = (
    "You are a cybersecurity assistant that protects ordinary people in Zimbabwe from scams. "
    "Judge the message. Typical local threats: fake EcoCash/OneMoney/bank messages, 'sent by mistake' "
    "reversal scams, fake prizes, advance-fee and job scams, SIM/account suspension links, "
    "relative-on-a-new-number requests, cloned voices. "
    "Normal messages (family chat, lecturer notices, real receipts, genuine reminders) are Benign with a low score. "
    "score: 0 = certainly safe, 100 = certainly malicious. "
    "why: ONE short sentence in plain English a non-technical person understands. "
    "Reply with JSON only."
)


def tri_llm_analyze(llm, text, hints):
    if llm is None:
        return None
    hint_txt = ("\nSignals already detected: " + "; ".join(hints[:4])) if hints else ""
    msgs = [
        {"role": "system", "content": TRI_SYSTEM},
        {"role": "user", "content": f"Message to check:\n\"\"\"\n{text[:1500]}\n\"\"\"{hint_txt}"},
    ]
    try:
        out = llm.create_chat_completion(
            messages=msgs, temperature=0.0, max_tokens=160,
            response_format={"type": "json_object", "schema": TRI_SCHEMA})
        raw = out["choices"][0]["message"]["content"]
        data = json.loads(raw)
        data["score"] = max(0, min(100, int(data.get("score", 0))))
        if data.get("threat_type") not in TRI_THREATS:
            data["threat_type"] = "Benign" if data["score"] < 30 else "Phishing"
        return data
    except Exception as e:  # any failure -> rules-only fallback
        print(f"[triage] LLM layer skipped: {e}")
        return None


# --------------------------------------------------------------------------- #
# Actions
# --------------------------------------------------------------------------- #
TRI_ACTIONS = {
    "Phishing": {
        "High": "Do NOT click any link or share your PIN, OTP or password. Delete the message, block the sender, and if you already replied, contact the real company on its official number and change your PIN.",
        "Medium": "Don't click anything yet. Call the organisation on its official number (not one from the message) to confirm.",
    },
    "Financial scam": {
        "High": "Do NOT send money or pay any fee. Block the sender and tell your mobile-money provider or bank. If you already paid, report it to them immediately, and to the police.",
        "Medium": "Don't send money. Confirm the claim with the provider through its official channel first.",
    },
    "Identity fraud": {
        "High": "Do NOT send money or personal details. Call the person on the number you already have to confirm it's really them. If details were shared, tell your bank or provider and change your PINs.",
        "Medium": "Verify who this is by calling their known number before doing anything they ask.",
    },
    "Malicious link": {
        "High": "Do NOT open the link or download any file. If you already did, disconnect from the internet, run a security scan and change important passwords from a clean device.",
        "Medium": "Avoid the link. If you must check it, type the organisation's official website yourself.",
    },
    "AI-enabled threat": {
        "High": "Do NOT act on a voice, video or image alone. Verify by calling back on a known number or asking something only the real person would know. Report it to your IT/security contact.",
        "Medium": "Confirm through a second channel before sending money or sharing information.",
    },
}
TRI_DEFAULT_LOW = "No action needed. Stay careful with links and never share your PIN or OTP."
TRI_DEFAULT_MED = "Verify the sender through an official channel before acting on this."


def tri_pick_action(threat, risk):
    if risk == "Low":
        return TRI_DEFAULT_LOW
    return TRI_ACTIONS.get(threat, {}).get(risk) or TRI_ACTIONS.get(threat, {}).get("High") or TRI_DEFAULT_MED


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def tri_risk_from_score(score):
    if score >= 60:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def tri_classify(text, llm=None):
    text = (text or "").strip()
    if not text:
        return {"error": "Empty message"}

    r = tri_rules_analyze(text)
    l = tri_llm_analyze(llm, text, r["reasons"])

    if l is not None:
        score = round(0.5 * r["score"] + 0.5 * l["score"])
        if r["score"] >= 60:                 # strong rule evidence is never diluted
            score = max(score, r["score"])
        engine = "Rules + local AI (offline)"
    else:
        score = r["score"]
        engine = "Rules only (offline)"

    risk = tri_risk_from_score(score)
    suspicious = score >= 30

    if r["reasons"] and r["threat"] != "Benign":
        threat = r["threat"]
    elif l is not None and l["threat_type"] != "Benign" and suspicious:
        threat = l["threat_type"]
    else:
        threat = "Benign" if not suspicious else "Phishing"
    if not suspicious:
        threat = "Benign"

    reasons = list(r["reasons"][:4])
    if l is not None and l.get("why"):
        if suspicious and l.get("suspicious") and l["why"] not in reasons:
            reasons.append(l["why"])
        elif not suspicious and not reasons:
            reasons = [l["why"]]
    if not reasons:
        reasons = ["No scam warning signs were found in this message."]

    return {
        "suspicious": suspicious,
        "threat_type": threat,
        "risk": risk,
        "score": score,
        "why": reasons[:4],
        "action": tri_pick_action(threat, risk),
        "engine": engine,
        "rule_score": r["score"],
        "ai_score": l["score"] if l else None,
        "links_found": r["urls"],
    }


_TRI_CHECK_REQ = re.compile(
    r"\b(is|are) (this|these|it)\b.{0,40}\b(scam|phish\w*|fake|legit\w*|real|genuine|safe|suspicious|fraud\w*)\b"
    r"|\b(check|analy[sz]e|scan|verify)\b.{0,25}\b(this|message|sms|email|text|link|whatsapp)\b",
    re.I | re.S)


def tri_format(t):
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


def _norm_history(history):
    """Accept [{'user':..,'assistant':..}] or [{'role':..,'content':..}] and return the first form."""
    turns, pending = [], None
    for m in history or []:
        if not isinstance(m, dict):
            continue
        if 'user' in m or 'assistant' in m:
            turns.append({'user': m.get('user', ''), 'assistant': m.get('assistant', '')})
        elif m.get('role') == 'user':
            pending = m.get('content', '')
        elif m.get('role') == 'assistant' and pending is not None:
            turns.append({'user': pending, 'assistant': m.get('content', '')})
            pending = None
    return turns


@app.route('/api/triage', methods=['POST'])
def api_triage():
    text = (request.get_json(silent=True) or {}).get('text', '')
    with model_lock:
        return jsonify(tri_classify(text, llm=llm if model_loaded else None))


@app.route('/api/chat', methods=['POST'])
def chat():
    if not model_loaded:
        return jsonify({'error': 'Model not loaded'}), 500
    try:
        data = request.get_json(silent=True) or {}
        message = data.get('message') or data.get('prompt') or data.get('text') or ''
        config = data.get('config') or {}
        history = _norm_history(data.get('history'))
        if not message.strip():
            return jsonify({'error': 'No message'}), 400

        # Phishing / scam check: "/check <text>", "is this a scam?", or scam-like content
        forced = message.strip().lower().startswith('/check')
        text = message.strip()[6:].strip() if forced else message
        if forced and not text:
            return jsonify({'response': 'Paste the message after /check, for example:\n/check Your account is suspended, click here to verify'})
        if not message.startswith('[SCAN REPORT]') and (forced or _TRI_CHECK_REQ.search(message) or tri_rules_analyze(message)['score'] >= 30):
            with model_lock:
                t = tri_classify(text, llm=llm)
            return jsonify({'response': tri_format(t), 'triage': t})

        result = generate_response(message, config, history)
        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        print(f'Error in chat endpoint: {e}')
        return jsonify({'error': str(e)}), 500


from flask import Response, stream_with_context


def _ndjson(obj):
    return json.dumps(obj) + '\n'


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    if not model_loaded:
        return jsonify({'error': 'Model not loaded'}), 500
    data = request.get_json(silent=True) or {}
    message = data.get('message') or data.get('prompt') or data.get('text') or ''
    config = data.get('config') or {}
    history = _norm_history(data.get('history'))
    if not message.strip():
        return jsonify({'error': 'No message'}), 400

    forced = message.strip().lower().startswith('/check')
    text = message.strip()[6:].strip() if forced else message

    def gen():
        try:
            if forced and not text:
                msg = 'Paste the message after /check, for example:\n/check Your account is suspended, click here to verify'
                yield _ndjson({'t': msg})
                yield _ndjson({'done': True, 'response': msg})
                return
            if not message.startswith('[SCAN REPORT]') and (forced or _TRI_CHECK_REQ.search(message) or tri_rules_analyze(message)['score'] >= 30):
                with model_lock:
                    t = tri_classify(text, llm=llm)
                out = tri_format(t)
                for ln in out.split('\n'):
                    yield _ndjson({'t': ln + '\n'})
                yield _ndjson({'done': True, 'response': out, 'triage': t})
                return

            token_limits = {'short': None, 'detailed': 450, 'professional': 600}
            max_tokens = token_limits.get(config.get('responseLength', 'detailed'), 450) or 200
            messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
            if config.get('sessionMemory') and history:
                for turn in history[-5:]:
                    if turn.get('user'):
                        messages.append({'role': 'user', 'content': turn['user']})
                    if turn.get('assistant'):
                        messages.append({'role': 'assistant', 'content': turn['assistant']})
            messages.append({'role': 'user', 'content': message})

            parts = []
            with model_lock:
                for chunk in llm.create_chat_completion(messages=messages, max_tokens=max_tokens,
                                                        temperature=0.7, top_p=0.9,
                                                        repeat_penalty=1.1, stream=True):
                    piece = chunk['choices'][0]['delta'].get('content')
                    if piece:
                        parts.append(piece)
                        yield _ndjson({'t': piece})
            yield _ndjson({'done': True, 'response': ''.join(parts).strip()})
        except Exception as e:
            print(f'Error in stream endpoint: {e}')
            yield _ndjson({'error': str(e)})

    return Response(stream_with_context(gen()), mimetype='application/x-ndjson',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


from flask import Response, stream_with_context


def _nd(obj):
    return json.dumps(obj) + '\n'


@app.route('/api/triage/batch', methods=['POST'])
def triage_batch():
    data = request.get_json(silent=True) or {}
    texts = data.get('texts')
    if not isinstance(texts, list) or not texts:
        return jsonify({'error': 'No messages'}), 400
    texts = texts[:5000]
    use_ai = data.get('mode') != 'fast' and model_loaded

    def gen():
        for i, tx in enumerate(texts):
            try:
                tx = str(tx or '').strip()[:3000]
                if not tx:
                    yield _nd({'i': i, 'skip': True})
                    continue
                if use_ai and tri_rules_analyze(tx)['score'] < 70:
                    with model_lock:
                        r = tri_classify(tx, llm=llm)
                else:
                    r = tri_classify(tx, llm=None)
                yield _nd({'i': i, 'r': r})
            except Exception as e:
                yield _nd({'i': i, 'error': str(e)})
        yield _nd({'done': True, 'total': len(texts)})

    return Response(stream_with_context(gen()), mimetype='application/x-ndjson',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/csv/save', methods=['POST'])
def csv_save():
    import csv
    data = request.get_json(silent=True) or {}
    header = data.get('header') or []
    rows = data.get('rows') or []
    folder = os.path.join(BASE_PATH, 'results')
    os.makedirs(folder, exist_ok=True)
    name = re.sub(r'[^A-Za-z0-9_.-]', '_', str(data.get('name') or 'triage'))[:60]
    path = os.path.join(folder, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return jsonify({'path': path, 'rows': len(rows)})


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
