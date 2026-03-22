import os
from openai import OpenAI
from .base import BaseLLMAdapter, LabelingResult


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI GPT-4o 适配器"""

    def __init__(self, config: dict):
        super().__init__(config)
        api_key = os.environ.get(config.get("api_key_env", "OPENAI_API_KEY"))
        if not api_key:
            raise ValueError("未设置 OPENAI_API_KEY 环境变量")
        self.client = OpenAI(api_key=api_key)
        self.model = config.get("model", "gpt-4o")
        self.max_tokens = config.get("max_tokens", 1024)

    def detect_nests(self, image_path: str, prompt: str) -> LabelingResult:
        result = LabelingResult(image_path=image_path)
        try:
            image_data, media_type = self.encode_image_base64(image_path)

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
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
            )

            result.raw_response = response.choices[0].message.content
            result.token_input = response.usage.prompt_tokens
            result.token_output = response.usage.completion_tokens

        except Exception as e:
            result.error = f"OpenAI错误: {e}"

        return result
