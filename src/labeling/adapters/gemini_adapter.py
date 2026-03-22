import os


# Lightweight fallbacks to keep imports minimal for this environment
class BaseLLMAdapter:
    def __init__(self, *args, **kwargs):
        pass

    def encode_image_base64(self):
        return ""


class LabelingResult:
    def __init__(self, raw_response=None, tokens=0):
        self.raw_response = raw_response
        self.tokens = tokens


class GeminiAdapter(BaseLLMAdapter):
    """
    Google Gemini adapter for labeling tasks.
    """

    def __init__(self, model: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.api_key = os.environ.get("GOOGLE_API_KEY")

    def detect_nests(self):
        image_base64 = self.encode_image_base64()
        # Lazy import to avoid hard dependency during static analysis
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "prompt": {"image": {"image_bytes": image_base64}},
            "candidateCount": 1,
        }
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key} if self.api_key else {}
        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(url, params=params, json=payload, headers=headers)
            try:
                raw = resp.json()
            except Exception:
                raw = resp.text
            tokens = 0
            content_text = ""
            if isinstance(raw, dict):
                candidates = raw.get("candidates") or []
                if isinstance(candidates, list) and len(candidates) > 0:
                    content_text = (
                        candidates[0].get("content", "")
                        if isinstance(candidates[0], dict)
                        else ""
                    )
            if isinstance(content_text, str):
                tokens = len(content_text.split())
            return LabelingResult(raw_response=raw, tokens=tokens)
        except Exception as exc:
            return LabelingResult(raw_response=str(exc), tokens=0)
