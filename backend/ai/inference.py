import logging
from huggingface_hub import InferenceClient
from config import settings
from ai.mock_llm import get_mock_response

logger = logging.getLogger(__name__)

# Initialize Hugging Face client.
# If HF_API_TOKEN is empty, call_llm automatically uses the mock module.
client = None
if settings.HF_API_TOKEN:
    try:
        client = InferenceClient(model=settings.HF_MODEL_ID, token=settings.HF_API_TOKEN)
    except Exception as e:
        logger.error(f"Failed to initialize HuggingFace InferenceClient: {e}")
        client = None


def call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Call the LLM via HuggingFace Inference API.
    Falls back to ai/mock_llm.py when no token is set or the API call fails.
    """
    if client:
        try:
            full_prompt = ""
            if system_prompt:
                full_prompt += f"<|system|>\n{system_prompt}\n"
            full_prompt += f"<|user|>\n{prompt}\n<|assistant|>\n"

            response = client.text_generation(
                prompt=full_prompt,
                max_new_tokens=1024,
                temperature=0.3,
                repetition_penalty=1.1,
            )
            return response.strip()
        except Exception as e:
            logger.warning(f"HuggingFace API call failed: {e}. Delegating to mock_llm.")

    return get_mock_response(prompt, system_prompt)

