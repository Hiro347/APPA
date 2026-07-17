import logging
from huggingface_hub import InferenceClient, AsyncInferenceClient
from config import settings
from ai.mock_llm import get_mock_response, get_mock_response_stream

logger = logging.getLogger(__name__)

client = None
async_client = None
if settings.HF_API_TOKEN:
    try:
        client = InferenceClient(model=settings.HF_MODEL_ID, token=settings.HF_API_TOKEN)
        async_client = AsyncInferenceClient(model=settings.HF_MODEL_ID, token=settings.HF_API_TOKEN)
    except Exception as e:
        logger.error(f"Failed to initialize HuggingFace Clients: {e}")
        client = None
        async_client = None


def call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Call the LLM via HuggingFace Inference API (Synchronous).
    Used for internal data processing (decomposition, condensation).
    """
    if client:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=settings.HF_MODEL_ID,
                messages=messages,
                max_tokens=1024,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"HuggingFace API call failed: {e}. Delegating to mock_llm.")

    return get_mock_response(prompt, system_prompt)

async def call_llm_stream(prompt: str, system_prompt: str = ""):
    """
    Call the LLM via HuggingFace Inference API with async streaming.
    Used for the final chat response rendered to the user.
    """
    if async_client:
        try:
            full_prompt = ""
            if system_prompt:
                full_prompt += f"<|system|>\n{system_prompt}\n"
            full_prompt += f"<|user|>\n{prompt}\n<|assistant|>\n"

            async for chunk in await async_client.text_generation(
                prompt=full_prompt,
                max_new_tokens=1024,
                temperature=0.3,
                repetition_penalty=1.1,
                stream=True,
            ):
                yield chunk
            return
        except Exception as e:
            logger.warning(f"HuggingFace API stream failed: {e}. Delegating to mock_llm stream.")

    async for chunk in get_mock_response_stream(prompt, system_prompt):
        yield chunk

