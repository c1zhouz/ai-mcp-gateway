from openai import AsyncOpenAI

def create_llm_client(api_key: str, base_url: str = None):
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)
