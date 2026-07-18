import logging
import asyncio
import re
from huggingface_hub import InferenceClient, AsyncInferenceClient
from config import settings

logger = logging.getLogger(__name__)

# Initialize Local Hugging Face Client (via OpenAI-Compatible llama.cpp server)
client = None
async_client = None

try:
    # Use base_url to point to the local docker container (or localhost if running natively)
    # api_key is required by the SDK but ignored by llama.cpp
    client = InferenceClient(base_url=settings.LOCAL_LLM_URL, api_key="sk-no-key-required")
    async_client = AsyncInferenceClient(base_url=settings.LOCAL_LLM_URL, api_key="sk-no-key-required")
    logger.info(f"Local LLM clients initialized successfully, pointing to: {settings.LOCAL_LLM_URL}")
except Exception as e:
    logger.error(f"Failed to initialize Local LLM clients: {e}")

def call_llm(prompt: str, system_prompt: str = "", enforce_json: bool = False) -> str:
    """
    Call the LLM via Hugging Face Inference API (Synchronous).
    Used for internal data processing (decomposition, condensation).
    """
    if not client:
        raise ValueError("Local LLM client not initialized.")

    try:
        messages = []
        if system_prompt:
            if enforce_json:
                system_prompt += "\n\nProvide the output in JSON format."
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.0
        }
        if enforce_json:
            kwargs["response_format"] = {"type": "json_object"}
            
        response = client.chat_completion(**kwargs)
        content = response.choices[0].message.content
        
        # DeepSeek-R1 compatibility: Strip out <think> tags completely
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        
        return content
    except Exception as e:
        logger.error(f"Hugging Face API call failed: {e}")
        raise e


# Global lock to prevent slamming the API with concurrent requests
_api_lock = asyncio.Lock()

async def async_call_llm(prompt: str, system_prompt: str = "", enforce_json: bool = False) -> str:
    """
    Async wrapper for call_llm with a strict concurrency lock.
    Prevents 429 Rate Limit errors when multiple search pipelines condense data simultaneously.
    """
    async with _api_lock:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, call_llm, prompt, system_prompt, enforce_json)


async def call_llm_stream(prompt: str, system_prompt: str = "", enforce_json: bool = False):
    """
    Call the LLM via Hugging Face Inference API with async streaming.
    Used for the final chat response (assessment/synthesis).
    """
    if not async_client:
        raise ValueError("Local LLM async client not initialized.")

    try:
        messages = []
        if system_prompt:
            if enforce_json:
                system_prompt += "\n\nCRITICAL RULE: You must respond ONLY with a raw, valid JSON object. Do not wrap it in markdown code blocks like ```json. Your very first character must be '{'."
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response_stream = await async_client.chat_completion(
            messages=messages,
            max_tokens=1000,
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

