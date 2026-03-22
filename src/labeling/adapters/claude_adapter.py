import os
import logging
from typing import Optional

try:
    from anthropic import (
        Anthropic,
        RateLimitError as AnthropRateLimitError,
        APIError as AnthropAPIError,
    )
except Exception:  # pragma: no cover
    Anthropic = None  # type: ignore
    AnthropRateLimitError = Exception  # type: ignore
    AnthropAPIError = Exception  # type: ignore

from .base import BaseLLMAdapter, LabelingResult

logger = logging.getLogger(__name__)


class ClaudeAdapter(BaseLLMAdapter):
    """
    Claude Adapter for Anthropic Claude API.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        if Anthropic is None:
            raise ImportError("anthropic SDK is not installed")
        # Initialize the Anthropic client
        self.client = Anthropic(api_key=api_key)
        # Defaults that can be overridden by subclass/config
        self.model_name = getattr(self, "model_name", "claude-2")
        self.max_tokens = getattr(self, "max_tokens_to_sample", 2048)

    def detect_nests(self) -> LabelingResult:
        """
        Detect forestry nests from the currently loaded image.
        Steps:
        - Encode image to base64 via base class helper
        - Build a prompt with the system prompt and image payload
        - Call Claude API and wrap response in LabelingResult
        - Propagate API errors for caller to handle
        """
        try:
            image_b64 = self.encode_image_base64()
            system_prompt = self._get_system_prompt()
            # Include a portion of the image data with the system prompt for context
            input_payload = (
                f"{system_prompt}\n\nImage (base64, truncated): {image_b64[:1000]}..."
            )

            response = self.client.completion(
                prompt=input_payload,
                model=self.model_name,
                max_tokens_to_sample=self.max_tokens,
            )

            raw_text = ""
            tokens = 0
            if isinstance(response, dict):
                raw_text = response.get("completion") or response.get("text") or ""
                usage = response.get("usage") or {}
                tokens = int(usage.get("total_tokens", 0) or 0)
            else:
                raw_text = str(response)

            return LabelingResult(raw_response=raw_text, tokens=tokens)
        except AnthropRateLimitError as e:
            logger.warning("Anthropic Claude rate limit reached: %s", e)
            raise
        except AnthropAPIError as e:
            logger.error("Anthropic Claude API error: %s", e)
            raise
        except Exception:
            logger.exception("Unexpected error in ClaudeAdapter.detect_nests")
            raise

    def _get_system_prompt(self) -> str:
        """Return the forestry nest detection system prompt."""
        return (
            "System: You are an AI assistant specialized in forestry nest detection. "
            "Given an input image provided as a base64-encoded string, identify any nests present, "
            "estimate their type (e.g., bird nest, insect nest) if possible, and provide approximate "
            "locations within the image along with a confidence score. Return a concise, structured response "
            "that is easy to parse downstream."
        )
