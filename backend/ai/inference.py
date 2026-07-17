import logging
from huggingface_hub import InferenceClient, AsyncInferenceClient
from config import settings

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
                max_tokens=4096,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"HuggingFace API call failed: {e}")
            raise e
    
    raise ValueError("HuggingFace API token or client not initialized.")

import asyncio
# Global lock to prevent slamming the free HuggingFace API with concurrent requests
hf_api_lock = asyncio.Lock()

async def async_call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Async wrapper for call_llm with a strict concurrency lock.
    Prevents 429 Rate Limit errors when multiple search pipelines condense data simultaneously.
    """
    async with hf_api_lock:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, call_llm, prompt, system_prompt)

async def call_llm_stream(prompt: str, system_prompt: str = ""):
    """
    Call the LLM via HuggingFace Inference API with async streaming.
    Used for the final chat response rendered to the user.
    """
    if async_client:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            stream = await async_client.chat_completion(
                messages=messages,
                max_tokens=4096,
                temperature=0.3,
                stream=True,
            )
            async for chunk in stream:
                yield chunk.choices[0].delta.content or ""
            return
        except Exception as e:
            logger.error(f"HuggingFace API stream failed: {e}")
            raise e

    raise ValueError("HuggingFace API async client not initialized.")

