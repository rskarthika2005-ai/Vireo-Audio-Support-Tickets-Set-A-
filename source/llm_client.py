import time
from google import genai
from google.genai import types
from source import config


RETRY_CODES = (429, 500, 503)


def get_client():
    if not config.API_KEY:
        raise ValueError("API key not found. Add GEMINI_API_KEY to the .env file.")
    return genai.Client(api_key=config.API_KEY)


def call_llm(client, system_prompt, user_message, tries=6):
    last_error = None
    for attempt in range(tries):
        try:
            response = client.models.generate_content(
                model=config.MODEL_NAME,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    max_output_tokens=500,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
            usage = response.usage_metadata
            tokens_in = usage.prompt_token_count or 0
            tokens_out = usage.candidates_token_count or 0
            return response.text or "", tokens_in, tokens_out
        except Exception as error:
            last_error = error
            code = getattr(error, "code", None)
            if code is not None and code not in RETRY_CODES:
                raise RuntimeError("model call failed: " + str(error))
            if attempt < tries - 1:
                wait = min(60, 10 * (2 ** attempt))      # 10s, 20s, 40s, 60s, 60s
                print(f"  retry {attempt + 1}/{tries - 1} in {wait}s: {str(error)[:90]}")
                time.sleep(wait)
    raise RuntimeError("model call failed after " + str(tries) + " tries: " + str(last_error))