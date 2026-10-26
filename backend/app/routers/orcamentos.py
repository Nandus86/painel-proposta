from app.core.dependencies import verificar_limite_orcamentos
from app.models.orcamento import ItemOrcamento, Orcamento, StatusOrcamento
from app.routers.documentos import DocKind, build_router
from app.schemas.orcamento import OrcamentoCreate, OrcamentoResponse, OrcamentoUpdate

ORCAMENTO = DocKind(
    model=Orcamento,
    item_model=ItemOrcamento,
    item_fk="orcamento_id",
    status_enum=StatusOrcamento,
    status_enviado=StatusOrcamento.ENVIADO,
    status_vencido=StatusOrcamento.VENCIDO,
    status_finais=(StatusOrcamento.APROVADO, StatusOrcamento.REJEITADO),
    label="Orçamento",
    nao_encontrado="Orçamento não encontrado",
    is_orcamento=True,
    create_schema=OrcamentoCreate,
    update_schema=OrcamentoUpdate,
    response_schema=OrcamentoResponse,
    limit_dependency=verificar_limite_orcamentos,
)

router = build_router(ORCAMENTO, prefix="/api/orcamentos", tags=["orcamentos"])
