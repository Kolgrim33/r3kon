"""
R3KON triage: offline phishing / scam detection with a Low/Medium/High risk score.

Hybrid design:
  1. Rules layer  - Zimbabwe-specific scam patterns + URL checks (fast, consistent)
  2. Local LLM    - the GGUF model already loaded by R3KON (judgement + wording)
  3. Combiner     - blends both into one 0-100 score, then Low / Medium / High

Everything runs on-device. If the LLM is unavailable or returns junk, the rules
layer still produces a complete, valid answer.
"""
import json
import re
from urllib.parse import urlparse

# --------------------------------------------------------------------------- #
# Rules
# --------------------------------------------------------------------------- #
# (id, regex, weight 0-100, threat type, plain-language reason)
RULES = [
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
_COMPILED = [(i, re.compile(p, re.I | re.S), w, t, r) for i, p, w, t, r in RULES]

# --------------------------------------------------------------------------- #
# URL checks
# --------------------------------------------------------------------------- #
URL_RE = re.compile(
    r"(?i)\b((?:https?://|www\.)[^\s<>\"']+"
    r"|[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|co\.zw|zw|xyz|top|click|link|info|ru|tk|ml|ga|cf|gq|"
    r"site|online|vip|cc|shop|club)(?:/[^\s<>\"']*)?)")

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly",
              "rb.gy", "shorturl.at", "tiny.cc"}
RISKY_TLDS = (".xyz", ".top", ".click", ".link", ".tk", ".ml", ".ga", ".cf", ".gq",
              ".ru", ".vip", ".cc", ".site", ".online", ".club", ".shop")
BRANDS = ["ecocash", "econet", "netone", "onemoney", "telecash", "zesa", "zimra", "cbz",
          "stanbic", "fbc", "steward", "innbucks", "paynow", "nedbank", "absa", "rbz", "telone"]
OFFICIAL = ("ecocash.co.zw", "econet.co.zw", "netone.co.zw", "telone.co.zw", "zesa.co.zw",
            "zimra.co.zw", "rbz.co.zw", "cbz.co.zw", "stanbicbank.co.zw", "fbc.co.zw",
            "nedbank.co.zw", "steward.co.zw", "innbucks.co.zw", "paynow.co.zw", "absa.co.zw")


def _host(url):
    u = url if "://" in url else "http://" + url
    try:
        return (urlparse(u).hostname or "").lower()
    except ValueError:
        return ""


def url_signals(text):
    """Return (list of (weight, threat_type, reason), list of urls found)."""
    sigs, urls = [], []
    for m in URL_RE.finditer(text):
        raw = m.group(1).rstrip(".,;:!?)")
        urls.append(raw)
        host = _host(raw)
        if not host:
            continue
        official = any(host == d or host.endswith("." + d) for d in OFFICIAL)
        if official:
            continue
        sigs.append((8, "Malicious link", f"It contains a link ({host}) you didn't ask for."))
        if host in SHORTENERS:
            sigs.append((25, "Malicious link", f"{host} is a link shortener that hides the real destination."))
        if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
            sigs.append((35, "Malicious link", "The link points to a raw IP address instead of a real website name."))
        if host.endswith(RISKY_TLDS):
            sigs.append((25, "Malicious link", f"The link ends in a domain type ({host.rsplit('.', 1)[-1]}) often used for scams."))
        if any(b in host for b in BRANDS):
            sigs.append((45, "Phishing", f"The link ({host}) imitates a known Zimbabwean brand but is not its real website."))
        if host.count("-") >= 2:
            sigs.append((10, "Malicious link", "The web address is stuffed with hyphens, a typical fake-site pattern."))
        if "@" in raw:
            sigs.append((20, "Malicious link", "The link contains an '@', a trick to disguise the real site."))
        if raw.lower().startswith("http://"):
            sigs.append((8, "Malicious link", "The link is not encrypted (http, not https)."))
    return sigs, urls


def rules_analyze(text):
    """Noisy-OR of all signals -> 0-100 score, dominant threat type, reasons."""
    signals = []
    for rid, rx, w, t, reason in _COMPILED:
        if rx.search(text):
            signals.append((w, t, reason))
    usigs, urls = url_signals(text)
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
THREATS = ["Phishing", "Financial scam", "Identity fraud", "Malicious link",
           "AI-enabled threat", "Benign"]

SCHEMA = {
    "type": "object",
    "properties": {
        "suspicious": {"type": "boolean"},
        "threat_type": {"type": "string", "enum": THREATS},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "why": {"type": "string"},
    },
    "required": ["suspicious", "threat_type", "score", "why"],
}

SYSTEM = (
    "You are a cybersecurity assistant that protects ordinary people in Zimbabwe from scams. "
    "Judge the message. Typical local threats: fake EcoCash/OneMoney/bank messages, 'sent by mistake' "
    "reversal scams, fake prizes, advance-fee and job scams, SIM/account suspension links, "
    "relative-on-a-new-number requests, cloned voices. "
    "Normal messages (family chat, lecturer notices, real receipts, genuine reminders) are Benign with a low score. "
    "score: 0 = certainly safe, 100 = certainly malicious. "
    "why: ONE short sentence in plain English a non-technical person understands. "
    "Reply with JSON only."
)


def llm_analyze(llm, text, hints):
    if llm is None:
        return None
    hint_txt = ("\nSignals already detected: " + "; ".join(hints[:4])) if hints else ""
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Message to check:\n\"\"\"\n{text[:1500]}\n\"\"\"{hint_txt}"},
    ]
    try:
        out = llm.create_chat_completion(
            messages=msgs, temperature=0.0, max_tokens=160,
            response_format={"type": "json_object", "schema": SCHEMA})
        raw = out["choices"][0]["message"]["content"]
        data = json.loads(raw)
        data["score"] = max(0, min(100, int(data.get("score", 0))))
        if data.get("threat_type") not in THREATS:
            data["threat_type"] = "Benign" if data["score"] < 30 else "Phishing"
        return data
    except Exception as e:  # any failure -> rules-only fallback
        print(f"[triage] LLM layer skipped: {e}")
        return None


# --------------------------------------------------------------------------- #
# Actions
# --------------------------------------------------------------------------- #
ACTIONS = {
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
DEFAULT_LOW = "No action needed. Stay careful with links and never share your PIN or OTP."
DEFAULT_MED = "Verify the sender through an official channel before acting on this."


def pick_action(threat, risk):
    if risk == "Low":
        return DEFAULT_LOW
    return ACTIONS.get(threat, {}).get(risk) or ACTIONS.get(threat, {}).get("High") or DEFAULT_MED


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def risk_from_score(score):
    if score >= 60:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def classify(text, llm=None):
    text = (text or "").strip()
    if not text:
        return {"error": "Empty message"}

    r = rules_analyze(text)
    l = llm_analyze(llm, text, r["reasons"])

    if l is not None:
        score = round(0.5 * r["score"] + 0.5 * l["score"])
        if r["score"] >= 60:                 # strong rule evidence is never diluted
            score = max(score, r["score"])
        engine = "Rules + local AI (offline)"
    else:
        score = r["score"]
        engine = "Rules only (offline)"

    risk = risk_from_score(score)
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
        if suspicious and l["why"] not in reasons:
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
        "action": pick_action(threat, risk),
        "engine": engine,
        "rule_score": r["score"],
        "ai_score": l["score"] if l else None,
        "links_found": r["urls"],
    }


if __name__ == "__main__":
    tests = [
        "Congratulations! You have won $500 in the EcoCash promo. Send your PIN to claim your prize within 24 hours.",
        "Your CBZ account has been suspended. Verify now: http://cbz-secure-login.xyz/verify",
        "I sent you $20 by mistake. Please reverse the transaction urgently.",
        "Hi, this is your son, I lost my phone, this is my new number. Please send airtime urgently.",
        "Lecturer notice: tomorrow's SIT lecture moves to Room 204 at 10am.",
        "Your ZESA token purchase of $10 was successful. Ref 88213.",
    ]
    for t in tests:
        res = classify(t)
        print(f"{res['risk']:<6} {res['score']:>3}  {res['threat_type']:<16} | {t[:60]}")
