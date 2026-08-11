"""AI abstraction. MAGNET must run with zero keys: DemoProvider is deterministic
and always available. Live providers activate only when their env var is set.
Nothing here sends/publishes anything -- callers always route output through
the Approval Inbox (see routers/approvals.py)."""
import hashlib
import json
import os
import urllib.request


class LLMProvider:
    name = "base"

    def draft(self, system: str, prompt: str) -> str:
        raise NotImplementedError


class DemoProvider(LLMProvider):
    """Deterministic, seeded text generation -- no network, no key, reproducible."""
    name = "demo"

    def draft(self, system: str, prompt: str) -> str:
        seed = int(hashlib.sha256((system + prompt).encode()).hexdigest(), 16) % 997
        opener = ["Quick thought", "Noticed this", "Sharing a quick idea", "One thing that might help"][seed % 4]
        return f"{opener}: {prompt.strip()[:280]}"


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def draft(self, system: str, prompt: str) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={self.api_key}"
        )
        body = json.dumps({
            "contents": [{"parts": [{"text": f"{system}\n\n{prompt}"}]}]
        }).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return data["candidates"][0]["content"]["parts"][0]["text"]


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def draft(self, system: str, prompt: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        body = json.dumps({
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


def get_provider() -> LLMProvider:
    if os.environ.get("GEMINI_API_KEY"):
        return GeminiProvider(os.environ["GEMINI_API_KEY"])
    if os.environ.get("GROQ_API_KEY"):
        return GroqProvider(os.environ["GROQ_API_KEY"])
    return DemoProvider()


def is_live_mode() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY"))
