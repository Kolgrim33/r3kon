import json, re, sys
from llama_cpp import Llama

llm = Llama(model_path="model/qwen1.5-1.8b-chat-q4_k_m.gguf",
            n_ctx=2048, n_threads=6, verbose=False)

SYSTEM = """You are Cyber Shield Zimbabwe, a scam and threat triage assistant.
Reply with ONLY a JSON object with these keys:
"suspicious": true or false,
"threat_type": one of "phishing", "financial_scam", "identity_fraud", "malicious_link", "ai_threat", "benign",
"risk": "Low", "Medium" or "High",
"explanation": 1-2 plain sentences saying why,
"action": one clear thing the person should do."""

def classify(text: str) -> dict:
    out = llm.create_chat_completion(
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": text}],
        temperature=0.1, max_tokens=250)
    raw = out["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        return json.loads(m.group(0))
    except Exception:
        return {"suspicious": True, "threat_type": "unknown", "risk": "Medium",
                "explanation": "Could not analyse this reliably.",
                "action": "Do not click links or reply; verify with the sender directly."}

if __name__ == "__main__":
    print(json.dumps(classify(sys.argv[1]), indent=2))
