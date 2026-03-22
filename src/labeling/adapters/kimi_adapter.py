import os
import httpx
from .base import BaseLLMAdapter, LabelingResult


class KimiAdapter(BaseLLMAdapter):
    """Moonshot Kimi 适配器（兼容 OpenAI 接口格式）"""

    def __init__(self, config: dict):
        super().__init__(config)
        api_key = os.environ.get(config.get("api_key_env", "KIMI_API_KEY"))
        if not api_key:
            raise ValueError("未设置 KIMI_API_KEY 环境变量")
        self.api_key = api_key
        self.model = config.get("model", "moonshot-v1-128k")
        self.base_url = config.get("base_url", "https://api.moonshot.cn/v1")
        self.max_tokens = config.get("max_tokens", 1024)

    def detect_nests(self, image_path: str, prompt: str) -> LabelingResult:
        result = LabelingResult(image_path=image_path)
        try:
            image_data, media_type = self.encode_image_base64(image_path)

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是一个专业的林业病虫害检测AI助手，"
                            "专门识别无人机航拍图像中的樟巢螟虫巢。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    },
                ],
            }

            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            result.raw_response = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            result.token_input = usage.get("prompt_tokens", 0)
            result.token_output = usage.get("completion_tokens", 0)

        except httpx.HTTPStatusError as e:
            result.error = f"HTTP错误 {e.response.status_code}: {e.response.text[:200]}"
        except Exception as e:
            result.error = f"未知错误: {e}"

        return result
