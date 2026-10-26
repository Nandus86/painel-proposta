from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from app.config import settings

DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash"
LLM_TIMEOUT = 90


def llm_disponivel() -> bool:
    """True se há um provedor configurado via variáveis de ambiente (fallback do OpenRouter)."""
    provider = settings.LLM_PROVIDER.lower()
    if provider == "openai":
        return bool(settings.OPENAI_API_KEY) and not settings.OPENAI_API_KEY.startswith("sk-your")
    if provider == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY) and not settings.ANTHROPIC_API_KEY.startswith("sk-ant-your")
    return provider == "ollama"


def get_llm(openrouter_key: str = None, openrouter_model: str = None):
    """Retorna o LLM configurado: OpenRouter (definido pelo superadmin) ou o provedor do .env."""
    if openrouter_key:
        model_name = (openrouter_model or "").strip() or DEFAULT_OPENROUTER_MODEL
        # Modelos do OpenRouter têm o formato "provedor/modelo"
        if "/" not in model_name:
            model_name = f"openai/{model_name}" if model_name.startswith("gpt") else DEFAULT_OPENROUTER_MODEL

        return ChatOpenAI(
            model=model_name,
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            timeout=LLM_TIMEOUT,
            max_retries=1,
            default_headers={
                "HTTP-Referer": settings.FRONTEND_URL,
                "X-Title": settings.APP_NAME,
            },
        )

    provider = settings.LLM_PROVIDER.lower()
    if provider == "openai":
        return ChatOpenAI(model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, timeout=LLM_TIMEOUT, max_retries=1)
    if provider == "anthropic":
        return ChatAnthropic(model=settings.LLM_MODEL, api_key=settings.ANTHROPIC_API_KEY, timeout=LLM_TIMEOUT, max_retries=1)
    if provider == "ollama":
        # Ollama expõe API compatível com OpenAI em /v1
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",
            timeout=LLM_TIMEOUT,
        )
    raise ValueError(f"Provider de LLM desconhecido: {settings.LLM_PROVIDER}")
