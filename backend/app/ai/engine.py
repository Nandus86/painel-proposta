from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from app.config import settings

def get_llm(openrouter_key: str = None, openrouter_model: str = None):
    """Returns the configured LLM instance."""
    if openrouter_key:
        # If openrouter_key is provided, we route requests to OpenRouter.
        model_name = openrouter_model or settings.LLM_MODEL
        if not model_name or "gpt" not in model_name and "claude" not in model_name and "gemini" not in model_name and "llama" not in model_name:
            model_name = "google/gemini-2.5-flash"
        elif "gpt-4o" in model_name and "/" not in model_name:
            model_name = "openai/gpt-4o"
        
        return ChatOpenAI(
            model=model_name,
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            default_headers={
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "Painel Proposta",
            }
        )

    if settings.LLM_PROVIDER == "openai":
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY
        )
    elif settings.LLM_PROVIDER == "anthropic":
        return ChatAnthropic(
            model=settings.LLM_MODEL,
            api_key=settings.ANTHROPIC_API_KEY
        )
    elif settings.LLM_PROVIDER == "ollama":
        # Ollama supports OpenAI-compatible API at /v1
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama" # Required but ignored by Ollama
        )
    else:
        raise ValueError(f"Provider de LLM desconhecido: {settings.LLM_PROVIDER}")
