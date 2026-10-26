import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import httpx
from app.database import get_db
from app.ai.engine import get_llm, llm_disponivel
from app.core.dependencies import get_current_active_user, require_superuser
from app.models.plano import Plano
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.sistema_config import SistemaConfig
from app.core.security import decrypt_data
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI"])


async def _limite_ia(db: AsyncSession, empresa: Empresa) -> int:
    """Limite diário de IA: o do plano tem prioridade sobre o campo legado da empresa."""
    plano = await db.get(Plano, (empresa.plano or "gratuito").lower().strip())
    if plano and plano.ai_credits_limit is not None:
        return plano.ai_credits_limit
    return empresa.ai_credits_limit or 0


async def _reset_diario(db: AsyncSession, empresa: Empresa) -> None:
    hoje = date.today()
    if empresa.ai_credits_last_reset != hoje:
        empresa.ai_credits_used_today = 0
        empresa.ai_credits_last_reset = hoje
        await db.commit()


@router.get("/openrouter/models")
async def get_openrouter_models(current_user: Usuario = Depends(require_superuser)):
    """Busca a lista de modelos disponíveis no OpenRouter."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://openrouter.ai/api/v1/models")
            response.raise_for_status()
            data = response.json()
            models = []
            for item in data.get("data", []):
                models.append({
                    "id": item.get("id"),
                    "name": item.get("name")
                })
            # Ordenar por nome
            models.sort(key=lambda x: x["name"])
            return models
    except Exception as e:
        logger.warning("Erro ao buscar modelos do OpenRouter: %s", e)
        # Retornar uma lista de fallback em caso de falha de conexão/API offline
        return [
            {"id": "google/gemini-2.5-flash", "name": "Google: Gemini 2.5 Flash"},
            {"id": "google/gemini-2.5-pro", "name": "Google: Gemini 2.5 Pro"},
            {"id": "meta-llama/llama-3-8b-instruct", "name": "Meta: Llama 3 8B Instruct"},
            {"id": "meta-llama/llama-3-70b-instruct", "name": "Meta: Llama 3 70B Instruct"},
            {"id": "anthropic/claude-3-haiku", "name": "Anthropic: Claude 3 Haiku"},
            {"id": "anthropic/claude-3-5-sonnet", "name": "Anthropic: Claude 3.5 Sonnet"},
            {"id": "openai/gpt-4o-mini", "name": "OpenAI: GPT-4o Mini"},
            {"id": "openai/gpt-4o", "name": "OpenAI: GPT-4o"}
        ]

class ItemSchema(BaseModel):
    descricao: str
    quantidade: float
    preco_unitario: float
    subtotal: float
    instrucoes_ia: Optional[str] = None

class GenerateProposalDescriptionRequest(BaseModel):
    titulo: str
    cliente_nome: str
    itens_detalhes: Optional[List[ItemSchema]] = None
    itens: Optional[List[str]] = None
    modelo_conteudo: Optional[str] = None
    contexto: Optional[str] = None

@router.post("/proposta/gerar-descricao")
async def gerar_descricao_proposta(
    data: GenerateProposalDescriptionRequest,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Gera uma descrição persuasiva para uma proposta comercial usando IA com base em um modelo."""
    # Buscar empresa para créditos e chaves
    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(status_code=400, detail="Empresa não encontrada.")

    await _reset_diario(db, empresa)
    limite = await _limite_ia(db, empresa)
    if empresa.ai_credits_used_today >= limite:
        raise HTTPException(status_code=429, detail="Limite diário de uso de IA atingido. Tente novamente amanhã ou faça upgrade do plano.")

    # Buscar configurações globais de IA
    config_result = await db.execute(select(SistemaConfig).where(SistemaConfig.id == 1))
    sistema_config = config_result.scalar_one_or_none()

    openrouter_key = None
    openrouter_model = "google/gemini-2.5-flash"
    
    if sistema_config:
        if sistema_config.openrouter_key:
            openrouter_key = decrypt_data(sistema_config.openrouter_key)
        if sistema_config.openrouter_model:
            openrouter_model = sistema_config.openrouter_model
        
    if not openrouter_key and not llm_disponivel():
        raise HTTPException(status_code=503, detail="A geração com IA ainda não foi configurada pelo administrador do sistema.")

    llm = get_llm(openrouter_key=openrouter_key, openrouter_model=openrouter_model)
    
    itens_str = ""
    valor_total = 0.0
    if data.itens_detalhes:
        for idx, item in enumerate(data.itens_detalhes):
            itens_str += f"{idx+1}. {item.descricao} - Qtd: {item.quantidade} - Valor Unitário: R$ {item.preco_unitario:.2f} - Subtotal: R$ {item.subtotal:.2f}\n"
            if item.instrucoes_ia:
                itens_str += f"   [Instrução da Diretoria para este item: {item.instrucoes_ia}]\n"
            valor_total += item.subtotal
    elif data.itens:
        itens_str = "\n- ".join(data.itens)
        
    modelo_texto = data.modelo_conteudo or (empresa.modelo_proposta_padrao if empresa else "")
    
    vendedor_nome = current_user.nome
    empresa_nome = empresa.nome_fantasia or empresa.razao_social if empresa else "Nossa Empresa"

    if modelo_texto:
        prompt = f"""
        Você é um consultor comercial especialista de alto impacto. Sua tarefa é **preencher um modelo de proposta existente** substituindo APENAS as variáveis marcadas com {{{{...}}}} e completando seções inteiramente vazias.

        === REGRAS ESTRITAS DE PRESERVAÇÃO DO MODELO (PRIORIDADE MÁXIMA) ===
        1. PRESERVE EXATAMENTE o texto original do modelo. NÃO reescreva, parafraseie, resuma ou altere nenhuma frase que já esteja escrita no modelo.
        2. Apenas SUBSTITUA as variáveis ({{{{...}}}}) pelos valores reais fornecidos abaixo.
        3. Se uma seção do modelo estiver completamente vazia (sem texto além de variáveis ou títulos), você PODE preencher com 1-2 frases complementares relevantes ao contexto. NUNCA mais que isso.
        4. Se uma seção já tiver texto, MANTENHA-O 100% INTACTO, palavra por palavra.
        5. Mantenha os mesmos títulos (##), mesma estrutura de seções, mesmas listas e parágrafos do modelo.
        6. Mantenha o mesmo tom de voz, nível de formalidade e estilo do modelo original.
        7. O resultado final deve ter NO MÍNIMO 90% de similaridade textual com o modelo original. A similaridade é medida caractere por caractere.
        8. NÃO adicione novas seções, introduções, conclusões, saudações ou despedidas que não estejam no modelo.
        9. NÃO gere tabelas de preços nem blocos de assinatura (isso é feito pelo sistema separadamente).
        10. Retorne EXCLUSIVAMENTE o conteúdo final em Markdown, sem preâmbulos como "Aqui está a proposta:".
        =============================================================

        === MODELO DE PROPOSTA (PRESERVE ESTA ESTRUTURA) ===
        {modelo_texto}
        ====================================================

        DADOS REAIS PARA SUBSTITUIR AS VARIÁVEIS:
        - Cliente (Razão Social): {data.cliente_nome}
        - Empresa Emitente (Quem está propondo): {empresa_nome}
        - Vendedor/Responsável: {vendedor_nome}
        - Título da Proposta: {data.titulo}
        - Itens/Serviços e Cotações:
        {itens_str}
        - Valor Total da Proposta: R$ {valor_total:.2f}
        - Contexto/Instruções Adicionais do Usuário: {data.contexto or "Nenhum"}

        LEMBRE-SE: seu trabalho é PREENCHER um modelo existente, não criar um novo texto. Respeite a estrutura original.
        """
    else:
        prompt = f"""
        Você é um consultor comercial especialista em vendas e negócios de alto impacto.
        Gere um texto de apresentação persuasivo (que servirá como o corpo de uma proposta comercial) utilizando os seguintes dados:
        
        - Título da Proposta: {data.titulo}
        - Empresa Emitente (Nós): {empresa_nome}
        - Vendedor/Consultor Responsável: {vendedor_nome}
        - Cliente: {data.cliente_nome}
        - Serviços/Itens Inclusos na Proposta:
        {itens_str}
        
        Contexto adicional para alinhar a comunicação: {data.contexto or "Nenhum"}
        
        REGRAS DE REDAÇÃO E FORMATAÇÃO:
        1. Estruture a apresentação utilizando formatação **Markdown** (títulos como ##, listas com -, etc.).
        2. Use **negrito** obrigatoriamente para destacar o nome do cliente ({data.cliente_nome}), o nome da nossa empresa ({empresa_nome}), o nome do responsável ({vendedor_nome}), e os nomes principais dos serviços/produtos.
        3. O texto deve justificar a importância e os benefícios dos serviços que estamos oferecendo, relacionando-os diretamente à solução do problema do cliente.
        4. NÃO crie a tabela de orçamentos, cronogramas engessados, condições de pagamento ou campos de assinatura. O sistema já cuidará dessa parte fora do texto. Foco apenas na argumentação persuasiva e apresentação dos serviços e da parceria.
        5. Retorne APENAS o texto da apresentação, sem preâmbulos da IA (como "Aqui está a proposta solicitada").
        """
    
    try:
        messages = [
            SystemMessage(content="Você é um assistente de redação comercial."),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
    except Exception as e:
        logger.error("Erro ao gerar descrição com IA (empresa %s): %s", empresa.id, e)
        raise HTTPException(status_code=502, detail="O serviço de IA não respondeu. Tente novamente em instantes.")

    # Consome o crédito de forma atômica (requisições simultâneas não ultrapassam o limite)
    consumido = await db.execute(
        update(Empresa)
        .where(Empresa.id == empresa.id, Empresa.ai_credits_used_today < limite)
        .values(ai_credits_used_today=Empresa.ai_credits_used_today + 1)
    )
    await db.commit()
    if consumido.rowcount == 0:
        raise HTTPException(status_code=429, detail="Limite diário de uso de IA atingido.")

    return {"descricao": response.content}

@router.get("/credits")
async def get_ai_credits(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retorna o saldo de créditos de IA para o dia atual."""
    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(status_code=400, detail="Empresa não encontrada.")

    await _reset_diario(db, empresa)
    limite = await _limite_ia(db, empresa)

    return {
        "used": empresa.ai_credits_used_today,
        "limit": limite,
        "remaining": max(0, limite - empresa.ai_credits_used_today)
    }

