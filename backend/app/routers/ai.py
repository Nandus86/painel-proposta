from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from app.database import get_db
from app.ai.engine import get_llm
from app.core.dependencies import get_current_active_user
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.sistema_config import SistemaConfig
from app.core.security import decrypt_data
from langchain_core.messages import HumanMessage, SystemMessage

router = APIRouter(prefix="/api/ai", tags=["AI"])

@router.get("/openrouter/models")
async def get_openrouter_models():
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
        print(f"Erro ao buscar modelos do OpenRouter: {e}")
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

    hoje = date.today()
    if empresa.ai_credits_last_reset != hoje:
        empresa.ai_credits_used_today = 0
        empresa.ai_credits_last_reset = hoje

    if empresa.ai_credits_used_today >= empresa.ai_credits_limit:
        raise HTTPException(status_code=429, detail="Limite diário de uso de IA atingido.")

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
        Você é um consultor comercial especialista de alto impacto. Sua tarefa é preencher e expandir um modelo/molde de proposta comercial seguindo o estilo, tom de voz e estrutura fornecidos abaixo.
        
        === MODELO DE PROPOSTA ===
        {modelo_texto}
        =========================
        
        Substitua as variáveis dinâmicas (ex: {{{{cliente}}}}, {{{{valor_total}}}}, {{{{itens}}}}, etc.) e elabore o texto final com base nos seguintes dados reais da proposta atual:
        - Título da Proposta: {data.titulo}
        - Empresa Emitente (Quem está propondo): {empresa_nome}
        - Vendedor/Responsável pela Proposta: {vendedor_nome}
        - Cliente/Prospect: {data.cliente_nome}
        - Itens/Serviços e Cotações:
        {itens_str}
        - Valor Total da Proposta: R$ {valor_total:.2f}
        - Contexto/Instruções Adicionais do Usuário: {data.contexto or "Nenhum"}
        
        REGRAS IMPORTANTES:
        1. Formate a saída utilizando **Markdown**. Use **negrito** para destacar o nome do cliente, da nossa empresa, os nomes dos serviços/itens e os valores.
        2. Seja claro e cite nominalmente os serviços fornecidos e as pessoas/empresas envolvidas no corpo do texto.
        3. A proposta final deve soar profissional, persuasiva e estruturada.
        4. NÃO gere tabelas de preços, nem adicione blocos de assinaturas no final do texto. Isso já é gerado pelo sistema separadamente. Apenas gere o corpo/apresentação da proposta.
        5. Retorne EXCLUSIVAMENTE o conteúdo final da proposta (sem saudações da IA do tipo "Aqui está a proposta:").
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
        
        # Incrementar uso e salvar
        empresa.ai_credits_used_today += 1
        await db.commit()
        
        return {"descricao": response.content}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Erro ao gerar descrição com IA: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar IA: {str(e)}")

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

    hoje = date.today()
    if empresa.ai_credits_last_reset != hoje:
        empresa.ai_credits_used_today = 0
        empresa.ai_credits_last_reset = hoje
        await db.commit()

    return {
        "used": empresa.ai_credits_used_today,
        "limit": empresa.ai_credits_limit,
        "remaining": max(0, empresa.ai_credits_limit - empresa.ai_credits_used_today)
    }

