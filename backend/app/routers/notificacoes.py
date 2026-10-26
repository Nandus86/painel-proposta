from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.notificacao import Notificacao
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/notificacoes", tags=["Notificações"])


@router.get("")
async def listar_notificacoes(
    limit: int = Query(20, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Últimas notificações do usuário logado e o total de não lidas."""
    itens = (await db.execute(
        select(Notificacao)
        .where(Notificacao.usuario_id == current_user.id)
        .order_by(Notificacao.created_at.desc())
        .limit(limit)
    )).scalars().all()
    nao_lidas = await db.scalar(
        select(func.count(Notificacao.id)).where(Notificacao.usuario_id == current_user.id, Notificacao.lida.is_(False))
    )
    return {
        "items": [
            {
                "id": n.id,
                "tipo": n.tipo,
                "titulo": n.titulo,
                "mensagem": n.mensagem,
                "link": n.link,
                "lida": n.lida,
                "created_at": n.created_at,
            }
            for n in itens
        ],
        "nao_lidas": nao_lidas or 0,
    }


@router.post("/lidas")
async def marcar_todas_lidas(current_user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(Notificacao)
        .where(Notificacao.usuario_id == current_user.id, Notificacao.lida.is_(False))
        .values(lida=True)
    )
    await db.commit()
    return {"ok": True}


@router.post("/{id}/lida")
async def marcar_lida(id: UUID, current_user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        update(Notificacao)
        .where(Notificacao.id == id, Notificacao.usuario_id == current_user.id)
        .values(lida=True)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    await db.commit()
    return {"ok": True}
