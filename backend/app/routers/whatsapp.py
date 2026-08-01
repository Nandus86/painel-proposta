from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.sistema_config import SistemaConfig
from app.core.dependencies import get_current_user, require_admin
from app.services.whatsapp import ensure_instance, connect, get_status, disconnect, send_text

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])


def _validate_uazapi_config(sistema_config: SistemaConfig):
    if not sistema_config.uazapi_base_url or not sistema_config.uazapi_admin_token:
        raise HTTPException(status_code=400, detail="WhatsApp não configurado no sistema")


@router.post("/conectar")
async def whatsapp_conectar(
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    sc = await db.get(SistemaConfig, 1)
    if not sc:
        sc = SistemaConfig(id=1)
        db.add(sc)
    _validate_uazapi_config(sc)

    try:
        await ensure_instance(empresa, sc)
        qr_data = await connect(empresa, sc)
        await db.commit()

        if qr_data.get("qrcode_base64"):
            return {"status": "connecting", "qr": qr_data["qrcode_base64"], "paircode": qr_data.get("paircode")}
        elif qr_data.get("paircode"):
            return {"status": "connecting", "paircode": qr_data["paircode"], "qr": None}
        return {"status": "connecting", "qr": None, "paircode": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def whatsapp_status(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    sc = await db.get(SistemaConfig, 1)
    if not sc:
        sc = SistemaConfig(id=1)
        db.add(sc)

    try:
        status_data = await get_status(empresa, sc)
        await db.commit()
        return status_data
    except Exception:
        return {"status": empresa.whatsapp_status or "disconnected", "numero": empresa.whatsapp_numero}


@router.post("/desconectar")
async def whatsapp_desconectar(
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    empresa = result.scalar_one_or_none()
    sc = await db.get(SistemaConfig, 1)
    if not sc:
        sc = SistemaConfig(id=1)
        db.add(sc)

    await disconnect(empresa, sc)
    await db.commit()
    return {"status": "disconnected"}


@router.post("/propostas/{id}/enviar")
async def whatsapp_enviar_proposta(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.proposta import Proposta
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Proposta)
        .options(selectinload(Proposta.empresa), selectinload(Proposta.cliente), selectinload(Proposta.usuario))
        .where(Proposta.id == id, Proposta.empresa_id == current_user.empresa_id)
    )
    proposta = result.scalar_one_or_none()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    if not proposta.token_publico:
        raise HTTPException(status_code=400, detail="Proposta não possui link público")
    if not proposta.cliente.telefone:
        raise HTTPException(status_code=400, detail="Cliente não possui telefone cadastrado")

    sc = await db.get(SistemaConfig, 1)
    if not sc:
        sc = SistemaConfig(id=1)
        db.add(sc)

    from app.services.email import build_email_variables, replace_variables
    from app.config import settings

    frontend = settings.FRONTEND_URL or f"https://{proposta.empresa.subdominio}.{settings.BASE_DOMAIN}" if proposta.empresa.subdominio else settings.FRONTEND_URL
    link = f"{frontend}/p/{proposta.token_publico}"

    variables = build_email_variables(proposta.empresa, proposta)
    variables["link_proposta"] = link

    msg_padrao = proposta.empresa.whatsapp_mensagem_padrao or f"Olá {{{{cliente_contato_nome}}}}! Sua proposta **{{{{proposta_titulo}}}}** está disponível. Valor: {{{{proposta_valor_total}}}}\n\n{link}"
    msg_texto = replace_variables(msg_padrao, variables)

    try:
        await send_text(proposta.empresa, sc, proposta.cliente.telefone, msg_texto)
        proposta.status = proposta.status  # mantém status
        await db.commit()
        return {"message": "Mensagem enviada com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

