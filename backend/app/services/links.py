from app.config import settings


def build_public_url(empresa, token, is_orcamento: bool = False) -> str:
    """Monta o link público de uma proposta (/p/) ou orçamento (/o/).

    Nunca usa cabeçalhos da requisição (Origin/Host são controláveis pelo cliente).
    """
    base = settings.FRONTEND_URL.rstrip("/")
    if settings.PUBLIC_LINKS_USE_TENANT_DOMAIN and empresa is not None:
        if empresa.dominio_personalizado:
            base = f"https://{empresa.dominio_personalizado}"
        elif empresa.subdominio:
            base = f"https://{empresa.subdominio}.{settings.BASE_DOMAIN}"
    return f"{base}/{'o' if is_orcamento else 'p'}/{token}"
