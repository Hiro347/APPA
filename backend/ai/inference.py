import logging
import asyncio
from huggingface_hub import InferenceClient, AsyncInferenceClient
from config import settings

logger = logging.getLogger(__name__)

# Initialize Hugging Face Clients
client = None
async_client = None

if settings.HF_API_TOKEN:
    try:
        client = InferenceClient(model=settings.HF_MODEL_ID, token=settings.HF_API_TOKEN)
        async_client = AsyncInferenceClient(model=settings.HF_MODEL_ID, token=settings.HF_API_TOKEN)
        logger.info(f"Hugging Face clients initialized successfully for model: {settings.HF_MODEL_ID}")
    except Exception as e:
        logger.error(f"Failed to initialize Hugging Face clients: {e}")
else:
    logger.warning("HF_API_TOKEN not found. LLM calls will fail.")

def call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Call the LLM via Hugging Face Inference API (Synchronous).
    Used for internal data processing (decomposition, condensation).
    """
    if not client:
        raise ValueError("Hugging Face client not initialized. Check HF_API_TOKEN.")

    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat_completion(
            messages=messages,
            max_tokens=2048,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Hugging Face API call failed: {e}")
        raise e


# Global lock to prevent slamming the API with concurrent requests
_api_lock = asyncio.Lock()

async def async_call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Async wrapper for call_llm with a strict concurrency lock.
    Prevents 429 Rate Limit errors when multiple search pipelines condense data simultaneously.
    """
    async with _api_lock:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, call_llm, prompt, system_prompt)


async def call_llm_stream(prompt: str, system_prompt: str = ""):
    """
    Call the LLM via Hugging Face Inference API with async streaming.
    Used for the final chat response (assessment/synthesis).
    """
    if not async_client:
        raise ValueError("Hugging Face async client not initialized. Check HF_API_TOKEN.")

    try:
        messages = []
        if system_prompt:
            # Enforce strict JSON requirement for HF since it lacks response_mime_type
            system_prompt += "\n\nCRITICAL RULE: You must respond ONLY with a raw, valid JSON object. Do not wrap it in markdown code blocks like ```json. Your very first character must be '{'."
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response_stream = await async_client.chat_completion(
            messages=messages,
            max_tokens=4096,
            temperature=0.3,
            stream=True
        )
        
        async for chunk in response_stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except Exception as e:
        logger.error(f"Hugging Face API stream failed: {e}")
        raise e

