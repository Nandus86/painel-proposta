from app.core.dependencies import verificar_limite_propostas
from app.models.proposta import ItemProposta, Proposta, StatusProposta
from app.routers.documentos import DocKind, build_router
from app.schemas.proposta import PropostaCreate, PropostaResponse, PropostaUpdate

PROPOSTA = DocKind(
    model=Proposta,
    item_model=ItemProposta,
    item_fk="proposta_id",
    status_enum=StatusProposta,
    status_enviado=StatusProposta.ENVIADA,
    status_vencido=StatusProposta.EXPIRADA,
    status_finais=(StatusProposta.ACEITA, StatusProposta.RECUSADA),
    label="Proposta",
    nao_encontrado="Proposta não encontrada",
    is_orcamento=False,
    create_schema=PropostaCreate,
    update_schema=PropostaUpdate,
    response_schema=PropostaResponse,
    limit_dependency=verificar_limite_propostas,
)

router = build_router(PROPOSTA, prefix="/api/propostas", tags=["propostas"])
